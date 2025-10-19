from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime, timezone
import logging
import os
from dotenv import load_dotenv

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables only for local development
if os.path.exists('.env'):
    load_dotenv()
    logger.info("Loading from .env file (local development)")
else:
    logger.info("Loading from environment (production)")

app = FastAPI(
    title="HNG Backend Stage 0",
    description="Profile endpoint with dynamic cat facts",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CAT_FACTS_API = "https://catfact.ninja/fact"
API_TIMEOUT = 5.0

USER_EMAIL = os.environ.get("USER_EMAIL", "your.email@example.com")
USER_NAME = os.environ.get("USER_NAME", "Your Full Name")
USER_STACK = os.environ.get("USER_STACK", "Python/FastAPI")

logger.info(f"Environment variables loaded - Email: {USER_EMAIL}, Name: {USER_NAME}")


async def fetch_cat_fact() -> str:
    """ 
    Fetch a random cat fact from the Cat Facts API.
    Returns a fallback message if the API fails.
    """
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(CAT_FACTS_API)
            response.raise_for_status()
            data = response.json()
            return data.get("fact", "Cats are amazing creatures!")
    except httpx.TimeoutException:
        logger.error("Cat Facts API request timed out")
        return "Cats are known for their independent nature and have been domesticated for thousands of years."
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching cat fact: {e}")
        return "Cats have over 20 different vocalizations, including the purr, meow, and hiss."
    except Exception as e:
        logger.error(f"Unexpected error fetching cat fact: {e}")
        return "Cats spend 70% of their lives sleeping, which is about 13-16 hours a day."


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to HNG Backend Stage 0 API",
        "endpoints": {
            "/me": "Get profile information with a random cat fact",
            "/docs": "API documentation"
        }
    }


@app.get("/me")
async def get_profile():
    """
    GET endpoint that returns profile information with a dynamic cat fact.
    
    Returns:
        JSON response with status, user info, timestamp, and cat fact
    """
    try:
        # Get current UTC timestamp in ISO 8601 format
        current_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Fetch cat fact dynamically
        cat_fact = await fetch_cat_fact()
        
        # Build response
        response_data = {
            "status": "success",
            "user": {
                "email": USER_EMAIL,
                "name": USER_NAME,
                "stack": USER_STACK
            },
            "timestamp": current_timestamp,
            "fact": cat_fact
        }
        
        logger.info(f"Profile request successful at {current_timestamp}")
        
        return JSONResponse(
            content=response_data,
            status_code=200,
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in /me endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)