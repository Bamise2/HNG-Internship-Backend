from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from app.models.country import Country, RefreshMetadata
from typing import List, Optional
import random

def get_country_by_name(db: Session, name: str) -> Optional[Country]:
    """Get country by name (case-insensitive)"""
    return db.query(Country).filter(func.lower(Country.name) == name.lower()).first()

def get_countries(
    db: Session,
    region: Optional[str] = None,
    currency: Optional[str] = None,
    sort: Optional[str] = None
) -> List[Country]:
    """Get all countries with optional filtering and sorting"""
    query = db.query(Country)
    
    if region:
        query = query.filter(func.lower(Country.region) == region.lower())
    
    if currency:
        query = query.filter(func.lower(Country.currency_code) == currency.upper())
    
    if sort:
        if sort == "gdp_desc":
            query = query.order_by(desc(Country.estimated_gdp))
        elif sort == "gdp_asc":
            query = query.order_by(asc(Country.estimated_gdp))
        elif sort == "population_desc":
            query = query.order_by(desc(Country.population))
        elif sort == "population_asc":
            query = query.order_by(asc(Country.population))
        elif sort == "name_asc":
            query = query.order_by(asc(Country.name))
        elif sort == "name_desc":
            query = query.order_by(desc(Country.name))
    
    return query.all()

def create_or_update_country(db: Session, country_data: dict) -> Country:
    """Create new country or update existing one"""
    existing = get_country_by_name(db, country_data['name'])
    
    if existing:
        # Update existing
        for key, value in country_data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        country = Country(**country_data)
        db.add(country)
        db.commit()
        db.refresh(country)
        return country

def delete_country(db: Session, name: str) -> bool:
    """Delete country by name"""
    country = get_country_by_name(db, name)
    if country:
        db.delete(country)
        db.commit()
        return True
    return False

def get_or_create_metadata(db: Session) -> RefreshMetadata:
    """Get or create refresh metadata"""
    metadata = db.query(RefreshMetadata).first()
    if not metadata:
        metadata = RefreshMetadata(total_countries=0)
        db.add(metadata)
        db.commit()
        db.refresh(metadata)
    return metadata

def update_metadata(db: Session, total_countries: int):
    """Update refresh metadata"""
    metadata = get_or_create_metadata(db)
    metadata.total_countries = total_countries
    db.commit()
    db.refresh(metadata)
    return metadata

def calculate_estimated_gdp(population: int, exchange_rate: float) -> float:
    """Calculate estimated GDP"""
    random_multiplier = random.uniform(1000, 2000)
    return (population * random_multiplier) / exchange_rate

def get_top_countries_by_gdp(db: Session, limit: int = 5) -> List[Country]:
    """Get top countries by estimated GDP"""
    return db.query(Country).filter(
        Country.estimated_gdp.isnot(None)
    ).order_by(desc(Country.estimated_gdp)).limit(limit).all()