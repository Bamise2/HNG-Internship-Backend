from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, Text
from sqlalchemy.sql import func
from app.database import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    capital = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True, index=True)
    population = Column(BigInteger, nullable=False, default=0)
    currency_code = Column(String(10), nullable=True, index=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(Text, nullable=True)
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class RefreshMetadata(Base):
    __tablename__ = "refresh_metadata"

    id = Column(Integer, primary_key=True, index=True)
    total_countries = Column(Integer, nullable=False, default=0)
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())