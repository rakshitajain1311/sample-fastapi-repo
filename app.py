#!/usr/bin/env python

import asyncio
import json
import logging
import os
import sys
import threading
import time
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# FastAPI imports
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FIXED: Environment-based deployment URL management - Following app.py pattern
def get_base_url():
    """Get base URL based on environment - Following app.py pattern"""
    deployment_url = os.getenv("DEPLOYMENT_URL")
    if deployment_url:
        return deployment_url.rstrip('/')
    else:
        port = os.getenv("PORT", "8050")
        return f"http://localhost:{port}"

# FIXED: Route handling following app.py pattern
root_path = "/" 
if os.getenv("ROUTE"):
    root_path = os.getenv("ROUTE")
    if not root_path.startswith('/'):
        root_path = '/' + root_path

# FIXED: Set deployment URL properly following app.py pattern
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

# FIXED: Deployment Information Hub - Following app.py pattern
DEPLOYMENT_INFO = {
    "base_url": get_base_url(),
    "api_endpoint": f"{get_base_url()}/api/predict",
    "environment": "Katonic Platform" if os.getenv("DEPLOYMENT_URL") else "Local",
    "port": os.getenv("PORT", "8050"),
    "request_count": 0,
    "startup_time": datetime.now().isoformat(),
    "version": "1.0.0-sales-script-generator"
}

# Pydantic models for request/response
class SalesScriptRequest(BaseModel):
    product_name: str
    target_audience: str
    key_benefits: List[str]
    tone: str = "professional"  # professional, casual, enthusiastic
    script_type: str = "cold_call"  # cold_call, presentation
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "AI Analytics Platform",
                "target_audience": "Small business owners",
                "key_benefits": ["Saves time", "Increases revenue", "Easy to use"],
                "tone": "professional",
                "script_type": "cold_call"
            }
        }

class GradioRequest(BaseModel):
    data: List[Union[str, None]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": ["AI Analytics Platform", "Small business owners", "professional"]
            }
        }

class SalesScriptResponse(BaseModel):
    success: bool
    script: str
    script_type: str
    word_count: int
    estimated_duration: str
    tips: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "script": "Hello, this is [Your Name] from...",
                "script_type": "cold_call",
                "word_count": 150,
                "estimated_duration": "1-2 minutes",
                "tips": ["Speak clearly", "Pause for responses"]
            }
        }

class GradioResponse(BaseModel):
    data: List[str]
    is_generating: bool = False
    duration: float = 0.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": ["{\n  \"success\": true,\n  \"script\": \"Hello, this is...\"\n}"],
                "is_generating": False,
                "duration": 1.2
            }
        }

# FIXED: FastAPI app initialization - Following app.py pattern
app = FastAPI(
    title="Sales Script Generator API",
    description="""
    ## Sales Script Generator with FastAPI
    
    ### Features:
    - **Cold Call Scripts**: Generate effective cold calling scripts
    - **Presentation Scripts**: Create engaging presentation content
    - **Customizable Tone**: Professional, casual, or enthusiastic
    - **Target Audience**: Tailored messaging for specific audiences
    
    ### Available Endpoints:
    - **Sales Script API**: Generate customized sales scripts
    - **Quick Script API**: Simplified script generation (Gradio format)
    - **Health Check**: System status monitoring
    
    ### Try the APIs below!
    """,
    version=DEPLOYMENT_INFO["version"],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path=root_path.rstrip('/') if root_path != '/' else '',
    contact={
        "name": "Katonic AI Support",
        "url": "https://katonic.ai",
        "email": "support@katonic.ai",
    },
    license_info={
        "name": "Katonic AI License",
        "url": "https://katonic.ai/license",
    },
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
def generate_sales_script(product_name: str, target_audience: str, key_benefits: List[str], 
                         tone: str = "professional", script_type: str = "cold_call") -> dict:
    """Generate a sales script based on input parameters"""
    
    # Script templates
    cold_call_template = {
        "professional": """
Hello, this is [Your Name] from [Company]. I hope I'm not catching you at a bad time.

I'm reaching out to {target_audience} because I know you're always looking for ways to {primary_benefit}.

We've developed {product_name} that specifically helps businesses like yours achieve:
{benefits_list}

I'd love to show you how {product_name} has helped similar companies in your industry. 

Would you have 15 minutes this week for a quick demonstration? I promise it will be worth your time.

What would work better for you - Tuesday afternoon or Thursday morning?
""",
        "casual": """
Hi there! This is [Your Name] from [Company]. 

Quick question - are you still dealing with [common problem] in your business?

I've got something that might interest you. It's called {product_name}, and it's designed specifically for {target_audience}.

Here's what makes it special:
{benefits_list}

Look, I know you're busy, so how about this - give me just 10 minutes to show you how this works, and if you don't see the value, no worries at all.

When would be a good time to chat briefly?
""",
        "enthusiastic": """
Hello! This is [Your Name] from [Company], and I have some exciting news for {target_audience}!

We've just launched {product_name}, and the results our clients are seeing are incredible:
{benefits_list}

I'm so confident this will transform your business that I want to offer you a personal demonstration at no cost.

This is a game-changer, and I'd hate for you to miss out on getting ahead of your competition.

Can we schedule 20 minutes this week? Trust me, this will be the best 20 minutes you'll invest in your business this month!

What day works best for you?
"""
    }
    
    presentation_template = {
        "professional": """
Good [morning/afternoon], everyone. Thank you for taking the time to learn about {product_name}.

Today, I'm here to show you how {product_name} can specifically benefit {target_audience}.

Let me start with a question: How many of you have experienced [common pain point]?

[Pause for responses]

That's exactly why we created {product_name}. Our solution addresses these challenges by providing:
{benefits_list}

Over the next [X] minutes, I'll show you exactly how this works and share some real results from companies just like yours.

By the end of this presentation, you'll understand:
- How {product_name} solves your specific challenges
- The measurable impact you can expect
- How to get started immediately

Let's begin with a quick demonstration...
""",
        "casual": """
Hey everyone! Thanks for being here today.

So, let me guess - you're probably thinking "another product demo, right?" 

Well, {product_name} is different, and I think you'll see why.

We built this specifically for {target_audience} because we kept hearing the same frustrations over and over.

Here's what {product_name} actually does:
{benefits_list}

Instead of just talking about it, let me show you. I'm going to walk through a real example that I think you'll find pretty interesting.

Ready? Let's dive in...
""",
        "enthusiastic": """
Welcome everyone! I am SO excited to share {product_name} with you today!

This is honestly one of the most innovative solutions I've seen for {target_audience}, and I can't wait to show you why.

Before we start, let me ask - who here is ready to revolutionize the way you [core function]?

[Pause for energy]

Perfect! Because {product_name} is going to blow your minds with:
{benefits_list}

I've got some incredible success stories to share, and by the time we're done, you're going to want to get started immediately.

This is going to be amazing - let's jump right in!
"""
    }
    
    # Select template
    templates = cold_call_template if script_type == "cold_call" else presentation_template
    template = templates.get(tone, templates["professional"])
    
    # Format benefits list
    benefits_list = "\n".join([f"• {benefit}" for benefit in key_benefits])
    primary_benefit = key_benefits[0] if key_benefits else "improve your business"
    
    # Generate script
    script = template.format(
        product_name=product_name,
        target_audience=target_audience,
        benefits_list=benefits_list,
        primary_benefit=primary_benefit
    ).strip()
    
    # Count words and estimate duration
    word_count = len(script.split())
    estimated_minutes = max(1, word_count // 150)  # ~150 words per minute speaking
    duration = f"{estimated_minutes}-{estimated_minutes + 1} minutes"
    
    # Generate tips based on script type and tone
    tips = []
    if script_type == "cold_call":
        tips = [
            "Speak clearly and at a moderate pace",
            "Pause after questions to allow responses",
            "Be prepared for objections",
            "Have your calendar ready for scheduling",
            "Practice saying the product name confidently"
        ]
    else:  # presentation
        tips = [
            "Make eye contact with your audience",
            "Use gestures to emphasize key points",
            "Pause for questions at natural breaks",
            "Have backup slides ready",
            "End with a clear call to action"
        ]
    
    if tone == "enthusiastic":
        tips.append("Let your genuine excitement show through")
    elif tone == "casual":
        tips.append("Keep the conversation natural and relaxed")
    else:
        tips.append("Maintain professional demeanor throughout")
    
    return {
        "success": True,
        "script": script,
        "script_type": script_type,
        "word_count": word_count,
        "estimated_duration": duration,
        "tips": tips[:5]  # Limit to 5 tips
    }

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "title": "Sales Script Generator API",
        "description": "Generate customized sales scripts for cold calls and presentations",
        "version": DEPLOYMENT_INFO["version"],
        "framework": "FastAPI",
        "endpoints": {
            "Interactive Docs": "/docs",
            "Alternative Docs": "/redoc",
            "Sales Script API": "/api/sales-script",
            "Quick Script API": "/api/quick-script/predict",
            "Health Check": "/health"
        },
        "example_usage": {
            "sales_script": {
                "method": "POST",
                "url": "/api/sales-script",
                "body": {
                    "product_name": "AI Analytics Platform",
                    "target_audience": "Small business owners", 
                    "key_benefits": ["Saves time", "Increases revenue"],
                    "tone": "professional",
                    "script_type": "cold_call"
                }
            },
            "quick_script": {
                "method": "POST",
                "url": "/api/quick-script/predict",
                "body": {"data": ["AI Platform", "Small businesses", "professional"]}
            }
        },
        "deployment_info": DEPLOYMENT_INFO
    }

# Main Sales Script Generator endpoint
@app.post("/api/sales-script", response_model=SalesScriptResponse, 
          summary="Generate Sales Script", 
          description="Generate a customized sales script with full configuration options")
async def generate_script(request: Request, script_request: SalesScriptRequest):
    """
    Generate a customized sales script based on detailed parameters
    """
    start_time = time.time()
    request_id = str(time.time()).replace('.', '')[-8:]
    DEPLOYMENT_INFO["request_count"] += 1
    
    try:
        logger.info(f"[{request_id}] Generating {script_request.script_type} script for {script_request.product_name}")
        
        # Generate the script
        result = generate_sales_script(
            product_name=script_request.product_name,
            target_audience=script_request.target_audience,
            key_benefits=script_request.key_benefits,
            tone=script_request.tone,
            script_type=script_request.script_type
        )
        
        processing_time = time.time() - start_time
        logger.info(f"[{request_id}] Script generated successfully in {processing_time:.2f}s")
        
        # Add metadata
        result.update({
            "processing_time": processing_time,
            "request_id": request_id,
            "total_requests": DEPLOYMENT_INFO["request_count"]
        })
        
        return SalesScriptResponse(**result)
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"[{request_id}] Error generating script: {e}")
        
        error_response = SalesScriptResponse(
            success=False,
            script=f"Error generating script: {str(e)}",
            script_type=script_request.script_type,
            word_count=0,
            estimated_duration="0 minutes",
            tips=["Please try again with valid parameters"]
        )
        return error_response

# Quick Script Generator (Gradio-compatible format)
@app.post("/api/quick-script/predict", response_model=GradioResponse,
          summary="Quick Script Generator", 
          description="Simplified script generation using Gradio-compatible format")
async def quick_script(request: Request, gradio_request: GradioRequest):
    """
    Quick script generator - Gradio-compatible format
    Expected data format: [product_name, target_audience, tone]
    """
    start_time = time.time()
    request_id = str(time.time()).replace('.', '')[-8:]
    DEPLOYMENT_INFO["request_count"] += 1
    
    try:
        # Extract parameters from Gradio format
        product_name = gradio_request.data[0] if len(gradio_request.data) > 0 else "Your Product"
        target_audience = gradio_request.data[1] if len(gradio_request.data) > 1 else "business owners"
        tone = gradio_request.data[2] if len(gradio_request.data) > 2 else "professional"
        
        # Default benefits if not provided
        default_benefits = ["Saves time", "Increases efficiency", "Reduces costs"]
        
        logger.info(f"[{request_id}] Quick script generation: {product_name} for {target_audience}")
        
        # Validate inputs
        if not product_name or product_name.strip() == "":
            response = {
                "success": False,
                "error": "Product name is required",
                "script": "Please provide a product name to generate a script."
            }
        else:
            # Generate script
            result = generate_sales_script(
                product_name=product_name.strip(),
                target_audience=target_audience.strip(),
                key_benefits=default_benefits,
                tone=tone.lower(),
                script_type="cold_call"
            )
            
            response = result
        
        processing_time = time.time() - start_time
        response.update({
            "processing_time": processing_time,
            "request_id": request_id,
            "total_requests": DEPLOYMENT_INFO["request_count"]
        })
        
        logger.info(f"[{request_id}] Quick script generated successfully")
        
        # Return in Gradio format
        return GradioResponse(
            data=[json.dumps(response, indent=2)],
            duration=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"[{request_id}] Error in quick script generation: {e}")
        
        error_response = {
            "success": False,
            "error": str(e),
            "script": "An error occurred while generating the script. Please try again.",
            "processing_time": processing_time,
            "request_id": request_id
        }
        
        return GradioResponse(
            data=[json.dumps(error_response, indent=2)],
            duration=processing_time
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """FastAPI startup event"""
    logger.info("=" * 80)
    logger.info("Sales Script Generator API - FastAPI")
    logger.info("=" * 80)
    logger.info(f"Environment: {DEPLOYMENT_INFO['environment']}")
    logger.info(f"API Endpoint: {DEPLOYMENT_INFO['api_endpoint']}")
    logger.info(f"Base URL: {DEPLOYMENT_INFO['base_url']}")
    logger.info(f"Port: {DEPLOYMENT_INFO['port']}")
    logger.info(f"Version: {DEPLOYMENT_INFO['version']}")
    logger.info("=" * 80)
    logger.info("Available Endpoints:")
    logger.info(f"Sales Script:     POST {DEPLOYMENT_INFO['base_url']}/api/sales-script")
    logger.info(f"Quick Script:     POST {DEPLOYMENT_INFO['base_url']}/api/quick-script/predict")
    logger.info(f"Health Check:     GET  {DEPLOYMENT_INFO['base_url']}/health")
    logger.info(f"Interactive Docs: GET  {DEPLOYMENT_INFO['base_url']}/docs")
    logger.info("=" * 80)

# Main entry point
if __name__ == "__main__":
    logger.info("Starting Sales Script Generator API...")
    
    port = int(os.getenv('PORT', DEPLOYMENT_INFO['port']))
    logger.info(f"Server will run on: http://localhost:{port}{root_path}")
    logger.info(f"Interactive docs: http://localhost:{port}{root_path}/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True,
        log_level="info"
    )
