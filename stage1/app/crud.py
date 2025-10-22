from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import StringAnalysis
from app.utils import analyze_string
from typing import List, Optional

def create_string_analysis(db: Session, value: str) -> StringAnalysis:
    """Create a new string analysis"""
    analysis_data = analyze_string(value)
    
    db_string = StringAnalysis(
        id=analysis_data["id"],
        value=analysis_data["value"],
        length=analysis_data["length"],
        is_palindrome=analysis_data["is_palindrome"],
        unique_characters=analysis_data["unique_characters"],
        word_count=analysis_data["word_count"],
        sha256_hash=analysis_data["sha256_hash"],
        character_frequency_map=analysis_data["character_frequency_map"]
    )
    
    db.add(db_string)
    db.commit()
    db.refresh(db_string)
    return db_string

def get_string_by_value(db: Session, value: str) -> Optional[StringAnalysis]:
    """Get string analysis by value"""
    return db.query(StringAnalysis).filter(StringAnalysis.value == value).first()

def get_string_by_id(db: Session, string_id: str) -> Optional[StringAnalysis]:
    """Get string analysis by ID (hash)"""
    return db.query(StringAnalysis).filter(StringAnalysis.id == string_id).first()

def get_all_strings(
    db: Session,
    is_palindrome: Optional[bool] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    word_count: Optional[int] = None,
    contains_character: Optional[str] = None
) -> List[StringAnalysis]:
    """Get all strings with optional filters"""
    query = db.query(StringAnalysis)
    
    filters = []
    
    if is_palindrome is not None:
        filters.append(StringAnalysis.is_palindrome == is_palindrome)
    
    if min_length is not None:
        filters.append(StringAnalysis.length >= min_length)
    
    if max_length is not None:
        filters.append(StringAnalysis.length <= max_length)
    
    if word_count is not None:
        filters.append(StringAnalysis.word_count == word_count)
    
    if contains_character is not None:
        # Check if character exists in value
        filters.append(StringAnalysis.value.contains(contains_character))
    
    if filters:
        query = query.filter(and_(*filters))
    
    return query.all()

def delete_string(db: Session, value: str) -> bool:
    """Delete string analysis by value"""
    db_string = get_string_by_value(db, value)
    if db_string:
        db.delete(db_string)
        db.commit()
        return True
    return False