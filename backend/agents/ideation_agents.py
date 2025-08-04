from dataclasses import dataclass, field
from typing import List, Literal, Optional, Union

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

from agents.ideation_prompts import (
    ANSWER_GENERATOR_PROMPT,
    CHECK_ANSWER,
    KEYWORD_GENERATOR_PROMPT,
    QUESTION_GENERATOR_PROMPT,
    SUMMARY_GENERATOR_PROMPT,  # Add this import
    format_qa_history,
)

load_dotenv()


# Pydantic models for structured outputs
class Question(BaseModel):
    question: str = Field(description="the well formatted question")


class NoMoreQuestions(BaseModel):
    done: Literal["NO_MORE_QUESTIONS_NEEDED"] = Field(
        description="indicates no more questions are needed"
    )


class QuestionOutput(BaseModel):
    final_output: Union[NoMoreQuestions, Question] = Field(
        description="either a new question or indication that questioning is complete"
    )


class Keywords(BaseModel):
    """List of keywords."""

    keywords: List[str] = Field(
        description="the keywords that might answer the question"
    )


class Answer(BaseModel):
    """Generated answer to a question."""

    answer: str = Field(description="comprehensive answer to the question")


class SatisfactionCheck(BaseModel):
    """Result of checking if an answer is satisfactory."""

    is_satisfactory: bool = Field(
        description="whether the answer adequately addresses the question"
    )
    reason: str = Field(description="explanation for the satisfaction assessment")


class Summary(BaseModel):
    """Generated summary of the business idea analysis."""

    summary: str = Field(
        description="comprehensive summary of the business idea based on Q&A analysis"
    )


@dataclass
class QuestionEntry:
    """Represents a question with optional response and keywords."""

    question: str
    response: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_satisfactory: bool = False
    satisfaction_reason: Optional[str] = None


@dataclass
class State:
    """State with questions and responses."""

    description: str
    questions: List[QuestionEntry] = field(default_factory=list)
    summary: Optional[str] = None  # Add summary field

    def copy(self):
        """Create a deep copy of the state."""
        return State(
            description=self.description,
            summary=self.summary,  # Include summary in copy
            questions=[
                QuestionEntry(
                    question=q.question,
                    response=q.response,
                    keywords=q.keywords.copy() if q.keywords else None,
                    is_satisfactory=q.is_satisfactory,
                    satisfaction_reason=q.satisfaction_reason,
                )
                for q in self.questions
            ],
        )


# Global model variable
model = None

def get_model():
    """Initialize and return the model, lazy loading to avoid import-time errors."""
    global model
    if model is None:
        try:
            # Use the same Groq model as the rest of the application
            model = init_chat_model("groq:llama3-70b-8192")
        except Exception as e:
            print(f"Warning: Could not initialize model: {e}")
            model = None
    return model


# Nodes
def generate_next_question(state: State) -> State:
    """Generate the next question from the description and previous answers."""
    try:
        model = get_model()
        if not model:
            return state
            
        # Format previous Q&A history
        qa_history = format_qa_history(
            [
                (q.question, q.response)
                for q in state.questions
                if q.response is not None
            ]
        )

        # Create prompt with current state
        prompt = QUESTION_GENERATOR_PROMPT.format(
            business_idea=state.description, qa_history=qa_history
        )

        try:
            # Try structured output first
            structured_llm = model.with_structured_output(QuestionOutput)
            response = structured_llm.invoke(prompt)

            # Check if no more questions are needed
            if isinstance(response.final_output, NoMoreQuestions):
                return state  # No new question added

            # Add new question to state
            new_question = QuestionEntry(question=response.final_output.question)
            state.questions.append(new_question)

        except Exception as structured_error:
            print(f"Structured output failed for question generation: {structured_error}, falling back to regular response")
            # Fallback to regular response if structured output fails
            response = model.invoke(prompt)
            question_text = response.content if hasattr(response, 'content') else str(response)
            
            # Clean up the response to extract just the question
            if "NO_MORE_QUESTIONS_NEEDED" in question_text.upper():
                return state  # No new question added
            
            # Extract the question (remove any prefixes or formatting)
            question_text = question_text.strip()
            if question_text and not question_text.startswith("I"):
                new_question = QuestionEntry(question=question_text)
                state.questions.append(new_question)

        return state

    except Exception as e:
        print(f"Error generating next question: {e}")
        return state


def check_if_satisfactory(state: State, question_index: int) -> State:
    """Check if the response answers the question at the specified index."""
    try:
        model = get_model()
        if not model:
            return state
            
        if not state.questions or question_index >= len(state.questions):
            return state

        if not state.questions[question_index].response:
            return state

        target_question = state.questions[question_index]

        check_prompt = CHECK_ANSWER.format(
            question=target_question.question,
            response=target_question.response,
        )

        try:
            # Try structured output first
            structured_llm = model.with_structured_output(SatisfactionCheck)
            response = structured_llm.invoke(check_prompt)
            is_satisfactory = response.is_satisfactory
            reason = response.reason
        except Exception as structured_error:
            print(f"Structured output failed for satisfaction check: {structured_error}, falling back to regular response")
            # Fallback to regular response if structured output fails
            response = model.invoke(check_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Simple heuristic: if response contains positive words, consider it satisfactory
            response_lower = response_text.lower()
            is_satisfactory = any(word in response_lower for word in ['satisfactory', 'adequate', 'yes', 'good', 'sufficient'])
            reason = response_text.strip()

        # Store satisfaction info in the question entry
        state.questions[question_index].is_satisfactory = is_satisfactory
        state.questions[question_index].satisfaction_reason = reason

        print(
            f"Satisfaction check for question {question_index}: {is_satisfactory} - {reason}"
        )

        return state

    except Exception as e:
        print(f"Error checking satisfaction: {e}")
        return state


def generate_keywords(state: State, question_index: int) -> State:
    """Generate keywords for the question at the specified index."""
    try:
        model = get_model()
        if not model:
            return state
            
        if not state.questions or question_index >= len(state.questions):
            return state

        target_question = state.questions[question_index]

        # Format previous Q&A history (excluding the target question if it's not the last one)
        qa_history = format_qa_history(
            [
                (q.question, q.response)
                for i, q in enumerate(state.questions)
                if i != question_index and q.response is not None
            ]
        )

        # Create keyword generation prompt
        prompt = KEYWORD_GENERATOR_PROMPT.format(
            business_idea=state.description,
            current_question=target_question.question,
            qa_history=qa_history,
        )

        try:
            # Try structured output first
            structured_llm = model.with_structured_output(Keywords)
            response = structured_llm.invoke(prompt)
            keywords = response.keywords
        except Exception as structured_error:
            print(f"Structured output failed for keywords: {structured_error}, falling back to regular response")
            # Fallback to regular response if structured output fails
            response = model.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract keywords from response text (look for JSON array or comma-separated values)
            import re
            import json
            
            # Try to find JSON array in response
            json_match = re.search(r'\[.*?\]', response_text)
            if json_match:
                try:
                    keywords = json.loads(json_match.group())
                except:
                    # Fallback: split by commas and clean up
                    keywords = [k.strip().strip('"\'') for k in response_text.split(',')]
            else:
                # Fallback: split by commas and clean up
                keywords = [k.strip().strip('"\'') for k in response_text.split(',')]
            
            # Limit to 6 keywords and filter out empty ones
            keywords = [k for k in keywords if k and len(k) > 2][:6]

        # Update the target question with keywords
        state.questions[question_index].keywords = keywords

        return state

    except Exception as e:
        print(f"Error generating keywords: {e}")
        return state


def generate_answer(
    state: State, selected_keywords: Keywords, question_index: int
) -> State:
    """Generate an answer for the question at the specified index."""
    try:
        model = get_model()
        if not model:
            return state
            
        if not state.questions or question_index >= len(state.questions):
            return state

        target_question = state.questions[question_index]

        # Join selected keywords
        keywords_str = ", ".join(selected_keywords.keywords)

        # Create answer generation prompt
        prompt = ANSWER_GENERATOR_PROMPT.format(
            business_idea=state.description,
            question=target_question.question,
            selected_keywords=keywords_str,
        )

        try:
            # Try structured output first
            structured_llm = model.with_structured_output(Answer)
            response = structured_llm.invoke(prompt)
            answer_text = response.answer
        except Exception as structured_error:
            print(f"Structured output failed: {structured_error}, falling back to regular response")
            # Fallback to regular response if structured output fails
            response = model.invoke(prompt)
            answer_text = response.content if hasattr(response, 'content') else str(response)

        # Update the target question with the response
        state.questions[question_index].response = answer_text

        return state

    except Exception as e:
        print(f"Error generating answer: {e}")
        return state


def generate_summary(state: State) -> State:
    """Generate a comprehensive summary of the business idea based on all Q&A analysis."""
    try:
        model = get_model()
        if not model:
            return state
            
        # Format all Q&A history
        qa_history = format_qa_history(
            [
                (q.question, q.response)
                for q in state.questions
                if q.response is not None
            ]
        )

        # Create summary generation prompt
        prompt = SUMMARY_GENERATOR_PROMPT.format(
            business_idea=state.description,
            qa_history=qa_history,
        )

        try:
            # Try structured output first
            structured_llm = model.with_structured_output(Summary)
            response = structured_llm.invoke(prompt)
            summary_text = response.summary
        except Exception as structured_error:
            print(f"Structured output failed for summary: {structured_error}, falling back to regular response")
            # Fallback to regular response if structured output fails
            response = model.invoke(prompt)
            summary_text = response.content if hasattr(response, 'content') else str(response)

        # Update the state with the summary
        state.summary = summary_text

        return state

    except Exception as e:
        print(f"Error generating summary: {e}")
        return state


def reset_questions(state: State, index: int) -> State:
    """Delete every question after this index."""
    try:
        if index < 0 or index >= len(state.questions):
            return state

        # Keep only questions up to and including the specified index
        state.questions = state.questions[: index + 1]

        # Clear summary since the analysis has changed
        state.summary = None

        return state

    except Exception as e:
        print(f"Error resetting questions: {e}")
        return state


# Helper functions for API integration
def get_current_question(state: State) -> Optional[str]:
    """Get the current question that needs to be answered."""
    if not state.questions:
        return None

    # Find the last question without a response
    for question in reversed(state.questions):
        if question.response is None:
            return question.question

    return None


def get_question_by_index(state: State, index: int) -> Optional[QuestionEntry]:
    """Get a question by its index."""
    if not state.questions or index < 0 or index >= len(state.questions):
        return None

    return state.questions[index]
