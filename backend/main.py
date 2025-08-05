import sys
import os
import json
import logging
import uuid
from typing import List, Optional

# Add paths for imports
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Import agents
from agents.Financial_Assessment import FinancialAssessmentAgent
from agents.legal_agent import LegalAgent
from agents.marketAnalysis_competitors_Agents import run_market_analysis_competitors
from agents.opportunities_agent import run_opportunities_agent
from agents.bmc_agent import extract_bmc_parts, read_multiple_files
from agents.image_agent import run_image_generation_agent
from agents.swot_agent import SWOTAgent

# Import ideation agents
from agents.ideation_structs import State, QuestionEntry
from agents.ideation_agents import (
    Keywords,
    check_if_satisfactory,
    generate_answer,
    generate_keywords,
    generate_next_question,
    generate_summary,
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

# Load environment variables
load_dotenv()

app = FastAPI(title="BrandOrbAI Unified API", version="1.0.0")

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
    
    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code}")
    logger.info("=== END REQUEST ===\n")
    return response

# In-memory storage
runs = {}  # For multi-agent runs
sessions = {}  # For ideation sessions

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

# Multi-agent models
class RunRequest(BaseModel):
    business_idea: str

class MultiAgentState:
    def __init__(self, business_idea: str):
        self.business_idea = business_idea
        self.financial_assessment = None
        self.legal_analysis = None
        self.partners_suppliers_investors = None
        self.market_analysis = None
        self.competitor_analysis = None 
        self.background_image = None  # Add image data to state

    def to_dict(self):
        return {
            "business_idea": self.business_idea,
            "financial_assessment": self.financial_assessment,
            "legal_analysis": self.legal_analysis,
            "partners_suppliers_investors": self.partners_suppliers_investors,
            "market_analysis": self.market_analysis,
            "competitor_analysis": self.competitor_analysis,
            "background_image": self.background_image,  # Include image in output
        }

# Ideation models
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
    summary: Optional[str] = None

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

# =============================================================================
# MULTI-AGENT ENDPOINTS
# =============================================================================

@app.post("/run-all")
async def run_all_agents(request: RunRequest):
    """Run all agents for business analysis including background image generation"""
    run_id = str(uuid.uuid4())
    state = MultiAgentState(request.business_idea)
    
    try:
        # Financial Assessment
        financial_agent = FinancialAssessmentAgent()
        state.financial_assessment = financial_agent.summarize_business_idea(state)
        
        # Legal Analysis
        legal_agent = LegalAgent()
        state = legal_agent.run(state)
        
        # Market Analysis & Competitors
        state = run_market_analysis_competitors(state)
        
        # Opportunities
        state.partners_suppliers_investors = run_opportunities_agent(state.business_idea)
        
        # Generate background image as part of the workflow
        try:
            logger.info(f"Generating background image for business idea: {request.business_idea}")
            
            # Create a business summary from all agent outputs for image generation
            summary_parts = []
            if state.financial_assessment:
                summary_parts.append("Financial assessment completed")
            if state.legal_analysis:
                summary_parts.append("Legal analysis completed")
            if state.market_analysis:
                summary_parts.append("Market analysis completed")
            if state.partners_suppliers_investors:
                summary_parts.append("Opportunities analysis completed")
            
            business_summary = f"Business plan for {request.business_idea}. Analysis includes: {', '.join(summary_parts)}"
            
            image_result = run_image_generation_agent(business_summary, request.business_idea)
            
            if image_result["status"] == "success":
                state.background_image = image_result
                logger.info(f"Successfully generated background image for business: {request.business_idea}")
            else:
                logger.warning(f"Image generation failed: {image_result.get('error', 'Unknown error')}")
                state.background_image = {"status": "error", "error": image_result.get('error', 'Unknown error')}
                
        except Exception as image_error:
            logger.error(f"Error during image generation: {str(image_error)}")
            state.background_image = {"status": "error", "error": str(image_error)}
        
        runs[run_id] = state.to_dict()
        
        # Return the complete state including image data for frontend access
        return {
            "message": "done", 
            "run_id": run_id,
            "data": state.to_dict()  # Include all state data including background_image
        }
    
    except Exception as e:
        logger.error(f"Error running agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@app.get("/agent-output")
async def get_agent_output(agent: str = Query(...)):
    """Get output from specific agent"""
    agent_file_map = {
        "market_analysis_competitors": os.path.join(
            os.path.dirname(__file__),
            "agents", "output", "market_analysis_competitors_output.txt"
        ),
        "financial_assessment": os.path.join(
            os.path.dirname(__file__),
            "agents", "output", "assessment_output.txt"
        ),
        "legal_analysis": os.path.join(
            os.path.dirname(__file__),
            "agents", "output", "legal_output.txt"
        ),
        "opportunities": os.path.join(
            os.path.dirname(__file__),
            "agents", "output", "opportunities_output.txt"
        ),
    }
    
    if agent not in agent_file_map:
        raise HTTPException(status_code=404, detail="Agent output file not found")
    
    file_path = os.path.abspath(agent_file_map[agent])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Output file does not exist")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"output": content}

# =============================================================================
# BMC ENDPOINTS
# =============================================================================

BMC_PARTS = [
    "Key Partners",
    "Key Activities", 
    "Key Resources",
    "Value Propositions",
    "Customer Relationships",
    "Channels",
    "Customer Segments",
    "Cost Structure",
    "Revenue Streams"
]

@app.post("/bmc/run")
def run_bmc_extraction():
    """Run BMC extraction using existing agent outputs"""
    input_files = [
        os.path.join(os.path.dirname(__file__), "agents", "output", "opportunities_output.txt"),
        os.path.join(os.path.dirname(__file__), "agents", "output", "market_analysis_competitors_output.txt"),
        os.path.join(os.path.dirname(__file__), "agents", "output", "assessment_output.txt"),
        os.path.join(os.path.dirname(__file__), "agents", "output", "legal_output.txt"),
    ]
    
    try:
        _, file_contents_map = read_multiple_files(input_files)
        report_text = ""  # Not used, kept for compatibility
        bmc = extract_bmc_parts(report_text, file_contents_map)
        
        # Save BMC output
        output_path = os.path.join(os.path.dirname(__file__), "agents", "output", "bmc_output.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            for part in BMC_PARTS:
                f.write(f"{part}:\n{bmc.get(part, '')}\n\n")
        
        return {"status": "BMC extraction completed", "output_file": output_path}
    except Exception as e:
        logger.error(f"BMC extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"BMC extraction failed: {str(e)}")

@app.get("/bmc/output", response_class=PlainTextResponse)
def get_bmc_output():
    """Get BMC output content"""
    output_path = os.path.join(os.path.dirname(__file__), "agents", "output", "bmc_output.txt")
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="BMC output not found")
    with open(output_path, "r", encoding="utf-8") as f:
        return f.read()

# =============================================================================
# IMAGE GENERATION ENDPOINTS
# =============================================================================

class ImageGenerationRequest(BaseModel):
    business_idea: str
    business_summary: str

class ImageGenerationResponse(BaseModel):
    image_url: str
    business_idea: str
    generated_at: str
    status: str
    base64_data: Optional[str] = None
    local_path: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    serve_url: Optional[str] = None  # Direct URL to serve the image

@app.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_business_image(request: ImageGenerationRequest):
    """Generate a background image for business idea using Groq + Pollinations AI"""
    try:
        logger.info(f"Generating image for business idea: {request.business_idea}")
        
        result = run_image_generation_agent(request.business_summary, request.business_idea)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=f"Image generation failed: {result.get('error', 'Unknown error')}")
        
        return ImageGenerationResponse(**result)
        
    except Exception as e:
        logger.error(f"Image generation endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@app.get("/image-output")
async def get_image_output():
    """Get the latest generated image information"""
    output_path = os.path.join(os.path.dirname(__file__), "agents", "output", "image_generation_output.json")
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="No image generation output found")
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            import json
            content = json.load(f)
        return content
    except Exception as e:
        logger.error(f"Error reading image output: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to read image output")

@app.get("/images/{filename}")
async def serve_image(filename: str):
    """Serve generated images directly"""
    image_path = os.path.join(os.path.dirname(__file__), "agents", "output", "images", filename)
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        path=image_path,
        media_type="image/jpeg",
        filename=filename
    )

# =============================================================================
# SWOT ANALYSIS ENDPOINTS
# =============================================================================

@app.post("/run-swot")
async def run_swot_analysis():
    """Generate SWOT analysis based on existing agent outputs"""
    try:
        logger.info("Starting SWOT analysis")
        
        # Create SWOT agent instance
        swot_agent = SWOTAgent()
        
        # Generate SWOT analysis
        result = swot_agent.generate_swot_analysis()
        
        if result.get("success", False):
            logger.info("SWOT analysis completed successfully")
            return {"message": "SWOT analysis completed", "status": "success"}
        else:
            logger.error(f"SWOT analysis failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=f"SWOT analysis failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error in SWOT analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SWOT analysis failed: {str(e)}")

@app.get("/swot-output")
async def get_swot_output():
    """Get the latest SWOT analysis output"""
    output_path = os.path.join(os.path.dirname(__file__), "agents", "output", "swot_output.txt")
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="No SWOT analysis output found")
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        logger.error(f"Error reading SWOT output: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to read SWOT output")

# =============================================================================
# IDEATION ENDPOINTS
# =============================================================================

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
    
    # Create new state
    state = State(description=request.description)
    logger.info(f"Created initial state: {state}")
    
    # Generate first question
    logger.info("Generating first question...")
    state = generate_next_question(state)
    logger.info(f"State after generating question: {state}")
    
    # Store session
    sessions[request.session_id] = state
    logger.info(f"Stored session. Total sessions: {len(sessions)}")
    
    # Convert to response format
    questions_data = []
    for q in state.questions:
        questions_data.append({
            "question": q.question,
            "response": q.response,
            "keywords": q.keywords,
            "is_satisfactory": q.is_satisfactory,
            "satisfaction_reason": q.satisfaction_reason,
        })
    
    response_data = SessionResponse(
        session_id=request.session_id,
        description=state.description,
        summary=state.summary,
        questions=questions_data
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
    
    # Generate next question ONLY if current answer is satisfactory and we haven't reached the limit
    new_question = None
    has_more = False
    
    if state.questions[request.question_index].is_satisfactory and len(state.questions) < 5:
        logger.info("Answer is satisfactory, generating next question...")
        state = generate_next_question(state)
        logger.info(f"State after generating next question: {state}")
        
        # Check if a new question was added
        if len(state.questions) > request.question_index + 1:
            new_question = state.questions[-1].question
            has_more = True
    elif not state.questions[request.question_index].is_satisfactory:
        logger.info("Answer is not satisfactory, allowing user to edit their response")
    else:
        logger.info("Maximum number of questions (5) reached")
    
    # Update the session
    sessions[request.session_id] = state
    
    logger.info(f"New question count: {len(state.questions)}")
    logger.info(f"Has more questions: {has_more}")
    logger.info(f"New question: {new_question}")
    
    response_data = AnswerResponse(
        question=new_question,
        has_more_questions=has_more,
        question_satisfaction=question_satisfaction
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
    generated_answer = state.questions[request.question_index].response or ""
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
    
    keywords = state.questions[question_index].keywords or []
    response_data = KeywordsResponse(keywords=keywords)
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
    
    # Generate summary if not already generated
    if not state.summary:
        logger.info("Summary not found, generating...")
        state = generate_summary(state)
        sessions[session_id] = state
        logger.info(f"Generated summary: {state.summary}")
    else:
        logger.info(f"Using existing summary: {state.summary}")
    
    response_data = SummaryResponse(summary=state.summary or "Summary generation failed")
    logger.info(f"SUMMARY RESPONSE JSON: {json.dumps(response_data.dict(), indent=2)}")
    logger.info("=== END GET SUMMARY ===\n")
    
    return response_data


@app.post("/summary-with-image/{session_id}", response_model=SummaryResponse)
async def get_summary_with_image(session_id: str):
    """Generate and return a comprehensive summary with embedded image metadata."""
    logger.info("=== GET SUMMARY WITH IMAGE ===")
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
    
    # Generate image for the business idea
    logger.info("Generating business image...")
    try:
        # Create a simple business summary for image generation
        business_summary = f"Business plan for {state.description}"
        for q in answered_questions[:3]:  # Use first 3 answers for context
            business_summary += f" {q.response[:100]}"  # Truncate for brevity
        
        image_result = run_image_generation_agent(business_summary, state.description)
        logger.info(f"Image generation result: {image_result}")
        
        # Generate summary with image metadata included
        logger.info("Generating summary with image metadata...")
        state = generate_summary(state, include_image_metadata=True, image_data=image_result)
        sessions[session_id] = state
        logger.info(f"Generated enhanced summary with image data")
        
    except Exception as e:
        logger.error(f"Error generating image for summary: {e}")
        # Fall back to regular summary if image generation fails
        if not state.summary:
            state = generate_summary(state)
            sessions[session_id] = state
    
    response_data = SummaryResponse(summary=state.summary or "Summary generation failed")
    logger.info(f"ENHANCED SUMMARY RESPONSE JSON: {json.dumps(response_data.dict(), indent=2)}")
    logger.info("=== END GET SUMMARY WITH IMAGE ===\n")
    
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
    
    # Reset questions
    state = reset_questions(state, request.index)
    logger.info(f"State after reset: {state}")
    
    # Update session
    sessions[request.session_id] = state
    
    # Convert to response format
    questions_data = []
    for q in state.questions:
        questions_data.append({
            "question": q.question,
            "response": q.response,
            "keywords": q.keywords,
            "is_satisfactory": q.is_satisfactory,
            "satisfaction_reason": q.satisfaction_reason,
        })
    
    response_data = SessionResponse(
        session_id=request.session_id,
        description=state.description,
        summary=state.summary,
        questions=questions_data
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
    
    # Convert to response format
    questions_data = []
    for q in state.questions:
        questions_data.append({
            "question": q.question,
            "response": q.response,
            "keywords": q.keywords,
            "is_satisfactory": q.is_satisfactory,
            "satisfaction_reason": q.satisfaction_reason,
        })
    
    response_data = SessionResponse(
        session_id=session_id,
        description=state.description,
        summary=state.summary,
        questions=questions_data
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

# =============================================================================
# HEALTH & ROOT ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    logger.info("=== ROOT ENDPOINT ===")
    
    response_data = {
        "message": "BrandOrbAI Unified API",
        "version": "1.0.0",
        "endpoints": {
            "multi_agent": "/run-all, /agent-output",
            "bmc": "/bmc/run, /bmc/output",
            "image_generation": "/generate-image, /image-output",
            "swot_analysis": "/run-swot, /swot-output",
            "ideation": {
                "POST /init": "Initialize a new session",
                "POST /respond": "Submit response to any question by index and get next question",
                "POST /suggest": "Get suggested answer using keywords for any question by index",
                "GET /keywords/{session_id}/{question_index}": "Get keywords for any question by index",
                "GET /summary/{session_id}": "Get comprehensive summary of business idea analysis",
                "POST /reset": "Reset questions after specified index",
                "GET /session/{session_id}": "Get session state",
                "DELETE /session/{session_id}": "Delete session",
            }
        },
        "status": "All services active and ready"
    }
    
    logger.info(f"ROOT RESPONSE JSON: {json.dumps(response_data, indent=2)}")
    logger.info("=== END ROOT ENDPOINT ===\n")
    
    return response_data

@app.get("/health")
def health_check():
    """Health check endpoint."""
    logger.info("=== HEALTH CHECK ===")
    
    response_data = {"status": "healthy", "service": "BrandOrbAI Unified API"}
    logger.info(f"HEALTH RESPONSE JSON: {json.dumps(response_data, indent=2)}")
    logger.info("=== END HEALTH CHECK ===\n")
    
    return response_data

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting BrandOrbAI Unified API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )