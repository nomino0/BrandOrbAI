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
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Import agents
from agents.Financial_Assessment import FinancialAssessmentAgent
from agents.legal_agent import LegalAgent
from agents.marketAnalysis_competitors_Agents import run_market_analysis_competitors
from agents.opportunities_agent import run_opportunities_agent
from agents.bmc_agent import extract_bmc_parts, read_multiple_files

# Import ideation agents - temporarily comment out to test basic server
# from agents.ideation_structs import State, QuestionEntry
# from agents.ideation_agents import (
#     Keywords,
#     check_if_satisfactory,
#     generate_answer,
#     generate_keywords,
#     generate_next_question,
#     generate_summary,
#     reset_questions,
# )

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

    def to_dict(self):
        return {
            "business_idea": self.business_idea,
            "financial_assessment": self.financial_assessment,
            "legal_analysis": self.legal_analysis,
            "partners_suppliers_investors": self.partners_suppliers_investors,
            "market_analysis": self.market_analysis,
            "competitor_analysis": self.competitor_analysis,
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
    """Run all agents for business analysis"""
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
        
        runs[run_id] = state.to_dict()
        return {"message": "done", "run_id": run_id}
    
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
# IDEATION ENDPOINTS - TEMPORARILY DISABLED FOR TESTING
# =============================================================================

# TODO: Re-enable once import conflicts are resolved

# def all_questions_answered(state: State) -> bool:
#     """Check if all questions have satisfactory answers."""
#     if not state.questions:
#         logger.info("No questions in state")
#         return False
    
#     result = all(
#         q.response is not None and q.is_satisfactory == True 
#         for q in state.questions
#     )
#     logger.info(f"All questions answered: {result}")
#     return result

# @app.post("/init", response_model=SessionResponse)
# async def init_session(request: InitSessionRequest):
#     """Initialize a new session with a business idea description and provided session ID."""
#     # Implementation commented out temporarily
#     raise HTTPException(status_code=501, detail="Ideation endpoints temporarily disabled")

# @app.post("/respond", response_model=AnswerResponse)
# async def respond_to_question(request: AnswerRequest):
#     """Receive a response to any question by index and generate next question if needed."""
#     # Implementation commented out temporarily
#     raise HTTPException(status_code=501, detail="Ideation endpoints temporarily disabled")

# @app.post("/suggest", response_model=SuggestAnswerResponse)
# async def suggest_answer(request: SuggestAnswerRequest):
#     """Generate a suggested response using selected keywords for any question by index."""
#     # Implementation commented out temporarily
#     raise HTTPException(status_code=501, detail="Ideation endpoints temporarily disabled")

# @app.get("/keywords/{session_id}/{question_index}", response_model=KeywordsResponse)
# async def get_keywords(session_id: str, question_index: int):
#     """Get keywords for any question by index."""
#     # Implementation commented out temporarily
#     raise HTTPException(status_code=501, detail="Ideation endpoints temporarily disabled")

# @app.get("/summary/{session_id}", response_model=SummaryResponse)
# async def get_summary(session_id: str):
#     """Generate and return a comprehensive summary of the business idea analysis."""
#     # Implementation commented out temporarily
#     raise HTTPException(status_code=501, detail="Ideation endpoints temporarily disabled")

# @app.post("/reset", response_model=SessionResponse)
# async def reset_session(request: ResetRequest):
#     """Reset questions after a specific index."""
#     # Implementation commented out temporarily
#     raise HTTPException(status_code=501, detail="Ideation endpoints temporarily disabled")

# @app.get("/session/{session_id}", response_model=SessionResponse)
# async def get_session(session_id: str):
#     """Get the current state of a session."""
#     # Implementation commented out temporarily
#     raise HTTPException(status_code=501, detail="Ideation endpoints temporarily disabled")

# @app.delete("/session/{session_id}")
# async def delete_session(session_id: str):
#     """Delete a session."""
#     # Implementation commented out temporarily
#     raise HTTPException(status_code=501, detail="Ideation endpoints temporarily disabled")

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
            "ideation": "Temporarily disabled - import conflicts being resolved"
        },
        "status": "Multi-agent and BMC services active, ideation service temporarily disabled"
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
        port=8000,
        reload=True
    )