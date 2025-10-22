from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class StringAnalysis(Base):
    __tablename__ = "string_analyses"

    id = Column(String, primary_key=True, index=True)  # SHA-256 hash
    value = Column(String, unique=True, nullable=False, index=True)
    length = Column(Integer, nullable=False)
    is_palindrome = Column(Boolean, nullable=False)
    unique_characters = Column(Integer, nullable=False)
    word_count = Column(Integer, nullable=False)
    sha256_hash = Column(String, nullable=False)
    character_frequency_map = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())