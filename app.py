#!/usr/bin/env python

import os
import logging
from datetime import datetime
from typing import List

# FastAPI imports
from fastapi import FastAPI
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

# Route handling
root_path = "/" 
if os.getenv("ROUTE"):
    root_path = os.getenv("ROUTE")
    if not root_path.startswith('/'):
        root_path = '/' + root_path

# Set deployment URL properly
base_route = os.environ.get('ROUTE', '')
if base_route and not base_route.startswith('/'):
    base_route = '/' + base_route
if base_route and not base_route.endswith('/'):
    base_route = base_route + '/'

os.environ["DEPLOYMENT_URL"] = f"https://qa-org2.katonic.ai{base_route}"

# Add Azure OpenAI configuration
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://katonic-oai-gpt4.openai.azure.com"
os.environ["AZURE_OPENAI_DEPLOYMENT"] = "gpt-4o"
os.environ["AZURE_OPENAI_API_VERSION"] = "2024-02-15-preview"

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
    root_path=root_path.rstrip('/') if root_path != '/' else ''
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to generate sales scripts
def generate_sales_script(product_name: str, target_audience: str, key_benefits: List[str]) -> dict:
    """Generate a simple sales script"""
    
    # Format benefits list
    benefits_list = "\n".join([f"• {benefit}" for benefit in key_benefits])
    
    # Simple script template
    script = f"""Hello, this is [Your Name] from [Company]. I hope I'm not catching you at a bad time.

I'm reaching out to {target_audience} because I know you're always looking for ways to improve your business.

We've developed {product_name} that specifically helps businesses like yours with:
{benefits_list}

I'd love to show you how {product_name} can benefit your business. 

Would you have 15 minutes this week for a quick demonstration?

What would work better for you - Tuesday afternoon or Thursday morning?"""
    
    # Count words
    word_count = len(script.split())
    
    return {
        "success": True,
        "script": script,
        "word_count": word_count
    }

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
        
    except Exception as e:
        logger.error(f"Error generating script: {e}")
        
        return SalesScriptResponse(
            success=False,
            script=f"Error generating script: {str(e)}",
            word_count=0
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """FastAPI startup event"""
    logger.info("Sales Script Generator API Started")
    logger.info(f"API Endpoint: {get_base_url()}/api/generate-script")
    logger.info(f"Interactive docs: {get_base_url()}/docs")

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
