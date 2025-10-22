from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db, engine, Base
from app import crud, schemas
from app.utils import parse_natural_language_query

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="String Analyzer Service",
    description="HNG Backend Stage 1 - Analyze and store string properties",
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "String Analyzer Service",
        "version": "1.0.0",
        "endpoints": {
            "POST /strings": "Analyze and store a string",
            "GET /strings/{string_value}": "Get specific string analysis",
            "GET /strings": "Get all strings with optional filters",
            "GET /strings/filter-by-natural-language": "Filter using natural language",
            "DELETE /strings/{string_value}": "Delete a string"
        }
    }

@app.post("/strings", response_model=schemas.StringResponse, status_code=status.HTTP_201_CREATED)
async def create_string(
    string_data: schemas.StringCreate,
    db: Session = Depends(get_db)
):
    """
    Analyze and store a string.
    Returns 409 if string already exists.
    """
    # Validate that value is actually a string
    if not isinstance(string_data.value, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Value must be a string"
        )
    
    # Check if string already exists
    existing = crud.get_string_by_value(db, string_data.value)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="String already exists in the system"
        )
    
    # Create new analysis
    try:
        db_string = crud.create_string_analysis(db, string_data.value)
        
        # Format response
        return schemas.StringResponse(
            id=db_string.id,
            value=db_string.value,
            properties=schemas.StringProperties(
                length=db_string.length,
                is_palindrome=db_string.is_palindrome,
                unique_characters=db_string.unique_characters,
                word_count=db_string.word_count,
                sha256_hash=db_string.sha256_hash,
                character_frequency_map=db_string.character_frequency_map
            ),
            created_at=db_string.created_at
        )
    except Exception as e:
        logger.error(f"Error creating string analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body or missing 'value' field"
        )

@app.get("/strings/{string_value}", response_model=schemas.StringResponse)
async def get_string(
    string_value: str,
    db: Session = Depends(get_db)
):
    """
    Get analysis for a specific string.
    Returns 404 if string doesn't exist.
    """
    db_string = crud.get_string_by_value(db, string_value)
    if not db_string:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="String does not exist in the system"
        )
    
    return schemas.StringResponse(
        id=db_string.id,
        value=db_string.value,
        properties=schemas.StringProperties(
            length=db_string.length,
            is_palindrome=db_string.is_palindrome,
            unique_characters=db_string.unique_characters,
            word_count=db_string.word_count,
            sha256_hash=db_string.sha256_hash,
            character_frequency_map=db_string.character_frequency_map
        ),
        created_at=db_string.created_at
    )

@app.get("/strings", response_model=schemas.StringListResponse)
async def get_all_strings(
    is_palindrome: Optional[bool] = Query(None),
    min_length: Optional[int] = Query(None, ge=0),
    max_length: Optional[int] = Query(None, ge=0),
    word_count: Optional[int] = Query(None, ge=0),
    contains_character: Optional[str] = Query(None, min_length=1, max_length=1),
    db: Session = Depends(get_db)
):
    """
    Get all strings with optional filtering.
    """
    try:
        strings = crud.get_all_strings(
            db=db,
            is_palindrome=is_palindrome,
            min_length=min_length,
            max_length=max_length,
            word_count=word_count,
            contains_character=contains_character
        )
        
        # Build filters_applied dict
        filters_applied = {}
        if is_palindrome is not None:
            filters_applied["is_palindrome"] = is_palindrome
        if min_length is not None:
            filters_applied["min_length"] = min_length
        if max_length is not None:
            filters_applied["max_length"] = max_length
        if word_count is not None:
            filters_applied["word_count"] = word_count
        if contains_character is not None:
            filters_applied["contains_character"] = contains_character
        
        # Format response
        data = [
            schemas.StringResponse(
                id=s.id,
                value=s.value,
                properties=schemas.StringProperties(
                    length=s.length,
                    is_palindrome=s.is_palindrome,
                    unique_characters=s.unique_characters,
                    word_count=s.word_count,
                    sha256_hash=s.sha256_hash,
                    character_frequency_map=s.character_frequency_map
                ),
                created_at=s.created_at
            )
            for s in strings
        ]
        
        return schemas.StringListResponse(
            data=data,
            count=len(data),
            filters_applied=filters_applied if filters_applied else None
        )
    except Exception as e:
        logger.error(f"Error filtering strings: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid query parameter values or types"
        )

@app.get("/strings/filter-by-natural-language", response_model=schemas.NaturalLanguageResponse)
async def filter_by_natural_language(
    query: str = Query(..., description="Natural language query"),
    db: Session = Depends(get_db)
):
    """
    Filter strings using natural language queries.
    Example: "all single word palindromic strings"
    """
    try:
        # Parse the natural language query
        filters = parse_natural_language_query(query)
        
        if not filters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to parse natural language query"
            )
        
        # Apply filters
        strings = crud.get_all_strings(
            db=db,
            is_palindrome=filters.get("is_palindrome"),
            min_length=filters.get("min_length"),
            max_length=filters.get("max_length"),
            word_count=filters.get("word_count"),
            contains_character=filters.get("contains_character")
        )
        
        # Format response
        data = [
            schemas.StringResponse(
                id=s.id,
                value=s.value,
                properties=schemas.StringProperties(
                    length=s.length,
                    is_palindrome=s.is_palindrome,
                    unique_characters=s.unique_characters,
                    word_count=s.word_count,
                    sha256_hash=s.sha256_hash,
                    character_frequency_map=s.character_frequency_map
                ),
                created_at=s.created_at
            )
            for s in strings
        ]
        
        return schemas.NaturalLanguageResponse(
            data=data,
            count=len(data),
            interpreted_query={
                "original": query,
                "parsed_filters": filters
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing natural language query: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query parsed but resulted in conflicting filters"
        )

@app.delete("/strings/{string_value}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_string(
    string_value: str,
    db: Session = Depends(get_db)
):
    """
    Delete a string from the system.
    Returns 404 if string doesn't exist.
    """
    success = crud.delete_string(db, string_value)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="String does not exist in the system"
        )
    return None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}