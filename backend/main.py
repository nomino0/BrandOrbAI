import sys
import os
import json
import logging
import uuid
import base64
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from io import BytesIO
import sys
import os
import logging

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
from agents.swot_agent import SWOTAgent, run_swot_agent
from agents.viability_agent import run_viability_assessment
from agents.brand_identity_agent import BrandIdentityAgent, run_brand_identity_analysis
from agents.brand_discovery_agent import BrandDiscoveryAgent, BrandDiscoverySession, run_brand_discovery_analysis
from agents.brand_orchestrator import BrandOrchestrator, run_brand_orchestration
from agents.identity_orchestrator import IdentityOrchestrator, run_comprehensive_brand_identity, run_comprehensive_brand_identity

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

# Import vectorization service
from agents.identity.vectorization_api import vectorization_router

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

# Include routers
app.include_router(vectorization_router)

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
brand_identity_storage = {}  # For brand identity results
brand_discovery_sessions = {}  # For brand discovery sessions

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

# Brand Identity models
class BrandChatbotData(BaseModel):
    company_name: Optional[str] = None
    brand_values: Optional[List[str]] = []
    target_audience: Optional[str] = None
    brand_personality: Optional[str] = None
    visual_preferences: Optional[dict] = {}
    voice_tone_preferences: Optional[str] = None
    mission_input: Optional[str] = None
    vision_input: Optional[str] = None

class BrandIdentityRequest(BaseModel):
    business_summary: str
    chatbot_data: Optional[BrandChatbotData] = None

class LogoGenerationRequest(BaseModel):
    brand_name: str
    logo_concept: dict
    colors: List[str]

class BrandAssetsRequest(BaseModel):
    brand_book: dict
    logo_data: dict

# Brand Discovery models
class BrandDiscoveryInitRequest(BaseModel):
    session_id: str
    business_summary: str

class BrandDiscoveryResponseRequest(BaseModel):
    session_id: str
    response: Any

class BrandDiscoveryCompleteRequest(BaseModel):
    session_id: str
    responses: Dict[str, Any]
    include_existing_data: Optional[bool] = True

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
        
        runs[run_id] = state.to_dict()
        
        # Return the complete state without image generation (handled separately by frontend)
        return {
            "message": "done", 
            "run_id": run_id,
            "data": state.to_dict()
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
        "business_summary": os.path.join(
            os.path.dirname(__file__),
            "agents", "output", "business_summary.txt"
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
# VIABILITY ASSESSMENT ENDPOINTS
# =============================================================================

@app.post("/save-business-summary")
async def save_business_summary(request: dict):
    """Save business summary for use by other agents"""
    try:
        business_summary = request.get("summary", "")
        if not business_summary:
            raise HTTPException(status_code=400, detail="Business summary is required")
        
        # Save to output directory
        output_dir = os.path.join(os.path.dirname(__file__), "agents", "output")
        os.makedirs(output_dir, exist_ok=True)
        
        summary_path = os.path.join(output_dir, "business_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(business_summary)
        
        logger.info(f"Business summary saved to: {summary_path}")
        return {"message": "Business summary saved successfully", "path": summary_path}
        
    except Exception as e:
        logger.error(f"Error saving business summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save business summary: {str(e)}")

@app.post("/run-viability")
async def run_viability_analysis():
    """Generate comprehensive viability assessment based on existing agent outputs"""
    try:
        logger.info("Starting viability assessment")
        
        # Run viability assessment
        result = run_viability_assessment()
        
        if result.get("success", False):
            logger.info("Viability assessment completed successfully")
            return {"message": "Viability assessment completed", "status": "success", "data": result.get("data")}
        else:
            logger.error(f"Viability assessment failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=f"Viability assessment failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error in viability assessment endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Viability assessment failed: {str(e)}")

@app.get("/viability-output")
async def get_viability_output():
    """Get the latest viability assessment output"""
    output_path = os.path.join(os.path.dirname(__file__), "agents", "output", "viability_assessment_output.json")
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="No viability assessment output found")
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            content = json.load(f)
        return {"data": content}
    except Exception as e:
        logger.error(f"Error reading viability output: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to read viability output")

# =============================================================================
# SWOT ANALYSIS ENDPOINTS
# =============================================================================

@app.post("/run-swot")
async def run_swot_analysis():
    """Generate SWOT analysis based on existing agent outputs"""
    try:
        logger.info("Starting SWOT analysis")
        
        # Read business summary for the business idea
        business_idea = ""
        business_summary_path = os.path.join(os.path.dirname(__file__), "agents", "output", "business_summary.txt")
        if os.path.exists(business_summary_path):
            with open(business_summary_path, "r", encoding="utf-8") as f:
                raw_summary = f.read()
                # Extract business idea from summary, remove date line
                if "\nGenerated on" in raw_summary:
                    business_idea = raw_summary.split("\nGenerated on")[0][:200]
                else:
                    business_idea = raw_summary[:200]  # Get first 200 chars as business idea
        else:
            # Fallback: generic description
            business_idea = "Digital business platform"
        
        # Run complete SWOT analysis
        result = run_swot_agent(business_idea)
        
        if result.get("status") == "success":
            logger.info("SWOT analysis completed successfully")
            return {"message": "SWOT analysis completed", "status": "success", "data": result}
        else:
            logger.error(f"SWOT analysis failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=f"SWOT analysis failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error in SWOT analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SWOT analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SWOT analysis failed: {str(e)}")

@app.get("/swot-output")
async def get_swot_output():
    """Get the latest SWOT analysis output"""
    # Try to read from the complete JSON file first
    complete_path = os.path.join(os.path.dirname(__file__), "agents", "output", "swot_complete.json")
    
    if os.path.exists(complete_path):
        try:
            with open(complete_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Return the SWOT analysis data directly
            return {"content": data.get("swot_analysis", {})}
        except Exception as e:
            logger.error(f"Error reading SWOT complete file: {str(e)}")
    
    # Fallback: try the old format
    output_path = os.path.join(os.path.dirname(__file__), "agents", "output", "swot_output.txt")
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="No SWOT analysis output found. Please run SWOT analysis first.")
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        logger.error(f"Error reading SWOT output: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to read SWOT output")

# =============================================================================
# COMPREHENSIVE BRAND IDENTITY ENDPOINTS (New Orchestrator)
# =============================================================================

@app.post("/brand-identity/logo")
async def create_logo_only(request: dict):
    """Create logo only"""
    try:
        business_data = request.get("business_data", {})
        requirements = request.get("requirements", "")
        
        orchestrator = IdentityOrchestrator()
        
        # Generate logo
        logo_result = orchestrator.logo_agent.generate_comprehensive_logo(
            business_context=business_data.get("summary", ""),
            business_model_data=business_data.get("bmc", {}),
            brand_requirements=requirements
        )
        
        return {
            "success": True,
            "type": "logo",
            "options": ["Modern Logo", "Classic Logo", "Creative Logo"],
            "download_urls": logo_result.get("logo_urls", [])
        }
        
    except Exception as e:
        logger.error(f"Error in logo creation: {e}")
        return {"success": False, "error": str(e)}

@app.post("/brand-identity/colors")
async def create_colors_only(request: dict):
    """Create color palette only"""
    try:
        business_data = request.get("business_data", {})
        requirements = request.get("requirements", "")
        
        # Simple color palette generation
        palette = ["#2563EB", "#7C3AED", "#059669", "#DC2626", "#EA580C"]
        
        return {
            "success": True,
            "type": "colors",
            "palette": palette
        }
        
    except Exception as e:
        logger.error(f"Error in color creation: {e}")
        return {"success": False, "error": str(e)}

@app.post("/brand-identity/flyer")
async def create_flyer_only(request: dict):
    """Create flyer only"""
    try:
        business_data = request.get("business_data", {})
        requirements = request.get("requirements", "")
        
        orchestrator = IdentityOrchestrator()
        
        # Generate flyer
        flyer_result = orchestrator.flyer_agent.generate_comprehensive_flyer(
            business_context=business_data.get("summary", ""),
            business_model_data=business_data.get("bmc", {}),
            brand_requirements=requirements
        )
        
        return {
            "success": True,
            "type": "flyer",
            "designs": ["Business Flyer", "Marketing Flyer"],
            "download_urls": flyer_result.get("flyer_urls", [])
        }
        
    except Exception as e:
        logger.error(f"Error in flyer creation: {e}")
        return {"success": False, "error": str(e)}

@app.post("/brand-identity/comprehensive")
async def create_comprehensive_brand_identity(request: dict):
    """Create comprehensive brand identity using the identity orchestrator"""
    try:
        business_summary = request.get("business_summary", "")
        brand_discovery_data = request.get("brand_discovery_data")
        existing_business_data = request.get("existing_business_data")
        
        if not business_summary:
            raise HTTPException(status_code=400, detail="Business summary is required")
        
        logger.info("Starting comprehensive brand identity creation with orchestrator")
        
        # Load existing business data if not provided
        if not existing_business_data:
            try:
                existing_business_data = await _load_existing_business_data()
            except Exception as e:
                logger.warning(f"Could not load existing business data: {e}")
                existing_business_data = {}
        
        # Run comprehensive brand identity creation
        result = run_comprehensive_brand_identity(
            business_summary,
            brand_discovery_data,
            existing_business_data
        )
        
        if result.get("success"):
            # Store the result
            analysis_id = f"comprehensive_{int(datetime.now().timestamp())}"
            brand_identity_storage[analysis_id] = {
                "content": result["brand_identity"],
                "metadata": result.get("generation_metadata", {}),
                "created_at": datetime.now().isoformat()
            }
            
            # Save to file for persistence
            try:
                output_dir = os.path.join(os.path.dirname(__file__), "agents", "output")
                os.makedirs(output_dir, exist_ok=True)
                
                output_file = os.path.join(output_dir, f"comprehensive_brand_identity_{analysis_id}.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(brand_identity_storage[analysis_id], f, indent=2)
                    
            except Exception as e:
                logger.warning(f"Could not save comprehensive brand identity to file: {e}")
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "brand_identity": result["brand_identity"],
                "metadata": result.get("generation_metadata", {})
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Comprehensive brand identity creation failed")
            }
            
    except Exception as e:
        logger.error(f"Error in comprehensive brand identity endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brand-identity/services-status")
async def get_brand_identity_services_status():
    """Get status of all brand identity services"""
    try:
        orchestrator = IdentityOrchestrator()
        services_status = orchestrator._get_services_status()
        
        return {
            "services": services_status,
            "orchestrator_available": True,
            "identity_agents_path": os.path.join(os.path.dirname(__file__), "agents", "identity"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking services status: {e}")
        return {
            "services": {"error": str(e)},
            "orchestrator_available": False,
            "timestamp": datetime.now().isoformat()
        }

@app.post("/brand-identity/generate-logo")
async def generate_logo_via_orchestrator(request: dict):
    """Generate logo using the identity orchestrator"""
    try:
        business_description = request.get("business_description", "")
        logo_description = request.get("logo_description", "modern and professional")
        selected_colors = request.get("selected_colors", ["#2563EB", "#FFFFFF"])
        
        if not business_description:
            raise HTTPException(status_code=400, detail="Business description is required")
        
        orchestrator = IdentityOrchestrator()
        
        if not orchestrator.logo_agent:
            raise HTTPException(status_code=503, detail="Logo generation service not available")
        
        logo_result = orchestrator.logo_agent.generate_logo(
            business_description,
            logo_description,
            selected_colors
        )
        
        if logo_result and logo_result.get("success"):
            # Store the logo
            logo_id = f"logo_{int(datetime.now().timestamp())}"
            brand_identity_storage[logo_id] = {
                "type": "logo",
                "content": logo_result,
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "logo_id": logo_id,
                "logo_data": logo_result
            }
        else:
            return {
                "success": False,
                "error": "Logo generation failed"
            }
            
    except Exception as e:
        logger.error(f"Error in logo generation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/brand-identity/generate-flyer")
async def generate_flyer_via_orchestrator(request: dict):
    """Generate flyer using the identity orchestrator"""
    try:
        business_description = request.get("business_description", "")
        flyer_content = request.get("flyer_content", "")
        
        if not business_description:
            raise HTTPException(status_code=400, detail="Business description is required")
        
        orchestrator = IdentityOrchestrator()
        
        if not orchestrator.flyer_agent:
            raise HTTPException(status_code=503, detail="Flyer generation service not available")
        
        flyer_result = orchestrator.flyer_agent.generate_comprehensive_flyer(
            business_description,
            flyer_content or f"Professional flyer for {business_description}"
        )
        
        if flyer_result:
            # Store the flyer
            flyer_id = f"flyer_{int(datetime.now().timestamp())}"
            brand_identity_storage[flyer_id] = {
                "type": "flyer",
                "content": flyer_result,
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "flyer_id": flyer_id,
                "flyer_data": flyer_result
            }
        else:
            return {
                "success": False,
                "error": "Flyer generation failed"
            }
            
    except Exception as e:
        logger.error(f"Error in flyer generation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brand-identity/assets/{asset_id}")
async def get_brand_identity_asset(asset_id: str):
    """Get a specific brand identity asset (logo, flyer, etc.)"""
    try:
        if asset_id in brand_identity_storage:
            return {
                "success": True,
                "asset": brand_identity_storage[asset_id]
            }
        else:
            raise HTTPException(status_code=404, detail="Asset not found")
            
    except Exception as e:
        logger.error(f"Error retrieving asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# BRAND DISCOVERY ENDPOINTS
# =============================================================================

@app.post("/brand-discovery/init")
async def init_brand_discovery_session(request: BrandDiscoveryInitRequest):
    """Initialize a new brand discovery session"""
    try:
        logger.info(f"Initializing brand discovery session: {request.session_id}")
        
        # Create new discovery session
        session = BrandDiscoverySession(request.session_id, request.business_summary)
        brand_discovery_sessions[request.session_id] = session
        
        # Get first question
        current_question = session.get_current_question()
        
        return {
            "success": True,
            "session_id": request.session_id,
            "session_structure": session.agent.get_discovery_session_structure(),
            "current_question": current_question,
            "existing_analysis": session.analysis
        }
        
    except Exception as e:
        logger.error(f"Error initializing brand discovery session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/brand-discovery/respond")
async def respond_to_brand_discovery_question(request: BrandDiscoveryResponseRequest):
    """Submit response to current brand discovery question"""
    try:
        if request.session_id not in brand_discovery_sessions:
            raise HTTPException(status_code=404, detail="Brand discovery session not found")
        
        session = brand_discovery_sessions[request.session_id]
        result = session.submit_response(request.response)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "next_question": result["next_question"],
            "progress": session._calculate_progress()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to brand discovery question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brand-discovery/suggestions/{session_id}")
async def get_brand_discovery_suggestions(session_id: str, question_type: str = Query(...)):
    """Get suggestions for specific question types (e.g., business names)"""
    try:
        if session_id not in brand_discovery_sessions:
            raise HTTPException(status_code=404, detail="Brand discovery session not found")
        
        session = brand_discovery_sessions[session_id]
        
        if question_type == "business_name":
            suggestions = session.agent.generate_business_name_suggestions(session.business_summary)
            return {"suggestions": suggestions}
        
        return {"suggestions": []}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting brand discovery suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/brand-discovery/complete")
async def complete_brand_discovery(request: BrandDiscoveryCompleteRequest):
    """Complete brand discovery and create comprehensive brand identity"""
    try:
        logger.info(f"Completing brand discovery for session: {request.session_id}")
        
        if request.session_id not in brand_discovery_sessions:
            raise HTTPException(status_code=404, detail="Brand discovery session not found")
        
        session = brand_discovery_sessions[request.session_id]
        
        # Run brand discovery analysis
        discovery_result = run_brand_discovery_analysis(
            request.session_id, 
            session.business_summary, 
            request.responses
        )
        
        if not discovery_result["success"]:
            return {
                "success": False,
                "errors": discovery_result.get("errors", []),
                "warnings": discovery_result.get("warnings", [])
            }
        
        # Gather existing business data if requested
        existing_data = {}
        if request.include_existing_data:
            try:
                # Load existing analysis files
                existing_data = await _load_existing_business_data()
            except Exception as e:
                logger.warning(f"Could not load existing data: {e}")
        
        # Run brand orchestration
        orchestration_result = run_brand_orchestration(
            discovery_result["brand_brief"],
            existing_data
        )
        
        if not orchestration_result["success"]:
            return {
                "success": False,
                "error": orchestration_result.get("error", "Brand orchestration failed")
            }
        
        # Store result
        analysis_id = f"discovery_{request.session_id}_{int(datetime.now().timestamp())}"
        brand_identity_storage[analysis_id] = {
            "content": orchestration_result["brand_identity"],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "session_id": request.session_id,
                "discovery_data": discovery_result["brand_brief"],
                "orchestration_version": "2.0"
            }
        }
        
        # Save to file for persistence
        try:
            output_dir = os.path.join(os.path.dirname(__file__), "agents", "output")
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = os.path.join(output_dir, f"brand_identity_{analysis_id}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(brand_identity_storage[analysis_id], f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not save brand identity to file: {e}")
        
        # Clean up session
        if request.session_id in brand_discovery_sessions:
            del brand_discovery_sessions[request.session_id]
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "brand_identity": orchestration_result["brand_identity"],
            "discovery_data": discovery_result["brand_brief"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing brand discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/brand-discovery/session/{session_id}")
async def get_brand_discovery_session(session_id: str):
    """Get current brand discovery session state"""
    try:
        if session_id not in brand_discovery_sessions:
            raise HTTPException(status_code=404, detail="Brand discovery session not found")
        
        session = brand_discovery_sessions[session_id]
        current_question = session.get_current_question()
        
        return {
            "session_id": session_id,
            "current_question": current_question,
            "responses": session.responses,
            "progress": session._calculate_progress(),
            "created_at": session.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting brand discovery session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _load_existing_business_data() -> Dict[str, Any]:
    """Load existing business analysis data from files"""
    existing_data = {}
    output_dir = os.path.join(os.path.dirname(__file__), "agents", "output")
    
    # Load business summary
    business_summary_path = os.path.join(output_dir, "business_summary.txt")
    if os.path.exists(business_summary_path):
        with open(business_summary_path, "r", encoding="utf-8") as f:
            existing_data["business_summary"] = f.read()
    
    # Load SWOT analysis
    swot_path = os.path.join(output_dir, "swot_complete.json")
    if os.path.exists(swot_path):
        with open(swot_path, "r", encoding="utf-8") as f:
            existing_data["swot_analysis"] = json.load(f)
    
    # Load viability assessment
    viability_path = os.path.join(output_dir, "viability_assessment_output.json")
    if os.path.exists(viability_path):
        with open(viability_path, "r", encoding="utf-8") as f:
            existing_data["viability_assessment"] = json.load(f)
    
    # Load market analysis
    market_path = os.path.join(output_dir, "market_analysis_competitors_output.txt")
    if os.path.exists(market_path):
        with open(market_path, "r", encoding="utf-8") as f:
            existing_data["market_analysis"] = f.read()
    
    # Load BMC data
    bmc_path = os.path.join(output_dir, "bmc_output.txt")
    if os.path.exists(bmc_path):
        with open(bmc_path, "r", encoding="utf-8") as f:
            existing_data["bmc_data"] = f.read()
    
    return existing_data

# =============================================================================
# BRAND IDENTITY ENDPOINTS (Enhanced)
# =============================================================================

@app.post("/run-brand-identity")
async def run_brand_identity_analysis_endpoint(request: BrandIdentityRequest):
    """Run comprehensive brand identity analysis with chatbot integration"""
    try:
        # Convert chatbot data to dict if provided
        chatbot_data_dict = None
        if request.chatbot_data:
            chatbot_data_dict = request.chatbot_data.model_dump()
        
        logger.info("Starting brand identity analysis...")
        
        # Run the brand identity analysis
        result = run_brand_identity_analysis(
            business_summary=request.business_summary,
            chatbot_data=chatbot_data_dict
        )
        
        if result.get("success"):
            # Store the result with a unique ID
            analysis_id = str(uuid.uuid4())
            brand_identity_storage[analysis_id] = result
            
            logger.info("Brand identity analysis completed successfully")
            return {
                "message": "Brand identity analysis completed", 
                "status": "success", 
                "analysis_id": analysis_id,
                "data": result
            }
        else:
            logger.error(f"Brand identity analysis failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=500, 
                detail=f"Brand identity analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error in brand identity analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Brand identity analysis failed: {str(e)}")

@app.get("/brand-identity-output")
async def get_brand_identity_output(analysis_id: Optional[str] = None):
    """Get brand identity analysis output"""
    try:
        if analysis_id and analysis_id in brand_identity_storage:
            # Return specific analysis
            return {"content": brand_identity_storage[analysis_id]}
        elif brand_identity_storage:
            # Return the most recent analysis
            latest_id = max(brand_identity_storage.keys())
            return {"content": brand_identity_storage[latest_id]}
        else:
            # Return empty content instead of error when no analysis exists
            logger.info("No brand identity analysis found - returning empty content")
            return {"content": None, "message": "No brand identity analysis found"}
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error retrieving brand identity output: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve brand identity output")

@app.post("/generate-brand-palettes")
async def generate_brand_color_palettes(request: dict):
    """Generate color palettes for brand identity"""
    try:
        brand_context = request.get('brand_context', {})
        
        agent = BrandIdentityAgent()
        palettes = agent.generate_color_palettes(brand_context)
        
        return {"palettes": palettes}
        
    except Exception as e:
        logger.error(f"Error generating color palettes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate color palettes: {str(e)}")

@app.post("/generate-logo-concepts")
async def generate_brand_logo_concepts(request: dict):
    """Generate logo concepts for brand identity"""
    try:
        brand_context = request.get('brand_context', {})
        selected_colors = request.get('selected_colors', [])
        
        agent = BrandIdentityAgent()
        concepts = agent.generate_logo_concepts(brand_context, selected_colors)
        
        return {"concepts": concepts}
        
    except Exception as e:
        logger.error(f"Error generating logo concepts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate logo concepts: {str(e)}")

@app.post("/generate-logo-image")
async def generate_brand_logo_image(request: LogoGenerationRequest):
    """Generate actual logo image from concept"""
    try:
        agent = BrandIdentityAgent()
        logo_result = agent.generate_logo_image(
            brand_name=request.brand_name,
            logo_concept=request.logo_concept,
            colors=request.colors
        )
        
        if logo_result.get("success"):
            # Store the logo with unique ID
            logo_id = str(uuid.uuid4())
            brand_identity_storage[f"logo_{logo_id}"] = logo_result
            
            return {
                "success": True,
                "logo_id": logo_id,
                "logo_data": logo_result
            }
        else:
            raise HTTPException(status_code=500, detail=logo_result.get("error", "Logo generation failed"))
        
    except Exception as e:
        logger.error(f"Error generating logo image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate logo image: {str(e)}")

@app.post("/generate-brand-assets")
async def generate_brand_assets_endpoint(request: BrandAssetsRequest):
    """Generate additional brand assets like business cards, letterheads"""
    try:
        agent = BrandIdentityAgent()
        assets = agent.generate_brand_assets(
            brand_book=request.brand_book,
            logo_data=request.logo_data
        )
        
        # Store assets with unique ID
        assets_id = str(uuid.uuid4())
        brand_identity_storage[f"assets_{assets_id}"] = assets
        
        return {
            "success": True,
            "assets_id": assets_id,
            "assets": assets
        }
        
    except Exception as e:
        logger.error(f"Error generating brand assets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate brand assets: {str(e)}")

@app.get("/brand-identity-list")
async def list_brand_identity_analyses():
    """List all brand identity analyses"""
    try:
        analyses = []
        for key, value in brand_identity_storage.items():
            if not key.startswith(('logo_', 'assets_')):
                analyses.append({
                    "analysis_id": key,
                    "generation_time": value.get("generation_time", "Unknown"),
                    "success": value.get("success", False)
                })
        
        return {"analyses": analyses}
        
    except Exception as e:
        logger.error(f"Error listing brand identity analyses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list brand identity analyses")

# =============================================================================
# REVISION ENDPOINTS
# =============================================================================

@app.post("/brand-identity/revise")
async def revise_brand_identity(request: dict):
    """Expert revision of a brand identity section. Body: { current_identity, section, instruction }."""
    try:
        current_identity = request.get("current_identity")
        section = request.get("section")
        instruction = request.get("instruction", "")
        if not current_identity or not section:
            raise HTTPException(status_code=400, detail="current_identity and section are required")
        agent = BrandIdentityAgent()
        result = agent.revise_brand_identity(current_identity, section, instruction)
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revision error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/summary/{session_id}", response_model=SummaryResponse)
async def get_summary(session_id: str):
    """Generate and get summary for a session, automatically saving to business_summary.txt."""
    logger.info("=== GET SUMMARY ===")
    logger.info(f"Session ID: {session_id}")
    
    if session_id not in sessions:
        logger.error(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[session_id]
    logger.info(f"Generating summary for state: {state}")
    
    # Generate summary (this will automatically save to business_summary.txt)
    updated_state = generate_summary(state)
    sessions[session_id] = updated_state  # Update the session with the summary
    
    if not updated_state.summary:
        logger.error("Failed to generate summary")
        raise HTTPException(status_code=500, detail="Failed to generate summary")
    
    response_data = SummaryResponse(summary=updated_state.summary)
    logger.info(f"SUMMARY RESPONSE: Generated summary of length {len(updated_state.summary)}")
    logger.info("=== END GET SUMMARY ===\n")
    
    return response_data

@app.post("/summary-with-image/{session_id}", response_model=SummaryResponse)
async def get_summary_with_image(session_id: str):
    """Generate summary with image metadata, automatically saving to business_summary.txt."""
    logger.info("=== GET SUMMARY WITH IMAGE ===")
    logger.info(f"Session ID: {session_id}")
    
    if session_id not in sessions:
        logger.error(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[session_id]
    
    # Read existing image data if available
    image_data = {}
    try:
        image_output_path = os.path.join(os.path.dirname(__file__), "agents", "output", "image_generation_output.json")
        if os.path.exists(image_output_path):
            with open(image_output_path, "r", encoding="utf-8") as f:
                image_data = json.load(f)
    except Exception as e:
        logger.warning(f"Could not read image data: {e}")
    
    # Generate summary with image metadata (this will automatically save to business_summary.txt)
    updated_state = generate_summary(state, include_image_metadata=True, image_data=image_data)
    sessions[session_id] = updated_state  # Update the session with the summary
    
    if not updated_state.summary:
        logger.error("Failed to generate summary")
        raise HTTPException(status_code=500, detail="Failed to generate summary")
    
    response_data = SummaryResponse(summary=updated_state.summary)
    logger.info(f"SUMMARY WITH IMAGE RESPONSE: Generated summary of length {len(updated_state.summary)}")
    logger.info("=== END GET SUMMARY WITH IMAGE ===\n")
    
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
# LOGO GENERATION ENDPOINTS
# =============================================================================

@app.post("/logo/generate-palettes")
async def generate_logo_color_palettes(request: dict):
    """Generate color palettes for logo design"""
    try:
        from agents.identity.main import LogoGeneratorAgent
        
        business_description = request.get("business_description", "")
        if not business_description:
            raise HTTPException(status_code=400, detail="Business description is required")
        
        agent = LogoGeneratorAgent()
        palettes = agent.generate_color_palette(business_description)
        
        if palettes:
            return {
                "success": True,
                "palettes": palettes
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate color palettes"
            }
            
    except Exception as e:
        logger.error(f"Error generating color palettes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/logo/generate")
async def generate_logo(request: dict):
    """Generate a logo using Pollinations AI"""
    try:
        from agents.identity.main import LogoGeneratorAgent
        
        business_description = request.get("business_description", "")
        logo_description = request.get("logo_description", "modern logo")
        selected_colors = request.get("color_palette", request.get("selected_colors", ["#2563EB", "#1F2937"]))
        
        if not business_description:
            raise HTTPException(status_code=400, detail="Business description is required")
        
        agent = LogoGeneratorAgent()
        logo_result = agent.generate_logo(business_description, logo_description, selected_colors)
        
        if logo_result and logo_result.get('success'):
            # Return URL for frontend to display
            return {
                "success": True,
                "url": logo_result.get('image_url') or logo_result.get('url'),
                "logo": logo_result
            }
        else:
            error_msg = logo_result.get('error', 'Failed to generate logo') if logo_result else 'Failed to generate logo'
            return {
                "success": False,
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Error generating logo: {e}")
        # Return error response instead of raising exception to avoid 500 errors
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/logo/generate-3d")
async def generate_3d_logo(request: dict):
    """Generate a 3D version of a logo"""
    try:
        from agents.identity.main import LogoGeneratorAgent
        
        business_description = request.get("business_description", "")
        logo_description = request.get("logo_description", "modern logo")
        selected_colors = request.get("color_palette", request.get("selected_colors", ["#2563EB", "#1F2937"]))
        base_logo_prompt = request.get("base_logo_prompt", None)
        
        if not business_description:
            raise HTTPException(status_code=400, detail="Business description is required")
        
        agent = LogoGeneratorAgent()
        logo_result = agent.generate_3d_logo(business_description, logo_description, selected_colors, base_logo_prompt)
        
        if logo_result and logo_result.get('success'):
            return {
                "success": True,
                "logo_3d": logo_result
            }
        else:
            return {
                "success": False,
                "error": logo_result.get('error', 'Failed to generate 3D logo')
            }
            
    except Exception as e:
        logger.error(f"Error generating 3D logo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/logo/suggestions")
async def get_logo_suggestions(request: dict):
    """Get suggested keywords for logo design"""
    try:
        from agents.identity.main import LogoGeneratorAgent
        
        business_description = request.get("business_description", "")
        if not business_description:
            raise HTTPException(status_code=400, detail="Business description is required")
        
        agent = LogoGeneratorAgent()
        suggestions = agent.generate_suggested_keywords(business_description)
        
        if suggestions:
            return {
                "success": True,
                "suggestions": suggestions
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate suggestions"
            }
            
    except Exception as e:
        logger.error(f"Error generating logo suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# BRAND NAME GENERATION ENDPOINT
# =============================================================================

@app.post("/logo/generate-names")
async def generate_brand_names(request: dict):
    """Generate brand name suggestions using AI"""
    try:
        from agents.identity.main import LogoGeneratorAgent
        
        business_description = request.get("business_description", "")
        if not business_description:
            raise HTTPException(status_code=400, detail="Business description is required")
        
        agent = LogoGeneratorAgent()
        
        # Use AI to generate brand name suggestions
        name_prompt = f"""
        Based on this business description: "{business_description}"
        
        Generate 8 creative, brandable business names that are:
        - Short (1-3 words max)
        - Memorable and catchy
        - Professional sounding
        - Relevant to the business
        - Easy to pronounce
        - Suitable for branding
        
        Return the response in this exact JSON format:
        {{
            "names": ["Name1", "Name2", "Name3", "Name4", "Name5", "Name6", "Name7", "Name8"]
        }}
        """
        
        response = agent.client.chat.completions.create(
            model=agent.model,
            messages=[{"role": "user", "content": name_prompt}],
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        # Extract JSON from the response
        import json
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                name_data = json.loads(json_match.group())
                if 'names' in name_data and len(name_data['names']) > 0:
                    return {
                        "success": True,
                        "names": name_data['names']
                    }
            except json.JSONDecodeError:
                pass
        
        # Fallback if JSON parsing fails
        return {
            "success": False,
            "error": "Failed to generate brand names",
            "names": []
        }
        
    except Exception as e:
        logger.error(f"Error generating brand names: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
            "brand_identity": "/run-brand-identity, /brand-identity/revise, /generate-brand-palettes",
            "brand_discovery": "/brand-discovery/init, /brand-discovery/respond, /brand-discovery/suggestions, /brand-discovery/complete",
            "logo_generation": "/logo/generate-palettes, /logo/generate, /logo/generate-3d, /logo/suggestions",
            "logo_vectorization": "/vectorize-logo",
            "vectorization": "/vectorization/vectorize, /vectorization/vectorize/upload/autotrace, /vectorization/vectorize/upload/potrace, /vectorization/health",
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
# STOCK IMAGES API ENDPOINTS
# =============================================================================

class StockImageRequest(BaseModel):
    query: str
    perPage: int = 8
    page: int = 1
    orientation: str = "landscape"

@app.post("/stock-images")
async def get_stock_images(request: StockImageRequest):
    """Get stock images from Pexels API"""
    logger.info(f"=== STOCK IMAGES REQUEST: {request.query} ===")
    
    try:
        headers = {
            'Authorization': 't2kXItoCsRYzjXRMm2muPOVE0fanryzMiD13aywXH7o6RPAmphADpkeh'
        }
        
        params = {
            'query': request.query,
            'per_page': request.perPage,
            'page': request.page,
            'orientation': request.orientation
        }
        
        logger.info(f"Calling Pexels API with query: '{request.query}'")
        
        response = requests.get(
            'https://api.pexels.com/v1/search',
            headers=headers,
            params=params,
            timeout=30
        )
        
        logger.info(f"Pexels API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            photo_count = len(result.get("photos", []))
            logger.info(f"✅ Stock images successful! Found {photo_count} photos")
            return result
        else:
            error_msg = f"Failed to fetch stock images: {response.status_code}"
            if response.text:
                error_msg += f" - {response.text[:200]}"
            logger.error(error_msg)
            raise HTTPException(status_code=response.status_code, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock images error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# LOGO VECTORIZATION API ENDPOINTS
# =============================================================================

class VectorizeLogoRequest(BaseModel):
    logoUrl: str
    method: str = "autotrace"  # autotrace or potrace
    colorCount: Optional[int] = 8  # Number of colors to extract from SVG
    threshold: Optional[str] = "60%"  # Threshold for potrace
    generateVariations: bool = True  # Generate meaningful color variations
    preprocessImage: bool = False  # NEW: Disabled for direct approach
    aiSeparation: bool = False  # NEW: Disabled for direct approach
    noBackgroundRemoval: Optional[bool] = True  # NEW: Keep background intact
    createPngVariations: Optional[bool] = True  # NEW: Create PNG versions

class VectorizeLogoResponse(BaseModel):
    success: bool
    vectorizedLogoUrl: Optional[str] = None
    svgContent: Optional[str] = None
    vectorizationStatus: str
    metadata: Optional[Dict[str, Any]] = None
    logoVariations: Optional[Dict[str, Any]] = None  # Logo variations
    error: Optional[str] = None

@app.post("/vectorize-logo", response_model=VectorizeLogoResponse)
async def vectorize_logo(request: VectorizeLogoRequest):
    """🎯 PURE PYTHON logo vectorization with meaningful color variations"""
    logger.info(f"=== 🎯 PURE PYTHON VECTORIZE LOGO REQUEST: {request.logoUrl[:100]}... ===")
    logger.info(f"Pure Python Method: {request.method}, Colors: {request.colorCount}")
    
    try:
        # Use PURE PYTHON vectorization approach
        logger.info(f"🎯 Starting PURE PYTHON vectorization (no external dependencies)...")
        
        vectorized_logo_url = None
        svg_content = None
        vectorization_status = "pending"
        metadata = {}
        logo_variations = {}
        
        try:
            # Use our pure Python vectorization service
            from agents.identity.vectorization_service import create_vectorization_service
            
            logger.info(f"🎯 Processing logo with PURE PYTHON approach...")
            
            # Create vectorization service instance
            vectorization_service = create_vectorization_service()
            
            # ENHANCED APPROACH: Pure Python vectorization with upscaling and pixel-to-vector conversion
            logger.info("🎯 ENHANCED VECTORIZATION: Upscaling + Pixel-to-Vector + 7 Variations (incl. Grayscale)")
            result = vectorization_service.vectorize_image_with_ai_separation(
                image_url=request.logoUrl,
                method="python_svg",
                target_size=1200,  # Higher resolution for better vectors
                upscale_factor=2.0,  # Minimum 2x upscaling
                color_count=request.colorCount or 12,  # More colors for better analysis
                generate_variations=request.generateVariations,
                create_png_variations=getattr(request, 'createPngVariations', True)
            )
            
            logger.info(f"🎯 Enhanced vectorization result: {result.get('success', False)} - Grayscale variation included")
            
            if result.get("success"):
                # Get SVG content
                svg_content = result.get("svg_content")
                if svg_content:
                    # Convert SVG to data URL
                    vectorized_logo_url = vectorization_service.get_svg_as_data_url(svg_content)
                    vectorization_status = "success_enhanced_upscaled_vector"
                    metadata = result.get("metadata", {})
                    
                    # Get variations created by SVG processing
                    if result.get("variations"):
                        logo_variations = result["variations"]
                        colors_found = metadata.get("colors_found", 0)
                        meaningful_variations = metadata.get("meaningful_variations", 0)
                        
                        logger.info(f"✅ Enhanced vectorization successful! Upscaled with {result['metadata']['colors_found']} colors + Grayscale variation")
                        logger.info(f"🎯 Found {colors_found} colors, created {meaningful_variations} meaningful variations")
                        logger.info(f"📊 No external dependencies, preserves original image integrity")
                        
                else:
                    vectorization_status = "no_svg_content"
                    logger.warning("Pure Python vectorization successful but no SVG content returned")
            else:
                error_msg = result.get("error", "Unknown error")
                vectorization_status = f"pure_python_failed"
                logger.warning(f"Pure Python vectorization failed: {error_msg}")
                
        except ImportError as e:
            vectorization_status = "vectorization_service_not_available"
            logger.warning(f"Pure Python vectorization service not available: {e}")
        except Exception as e:
            vectorization_status = f"pure_python_error_{type(e).__name__}"
            logger.warning(f"Pure Python vectorization error: {str(e)}")
        
        logger.info(f"✅ Pure Python vectorization complete - status: {vectorization_status}")
        
        return VectorizeLogoResponse(
            success=bool(vectorized_logo_url),
            vectorizedLogoUrl=vectorized_logo_url,
            svgContent=svg_content,
            vectorizationStatus=vectorization_status,
            metadata=metadata,
            logoVariations=logo_variations if logo_variations else None,
            error=None if vectorized_logo_url else f"Pure Python vectorization failed: {vectorization_status}"
        )
        
    except Exception as e:
        logger.error(f"Pure Python logo vectorization error: {str(e)}")
        return VectorizeLogoResponse(
            success=False,
            vectorizedLogoUrl=None,
            svgContent=None,
            vectorizationStatus="error",
            metadata=None,
            logoVariations=None,
            error=f"Failed to vectorize logo: {str(e)}"
        )

# =============================================================================
# LOGO VARIATIONS GENERATION FUNCTIONS
# =============================================================================

async def generate_logo_variations(svg_content: str, vectorization_service=None):
    """Generate different logo variations from SVG content"""
    try:
        variations = {}
        
        # Parse SVG to get dimensions and elements
        import xml.etree.ElementTree as ET
        from io import StringIO
        import re
        
        # Clean SVG content and parse
        svg_root = ET.fromstring(svg_content)
        
        # Get original dimensions
        width = svg_root.get('width', '1024')
        height = svg_root.get('height', '1024')
        viewbox = svg_root.get('viewBox', f'0 0 {width} {height}')
        
        # Extract numeric values from dimensions
        width_num = int(re.search(r'\d+', str(width)).group()) if re.search(r'\d+', str(width)) else 1024
        height_num = int(re.search(r'\d+', str(height)).group()) if re.search(r'\d+', str(height)) else 1024
        
        # 1. Primary Logo (Original)
        variations['primary'] = {
            'name': 'Primary Logo',
            'description': 'Main logo version for general use',
            'svg_content': svg_content,
            'data_url': vectorization_service.get_svg_as_data_url(svg_content) if vectorization_service else None,
            'dimensions': {'width': width_num, 'height': height_num},
            'usage': 'Headers, business cards, primary branding'
        }
        
        # 2. Horizontal Version (if not already horizontal)
        if height_num > width_num * 0.6:  # If logo is more square/vertical
            horizontal_svg = create_horizontal_variation(svg_content, svg_root, width_num, height_num)
            variations['horizontal'] = {
                'name': 'Horizontal Logo',
                'description': 'Wide format logo for headers and banners',
                'svg_content': horizontal_svg,
                'data_url': vectorization_service.get_svg_as_data_url(horizontal_svg) if vectorization_service else None,
                'dimensions': {'width': width_num * 1.5, 'height': height_num * 0.7},
                'usage': 'Website headers, email signatures, letterheads'
            }
        
        # 3. Vertical/Stacked Version
        vertical_svg = create_vertical_variation(svg_content, svg_root, width_num, height_num)
        variations['vertical'] = {
            'name': 'Vertical Logo',
            'description': 'Stacked logo for narrow spaces',
            'svg_content': vertical_svg,
            'data_url': vectorization_service.get_svg_as_data_url(vertical_svg) if vectorization_service else None,
            'dimensions': {'width': width_num * 0.8, 'height': height_num * 1.3},
            'usage': 'Social media profiles, mobile apps, narrow layouts'
        }
        
        # 4. Icon/Brandmark Only (extract main graphic element)
        icon_svg = create_icon_variation(svg_content, svg_root, width_num, height_num)
        variations['icon'] = {
            'name': 'Icon/Brandmark',
            'description': 'Graphic element only, no text',
            'svg_content': icon_svg,
            'data_url': vectorization_service.get_svg_as_data_url(icon_svg) if vectorization_service else None,
            'dimensions': {'width': min(width_num, height_num), 'height': min(width_num, height_num)},
            'usage': 'Favicons, app icons, social media avatars'
        }
        
        # 5. Wordmark/Logotype (text elements only)
        wordmark_svg = create_wordmark_variation(svg_content, svg_root, width_num, height_num)
        if wordmark_svg:
            variations['wordmark'] = {
                'name': 'Wordmark/Logotype',
                'description': 'Text-only version of the logo',
                'svg_content': wordmark_svg,
                'data_url': vectorization_service.get_svg_as_data_url(wordmark_svg) if vectorization_service else None,
                'dimensions': {'width': width_num * 1.2, 'height': height_num * 0.4},
                'usage': 'Minimal applications, fine print, watermarks'
            }
        
        # 6. One-Color (Black) Version
        onecolor_svg = create_onecolor_variation(svg_content, svg_root, '#000000')
        variations['onecolor_black'] = {
            'name': 'One-Color (Black)',
            'description': 'Single black color version',
            'svg_content': onecolor_svg,
            'data_url': vectorization_service.get_svg_as_data_url(onecolor_svg) if vectorization_service else None,
            'dimensions': {'width': width_num, 'height': height_num},
            'usage': 'Photocopying, fax, single-color printing'
        }
        
        # 7. Reversed Out (White) Version
        reversed_svg = create_onecolor_variation(svg_content, svg_root, '#FFFFFF')
        variations['reversed_white'] = {
            'name': 'Reversed Out (White)',
            'description': 'White version for dark backgrounds',
            'svg_content': reversed_svg,
            'data_url': vectorization_service.get_svg_as_data_url(reversed_svg) if vectorization_service else None,
            'dimensions': {'width': width_num, 'height': height_num},
            'usage': 'Dark backgrounds, merchandise, packaging'
        }
        
        logger.info(f"Generated {len(variations)} logo variations successfully")
        return variations
        
    except Exception as e:
        logger.error(f"Error generating logo variations: {str(e)}")
        return {}

async def generate_png_logo_variations(png_bytes: bytes):
    """Generate logo variations from PNG with transparent background"""
    try:
        variations = {}
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Load the original PNG
        original_image = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
        width, height = original_image.size
        
        # 1. Primary Logo (Original PNG)
        buffer = io.BytesIO()
        original_image.save(buffer, format='PNG')
        variations['primary'] = {
            'name': 'Primary Logo',
            'description': 'Main PNG logo with transparent background',
            'data_url': f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}",
            'dimensions': {'width': width, 'height': height},
            'usage': 'Digital use, websites, presentations'
        }
        
        # 2. Horizontal Version (if logo is tall)
        if height > width * 0.6:
            horizontal_img = create_horizontal_png(original_image)
            buffer = io.BytesIO()
            horizontal_img.save(buffer, format='PNG')
            variations['horizontal'] = {
                'name': 'Horizontal Logo',
                'description': 'Wide format PNG for headers',
                'data_url': f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}",
                'dimensions': {'width': horizontal_img.size[0], 'height': horizontal_img.size[1]},
                'usage': 'Website headers, banners'
            }
        
        # 3. Icon Version (square crop of main element)
        icon_img = create_icon_png(original_image)
        buffer = io.BytesIO()
        icon_img.save(buffer, format='PNG')
        variations['icon'] = {
            'name': 'Icon/Brandmark',
            'description': 'Square icon version',
            'data_url': f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}",
            'dimensions': {'width': icon_img.size[0], 'height': icon_img.size[1]},
            'usage': 'App icons, social media avatars'
        }
        
        # 4. One-Color Black Version
        black_img = create_onecolor_png(original_image, (0, 0, 0, 255))
        buffer = io.BytesIO()
        black_img.save(buffer, format='PNG')
        variations['onecolor_black'] = {
            'name': 'One-Color (Black)',
            'description': 'Black version for single-color printing',
            'data_url': f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}",
            'dimensions': {'width': black_img.size[0], 'height': black_img.size[1]},
            'usage': 'Photocopying, single-color print'
        }
        
        # 5. White Version
        white_img = create_onecolor_png(original_image, (255, 255, 255, 255))
        buffer = io.BytesIO()
        white_img.save(buffer, format='PNG')
        variations['reversed_white'] = {
            'name': 'Reversed Out (White)',
            'description': 'White version for dark backgrounds',
            'data_url': f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}",
            'dimensions': {'width': white_img.size[0], 'height': white_img.size[1]},
            'usage': 'Dark backgrounds, merchandise'
        }
        
        logger.info(f"Generated {len(variations)} PNG-based logo variations")
        return variations
        
    except Exception as e:
        logger.error(f"Error generating PNG logo variations: {str(e)}")
        return {}

def create_horizontal_variation(svg_content: str, svg_root, width: int, height: int):
    """Create horizontal layout variation"""
    try:
        # Simple approach: adjust viewBox to make it wider
        new_viewbox = f"0 0 {width * 1.5} {height * 0.7}"
        horizontal_svg = svg_content.replace(
            svg_root.get('viewBox', f'0 0 {width} {height}'),
            new_viewbox
        )
        return horizontal_svg
    except:
        return svg_content

def create_vertical_variation(svg_content: str, svg_root, width: int, height: int):
    """Create vertical/stacked layout variation"""
    try:
        # Simple approach: adjust viewBox to make it taller
        new_viewbox = f"0 0 {width * 0.8} {height * 1.3}"
        vertical_svg = svg_content.replace(
            svg_root.get('viewBox', f'0 0 {width} {height}'),
            new_viewbox
        )
        return vertical_svg
    except:
        return svg_content

def create_icon_variation(svg_content: str, svg_root, width: int, height: int):
    """Create icon-only variation by focusing on graphic elements"""
    try:
        # Create a square viewBox focusing on the center
        size = min(width, height)
        offset_x = (width - size) // 2
        offset_y = (height - size) // 2
        new_viewbox = f"{offset_x} {offset_y} {size} {size}"
        
        icon_svg = svg_content.replace(
            svg_root.get('viewBox', f'0 0 {width} {height}'),
            new_viewbox
        )
        return icon_svg
    except:
        return svg_content

def create_wordmark_variation(svg_content: str, svg_root, width: int, height: int):
    """Create text-only variation"""
    try:
        # This is a simplified approach - in a real implementation,
        # you'd parse SVG elements and extract text elements only
        import re
        
        # Look for text elements in SVG
        if '<text' in svg_content or 'font' in svg_content.lower():
            # Create a wider, shorter viewBox for text
            new_viewbox = f"0 0 {width * 1.2} {height * 0.4}"
            wordmark_svg = svg_content.replace(
                svg_root.get('viewBox', f'0 0 {width} {height}'),
                new_viewbox
            )
            return wordmark_svg
        return None
    except:
        return None

def create_onecolor_variation(svg_content: str, svg_root, color: str):
    """Create single-color variation"""
    try:
        import re
        
        # Replace all fill colors with the specified color
        onecolor_svg = re.sub(r'fill="[^"]*"', f'fill="{color}"', svg_content)
        onecolor_svg = re.sub(r'stroke="[^"]*"', f'stroke="{color}"', onecolor_svg)
        
        # Handle style attributes
        onecolor_svg = re.sub(r'fill:[^;]*;', f'fill:{color};', onecolor_svg)
        onecolor_svg = re.sub(r'stroke:[^;]*;', f'stroke:{color};', onecolor_svg)
        
        return onecolor_svg
    except:
        return svg_content

def create_horizontal_png(image):
    """Create horizontal PNG variation"""
    try:
        from PIL import Image
        
        # Create a wider canvas
        new_width = int(image.width * 1.5)
        new_height = int(image.height * 0.8)
        
        horizontal_img = Image.new('RGBA', (new_width, new_height), (255, 255, 255, 0))
        
        # Paste original image in center
        x_offset = (new_width - image.width) // 2
        y_offset = (new_height - image.height) // 2
        horizontal_img.paste(image, (x_offset, y_offset), image)
        
        return horizontal_img
    except:
        return image

def create_icon_png(image):
    """Create square icon PNG"""
    try:
        from PIL import Image
        
        # Create square dimensions
        size = min(image.width, image.height)
        icon_img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        
        # Crop to center square
        left = (image.width - size) // 2
        top = (image.height - size) // 2
        cropped = image.crop((left, top, left + size, top + size))
        
        icon_img.paste(cropped, (0, 0), cropped)
        return icon_img
    except:
        return image

def create_onecolor_png(image, color):
    """Create single-color PNG variation"""
    try:
        from PIL import Image
        
        # Convert to grayscale first to get the alpha mask
        grayscale = image.convert('LA')
        
        # Create new image with specified color
        onecolor_img = Image.new('RGBA', image.size, (255, 255, 255, 0))
        
        # Apply color based on original image's alpha
        pixels = list(image.getdata())
        new_pixels = []
        
        for pixel in pixels:
            if len(pixel) == 4:  # RGBA
                if pixel[3] > 0:  # If not transparent
                    new_pixels.append((color[0], color[1], color[2], pixel[3]))
                else:
                    new_pixels.append((255, 255, 255, 0))
            else:
                new_pixels.append(color)
        
        onecolor_img.putdata(new_pixels)
        return onecolor_img
    except:
        return image

# =============================================================================
# BRAND GUIDELINES EXPORT ENDPOINTS
# =============================================================================

class BrandGuidelinesExportRequest(BaseModel):
    brandData: Dict[str, Any]
    format: str = "pdf"

class BrandGuidelinesExportResponse(BaseModel):
    success: bool
    downloadUrl: Optional[str] = None
    error: Optional[str] = None

@app.post("/brand-guidelines/export", response_model=BrandGuidelinesExportResponse)
async def export_brand_guidelines(request: BrandGuidelinesExportRequest):
    """Export brand guidelines to various formats"""
    logger.info(f"=== BRAND GUIDELINES EXPORT: {request.format} ===")
    
    try:
        brand_data = request.brandData
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if request.format == "json":
            filename = f"brand_guidelines_{timestamp}.json"
            filepath = os.path.join("agents", "output", filename)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(brand_data, f, indent=2)
            
            return BrandGuidelinesExportResponse(
                success=True,
                downloadUrl=f"/download/{filename}"
            )
            
        elif request.format == "html":
            # Generate HTML brand guidelines
            html_content = generate_html_guidelines(brand_data)
            filename = f"brand_guidelines_{timestamp}.html"
            filepath = os.path.join("agents", "output", filename)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return BrandGuidelinesExportResponse(
                success=True,
                downloadUrl=f"/download/{filename}"
            )
            
        else:  # PDF format
            # For PDF generation, you would need a library like reportlab or weasyprint
            # For now, return a text format
            text_content = generate_text_guidelines(brand_data)
            filename = f"brand_guidelines_{timestamp}.txt"
            filepath = os.path.join("agents", "output", filename)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            return BrandGuidelinesExportResponse(
                success=True,
                downloadUrl=f"/download/{filename}"
            )
            
    except Exception as e:
        logger.error(f"Brand guidelines export error: {str(e)}")
        return BrandGuidelinesExportResponse(
            success=False,
            error=str(e)
        )

def generate_html_guidelines(brand_data: Dict[str, Any]) -> str:
    """Generate HTML brand guidelines"""
    colors_html = ""
    if brand_data.get("colors"):
        colors_html = "<div class='colors'>"
        for color in brand_data["colors"]:
            colors_html += f'<div class="color-swatch" style="background-color: {color}"><span>{color}</span></div>'
        colors_html += "</div>"
    
    personality_html = ""
    if brand_data.get("personality"):
        personality_html = "<ul>"
        for trait in brand_data["personality"]:
            personality_html += f"<li>{trait}</li>"
        personality_html += "</ul>"
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{brand_data.get('name', 'Brand')} Guidelines</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
            h2 {{ color: #666; margin-top: 30px; }}
            .colors {{ display: flex; gap: 20px; margin: 20px 0; }}
            .color-swatch {{ 
                width: 100px; height: 100px; border-radius: 8px; 
                display: flex; align-items: center; justify-content: center;
                color: white; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
            }}
            .logo {{ text-align: center; margin: 20px 0; }}
            .logo img {{ max-width: 300px; max-height: 200px; }}
        </style>
    </head>
    <body>
        <h1>{brand_data.get('name', 'Brand')} Brand Guidelines</h1>
        
        <h2>Brand Logo</h2>
        <div class="logo">
            {f'<img src="{brand_data["logoUrl"]}" alt="Brand Logo" />' if brand_data.get("logoUrl") else '<p>Logo not available</p>'}
        </div>
        
        <h2>Color Palette</h2>
        {colors_html}
        
        <h2>Brand Personality</h2>
        {personality_html}
        
        <h2>Brand Description</h2>
        <p>{brand_data.get('customDescription', 'No description provided')}</p>
        
        <h2>Usage Guidelines</h2>
        <ul>
            <li>Maintain proper logo clear space</li>
            <li>Use brand colors consistently</li>
            <li>Follow typography guidelines</li>
            <li>Ensure brand voice consistency</li>
        </ul>
        
        <p><em>Generated on {datetime.now().strftime("%B %d, %Y")}</em></p>
    </body>
    </html>
    """
    
    return html_template

def generate_text_guidelines(brand_data: Dict[str, Any]) -> str:
    """Generate text brand guidelines"""
    text = f"""
{brand_data.get('name', 'Brand')} Brand Guidelines
{'='*50}

Brand Colors:
{chr(10).join([f'- {color}' for color in brand_data.get('colors', [])])}

Brand Personality:
{chr(10).join([f'- {trait}' for trait in brand_data.get('personality', [])])}

Brand Description:
{brand_data.get('customDescription', 'No description provided')}

Logo Usage Guidelines:
- Maintain minimum clear space around logo
- Use on appropriate backgrounds for visibility
- Never distort or stretch the logo
- Use vector formats when possible

Typography Guidelines:
- Use consistent font families
- Maintain proper hierarchy
- Ensure readability across all media

Generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
    """
    
    return text.strip()

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated files"""
    filepath = os.path.join("agents", "output", filename)
    
    if os.path.exists(filepath):
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/octet-stream'
        )
    else:
        raise HTTPException(status_code=404, detail="File not found")

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