import json
import logging
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents import (
    Keywords,
    State,
    check_if_satisfactory,
    generate_answer,
    generate_keywords,
    generate_next_question,
    generate_summary,  # Add this import
    reset_questions,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Business Idea Q&A API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request/response logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log request details
    body = await request.body()
    logger.info("=== INCOMING REQUEST ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    if body:
        try:
            body_json = json.loads(body)
            logger.info(f"Request Body: {json.dumps(body_json, indent=2)}")
        except:
            logger.info(f"Request Body (raw): {body.decode()}")
    else:
        logger.info("Request Body: Empty")
    
    # Process request
    response = await call_next(request)
    
    # Log response status
    logger.info(f"Response Status: {response.status_code}")
    logger.info("=== END REQUEST ===\n")
    
    return response

#TODO: In-memory storage for sessions (in production, use a proper database)
sessions = {}


# Request/Response models
class InitSessionRequest(BaseModel):
    session_id: str
    description: str


class AnswerRequest(BaseModel):
    session_id: str
    question_index: int
    response: str


class SuggestAnswerRequest(BaseModel):
    session_id: str
    question_index: int
    selected_keywords: List[str]


class ResetRequest(BaseModel):
    session_id: str
    index: int


class SessionResponse(BaseModel):
    session_id: str
    description: str
    questions: List[dict]
    summary: Optional[str] = None  # Add summary field


class AnswerResponse(BaseModel):
    question: Optional[str]
    has_more_questions: bool
    question_satisfaction: dict


class KeywordsResponse(BaseModel):
    keywords: List[str]


class SuggestAnswerResponse(BaseModel):
    answer: str


class SummaryResponse(BaseModel):
    summary: str


def all_questions_answered(state: State) -> bool:
    """Check if all questions have satisfactory answers."""
    if not state.questions:
        logger.info("No questions in state")
        return False
    
    result = all(
        q.response is not None and q.is_satisfactory == True 
        for q in state.questions
    )
    logger.info(f"All questions answered: {result}")
    return result

@app.post("/init", response_model=SessionResponse)
async def init_session(request: InitSessionRequest):
    """Initialize a new session with a business idea description and provided session ID."""
    logger.info("=== INIT SESSION ===")
    logger.info(f"Session ID: {request.session_id}")
    logger.info(f"Description: {request.description}")
    
    if request.session_id in sessions:
        logger.error(f"Session already exists: {request.session_id}")
        raise HTTPException(status_code=400, detail="Session ID already exists")
    
    state = State(description=request.description)
    logger.info(f"Created initial state: {state}")

    # Generate the first question
    logger.info("Generating first question...")
    state = generate_next_question(state)
    logger.info(f"State after generating question: {state}")

    sessions[request.session_id] = state
    logger.info(f"Stored session. Total sessions: {len(sessions)}")

    response_data = SessionResponse(
        session_id=request.session_id,
        description=state.description,
        summary=state.summary,  # Include summary
        questions=[
            {
                "question": q.question,
                "response": q.response,
                "keywords": q.keywords,
                "is_satisfactory": q.is_satisfactory,
                "satisfaction_reason": q.satisfaction_reason,
            }
            for q in state.questions
        ],
    )
    
    logger.info(f"INIT RESPONSE JSON: {json.dumps(response_data.dict(), indent=2)}")
    logger.info("=== END INIT SESSION ===\n")
    
    return response_data


@app.post("/respond", response_model=AnswerResponse)
async def respond_to_question(request: AnswerRequest):
    """Receive a response to any question by index and generate next question if needed."""
    logger.info("=== RESPOND TO QUESTION ===")
    logger.info(f"Session ID: {request.session_id}")
    logger.info(f"Question Index: {request.question_index}")
    logger.info(f"Response: {request.response}")
    
    if request.session_id not in sessions:
        logger.error(f"Session not found: {request.session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[request.session_id]
    logger.info(f"Current state: {state}")

    if not state.questions or request.question_index >= len(state.questions):
        logger.error(f"Invalid question index: {request.question_index}, total questions: {len(state.questions) if state.questions else 0}")
        raise HTTPException(status_code=400, detail="Invalid question index")

    # Set the response for the specified question
    logger.info(f"Setting response for question {request.question_index}")
    state.questions[request.question_index].response = request.response

    # Check if the response is satisfactory
    logger.info("Checking if response is satisfactory...")
    state = check_if_satisfactory(state, request.question_index)
    
    logger.info(f"Satisfaction check result: {state.questions[request.question_index].is_satisfactory}")
    logger.info(f"Satisfaction reason: {state.questions[request.question_index].satisfaction_reason}")

    question_satisfaction = {
        "is_satisfactory": state.questions[request.question_index].is_satisfactory,
        "reason": state.questions[request.question_index].satisfaction_reason,
    }

    # Generate next question if we haven't reached the limit
    if len(state.questions) < 5:
        logger.info("Generating next question...")
        state = generate_next_question(state)
        logger.info(f"State after generating next question: {state}")
    else:
        logger.info("Maximum number of questions (5) reached")

    # Update the session
    sessions[request.session_id] = state

    # Check if a new question was added
    has_more_questions = len(state.questions) > request.question_index + 1
    new_question = state.questions[-1].question if has_more_questions else None
    
    logger.info(f"New question count: {len(state.questions)}")
    logger.info(f"Has more questions: {has_more_questions}")
    logger.info(f"New question: {new_question}")

    response_data = AnswerResponse(
        question=new_question,
        has_more_questions=has_more_questions,
        question_satisfaction=question_satisfaction,
    )
    
    logger.info(f"RESPOND RESPONSE JSON: {json.dumps(response_data.dict(), indent=2)}")
    logger.info("=== END RESPOND TO QUESTION ===\n")

    return response_data


@app.post("/suggest", response_model=SuggestAnswerResponse)
async def suggest_answer(request: SuggestAnswerRequest):
    """Generate a suggested response using selected keywords for any question by index."""
    logger.info("=== SUGGEST ANSWER ===")
    logger.info(f"Session ID: {request.session_id}")
    logger.info(f"Question Index: {request.question_index}")
    logger.info(f"Selected Keywords: {request.selected_keywords}")
    
    if request.session_id not in sessions:
        logger.error(f"Session not found: {request.session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[request.session_id]
    logger.info(f"Current state: {state}")

    if not state.questions or request.question_index >= len(state.questions):
        logger.error(f"Invalid question index: {request.question_index}, total questions: {len(state.questions) if state.questions else 0}")
        raise HTTPException(status_code=400, detail="Invalid question index")

    # Create Keywords object from selected keywords
    selected_keywords = Keywords(keywords=request.selected_keywords)
    logger.info(f"Created Keywords object: {selected_keywords}")

    # Generate answer directly in the state
    logger.info("Generating answer...")
    state = generate_answer(state, selected_keywords, request.question_index)
    logger.info(f"State after generating answer: {state}")
    
    # Update the session with the new answer
    sessions[request.session_id] = state

    # Return the generated answer
    generated_answer = state.questions[request.question_index].response
    logger.info(f"Generated answer: {generated_answer}")

    response_data = SuggestAnswerResponse(answer=generated_answer)
    logger.info(f"SUGGEST RESPONSE JSON: {json.dumps(response_data.dict(), indent=2)}")
    logger.info("=== END SUGGEST ANSWER ===\n")

    return response_data


@app.get("/keywords/{session_id}/{question_index}", response_model=KeywordsResponse)
async def get_keywords(session_id: str, question_index: int):
    """Get keywords for any question by index."""
    logger.info("=== GET KEYWORDS ===")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Question Index: {question_index}")
    
    if session_id not in sessions:
        logger.error(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[session_id]
    logger.info(f"Current state: {state}")

    if not state.questions or question_index >= len(state.questions):
        logger.error(f"Invalid question index: {question_index}, total questions: {len(state.questions) if state.questions else 0}")
        raise HTTPException(status_code=400, detail="Invalid question index")

    # Generate keywords for the specified question if not already generated
    if not state.questions[question_index].keywords:
        logger.info("Keywords not found, generating...")
        state = generate_keywords(state, question_index)
        sessions[session_id] = state
        logger.info(f"Generated keywords: {state.questions[question_index].keywords}")
    else:
        logger.info(f"Using existing keywords: {state.questions[question_index].keywords}")

    response_data = KeywordsResponse(keywords=state.questions[question_index].keywords or [])
    logger.info(f"KEYWORDS RESPONSE JSON: {json.dumps(response_data.dict(), indent=2)}")
    logger.info("=== END GET KEYWORDS ===\n")

    return response_data


@app.get("/summary/{session_id}", response_model=SummaryResponse)
async def get_summary(session_id: str):
    """Generate and return a comprehensive summary of the business idea analysis."""
    logger.info("=== GET SUMMARY ===")
    logger.info(f"Session ID: {session_id}")
    
    if session_id not in sessions:
        logger.error(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[session_id]
    logger.info(f"Current state: {state}")

    # Check if there are any answered questions
    answered_questions = [q for q in state.questions if q.response is not None]
    if not answered_questions:
        logger.error("No answered questions found for summary generation")
        raise HTTPException(status_code=400, detail="No answered questions available for summary generation")

    # Generate summary if not already generated or if analysis has changed
    if not state.summary:
        logger.info("Summary not found, generating...")
        state = generate_summary(state)
        sessions[session_id] = state
        logger.info(f"Generated summary: {state.summary}")
    else:
        logger.info(f"Using existing summary: {state.summary}")

    response_data = SummaryResponse(summary=state.summary)
    logger.info(f"SUMMARY RESPONSE JSON: {json.dumps(response_data.dict(), indent=2)}")
    logger.info("=== END GET SUMMARY ===\n")

    return response_data


@app.post("/reset", response_model=SessionResponse)
async def reset_session(request: ResetRequest):
    """Reset questions after a specific index."""
    logger.info("=== RESET SESSION ===")
    logger.info(f"Session ID: {request.session_id}")
    logger.info(f"Reset Index: {request.index}")
    
    if request.session_id not in sessions:
        logger.error(f"Session not found: {request.session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[request.session_id]
    logger.info(f"State before reset: {state}")
    
    state = reset_questions(state, request.index)
    logger.info(f"State after reset: {state}")

    sessions[request.session_id] = state

    response_data = SessionResponse(
        session_id=request.session_id,
        description=state.description,
        summary=state.summary,  # Include summary
        questions=[
            {
                "question": q.question,
                "response": q.response,
                "keywords": q.keywords,
                "is_satisfactory": q.is_satisfactory,
                "satisfaction_reason": q.satisfaction_reason,
            }
            for q in state.questions
        ],
    )
    
    logger.info(f"RESET RESPONSE JSON: {json.dumps(response_data.dict(), indent=2)}")
    logger.info("=== END RESET SESSION ===\n")

    return response_data


@app.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get the current state of a session."""
    logger.info("=== GET SESSION ===")
    logger.info(f"Session ID: {session_id}")
    
    if session_id not in sessions:
        logger.error(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[session_id]
    logger.info(f"Retrieved state: {state}")

    response_data = SessionResponse(
        session_id=session_id,
        description=state.description,
        summary=state.summary,  # Include summary
        questions=[
            {
                "question": q.question,
                "response": q.response,
                "keywords": q.keywords,
                "is_satisfactory": q.is_satisfactory,
                "satisfaction_reason": q.satisfaction_reason,
            }
            for q in state.questions
        ],
    )
    
    logger.info(f"GET SESSION RESPONSE JSON: {json.dumps(response_data.dict(), indent=2)}")
    logger.info("=== END GET SESSION ===\n")

    return response_data


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    logger.info("=== DELETE SESSION ===")
    logger.info(f"Session ID: {session_id}")
    
    if session_id not in sessions:
        logger.error(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    logger.info(f"Session deleted. Remaining sessions: {len(sessions)}")
    
    response_data = {"message": "Session deleted successfully"}
    logger.info(f"DELETE RESPONSE JSON: {json.dumps(response_data, indent=2)}")
    logger.info("=== END DELETE SESSION ===\n")
    
    return response_data


@app.get("/")
async def root():
    """Root endpoint with API information."""
    logger.info("=== ROOT ENDPOINT ===")
    
    response_data = {
        "message": "Business Idea Q&A API",
        "version": "1.0.0",
        "endpoints": {
            "POST /init": "Initialize a new session",
            "POST /respond": "Submit response to any question by index and get next question",
            "POST /suggest": "Get suggested answer using keywords for any question by index",
            "GET /keywords/{session_id}/{question_index}": "Get keywords for any question by index",
            "GET /summary/{session_id}": "Get comprehensive summary of business idea analysis",
            "POST /reset": "Reset questions after specified index",
            "GET /session/{session_id}": "Get session state",
            "DELETE /session/{session_id}": "Delete session",
        },
    }
    
    logger.info(f"ROOT RESPONSE JSON: {json.dumps(response_data, indent=2)}")
    logger.info("=== END ROOT ENDPOINT ===\n")
    
    return response_data

@app.get("/health")
def health_check():
    """Health check endpoint."""
    logger.info("=== HEALTH CHECK ===")
    
    response_data = {"status": "healthy", "service": "Iterative Business Consultant"}
    logger.info(f"HEALTH RESPONSE JSON: {json.dumps(response_data, indent=2)}")
    logger.info("=== END HEALTH CHECK ===\n")
    
    return response_data

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI application...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
