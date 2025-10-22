from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime

class StringCreate(BaseModel):
    value: str = Field(..., description="String to analyze")

class StringProperties(BaseModel):
    length: int
    is_palindrome: bool
    unique_characters: int
    word_count: int
    sha256_hash: str
    character_frequency_map: Dict[str, int]

class StringResponse(BaseModel):
    id: str
    value: str
    properties: StringProperties
    created_at: datetime

    class Config:
        from_attributes = True

class StringListResponse(BaseModel):
    data: List[StringResponse]
    count: int
    filters_applied: Optional[Dict] = None

class NaturalLanguageResponse(BaseModel):
    data: List[StringResponse]
    count: int
    interpreted_query: Dict