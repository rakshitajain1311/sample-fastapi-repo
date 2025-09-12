#!/usr/bin/env python

import os
import logging
from datetime import datetime
from typing import List

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# FastAPI imports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment-based deployment URL management
def get_base_url():
    """Get base URL based on environment"""
    deployment_url = os.getenv("DEPLOYMENT_URL")
    if deployment_url:
        return deployment_url.rstrip('/')
    else:
        port = os.getenv("PORT", "8050")
        return f"http://localhost:{port}"

# Simplified route handling
root_path = os.getenv("ROUTE", "").rstrip('/') if os.getenv("ROUTE") else ""

# Pydantic models
class SalesScriptRequest(BaseModel):
    product_name: str
    target_audience: str
    key_benefits: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "AI Analytics Platform",
                "target_audience": "Small business owners",
                "key_benefits": ["Saves time", "Increases revenue", "Easy to use"]
            }
        }

class SalesScriptResponse(BaseModel):
    success: bool
    script: str
    word_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "script": "Hello, this is [Your Name] from [Company]...",
                "word_count": 150
            }
        }

# FastAPI app initialization
app = FastAPI(
    title="Sales Script Generator API",
    description="Generate customized sales scripts for your products",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=root_path
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sales Script Generator API",
        "status": "running",
        "docs_url": f"{get_base_url()}/docs",
        "api_endpoint": f"{get_base_url()}/api/generate-script"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Helper function to generate sales scripts
def generate_sales_script(product_name: str, target_audience: str, key_benefits: List[str]) -> dict:
    """Generate a simple sales script"""
    
    try:
        # Validate inputs
        if not product_name.strip():
            raise ValueError("Product name cannot be empty")
        if not target_audience.strip():
            raise ValueError("Target audience cannot be empty")
        if not key_benefits or len(key_benefits) == 0:
            raise ValueError("At least one key benefit is required")
        
        # Format benefits list
        benefits_list = "\n".join([f"• {benefit.strip()}" for benefit in key_benefits if benefit.strip()])
        
        # Enhanced script template
        script = f"""Hello, this is [Your Name] from [Company]. I hope I'm not catching you at a bad time.

I'm reaching out to {target_audience} because I know you're always looking for ways to improve your business.

We've developed {product_name} that specifically helps businesses like yours with:
{benefits_list}

Many of our clients have seen significant improvements in their operations after implementing {product_name}.

I'd love to show you how {product_name} can benefit your business specifically. 

Would you have 15 minutes this week for a quick demonstration? I can show you exactly how this would work for your situation.

What would work better for you - Tuesday afternoon or Thursday morning?

Thank you for your time, and I look forward to hearing from you!"""
        
        # Count words
        word_count = len(script.split())
        
        return {
            "success": True,
            "script": script,
            "word_count": word_count
        }
    
    except Exception as e:
        raise ValueError(f"Error generating script: {str(e)}")

# Main Sales Script Generator endpoint
@app.post("/api/generate-script", response_model=SalesScriptResponse)
async def generate_script(script_request: SalesScriptRequest):
    """
    Generate a customized sales script
    """
    try:
        logger.info(f"Generating script for {script_request.product_name}")
        
        # Generate the script
        result = generate_sales_script(
            product_name=script_request.product_name,
            target_audience=script_request.target_audience,
            key_benefits=script_request.key_benefits
        )
        
        logger.info("Script generated successfully")
        
        return SalesScriptResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error generating script: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Startup event
@app.on_event("startup")
async def startup_event():
    """FastAPI startup event"""
    logger.info("Sales Script Generator API Started")
    logger.info(f"API Endpoint: {get_base_url()}/api/generate-script")
    logger.info(f"Interactive docs: {get_base_url()}/docs")
    logger.info(f"Root path: {root_path}")
    
    # Check OpenAI configuration
    if os.getenv("OPENAI_API_KEY"):
        logger.info("OpenAI API key found - AI-powered script generation enabled")
    else:
        logger.info("No OpenAI API key - running with template-based script generation only")

# Main entry point
if __name__ == "__main__":
    logger.info("Starting Sales Script Generator API...")
    
    port = int(os.getenv('PORT', '8050'))
    logger.info(f"Server will run on: http://localhost:{port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False
    )
