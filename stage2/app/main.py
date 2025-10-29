from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import logging
import os

from app.database import init_db
from app.api.routes import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Country Currency & Exchange API",
    description="RESTful API for fetching country data with currency exchange rates",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    
    # Create cache directory
    cache_dir = os.getenv("CACHE_DIR", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    logger.info(f"Cache directory created: {cache_dir}")

# Include routers
app.include_router(router, tags=["countries"])

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Country Currency & Exchange API",
        "version": "1.0.0",
        "endpoints": {
            "POST /countries/refresh": "Fetch and cache country data",
            "GET /countries": "Get all countries (with filters)",
            "GET /countries/{name}": "Get specific country",
            "DELETE /countries/{name}": "Delete country",
            "GET /status": "Get API status",
            "GET /countries/image": "Get summary image",
            "GET /docs": "API documentation"
        }
    }

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for error in exc.errors():
        field = error['loc'][-1]
        message = error['msg']
        errors[field] = message
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation failed",
            "details": errors
        }
    )

# Generic error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error"
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)