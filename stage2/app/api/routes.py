from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database import get_db
from app.schemas.country import CountryResponse, StatusResponse, RefreshResponse, ErrorResponse
from app.crud import country as crud
from app.services.external_api import fetch_countries, fetch_exchange_rates, process_country_data
from app.services.image_generator import generate_summary_image

router = APIRouter()

@router.post("/countries/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh_countries(db: Session = Depends(get_db)):
    """
    Fetch all countries and exchange rates, then cache them in database.
    Also generates summary image.
    """
    try:
        # Fetch data from external APIs
        countries_data = await fetch_countries()
        exchange_rates = await fetch_exchange_rates()
        
        # Process and store each country
        processed_count = 0
        for country in countries_data:
            try:
                country_info = process_country_data(country, exchange_rates)
                crud.create_or_update_country(db, country_info)
                processed_count += 1
            except Exception as e:
                # Log error but continue processing other countries
                print(f"Error processing country {country.get('name')}: {str(e)}")
                continue
        
        # Update metadata
        metadata = crud.update_metadata(db, processed_count)
        
        # Generate summary image
        top_countries = crud.get_top_countries_by_gdp(db, limit=5)
        generate_summary_image(processed_count, top_countries, metadata.last_refreshed_at)
        
        return RefreshResponse(
            message="Countries refreshed successfully",
            total_countries=processed_count,
            last_refreshed_at=metadata.last_refreshed_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "External data source unavailable",
                "details": str(e)
            }
        )

@router.get("/countries", response_model=List[CountryResponse])
def get_countries(
    region: Optional[str] = Query(None, description="Filter by region (e.g., Africa)"),
    currency: Optional[str] = Query(None, description="Filter by currency code (e.g., NGN)"),
    sort: Optional[str] = Query(None, description="Sort results (gdp_desc, gdp_asc, population_desc, etc.)"),
    db: Session = Depends(get_db)
):
    """
    Get all countries from database with optional filters and sorting.
    """
    countries = crud.get_countries(db, region=region, currency=currency, sort=sort)
    return countries

@router.get("/countries/{name}", response_model=CountryResponse)
def get_country(name: str, db: Session = Depends(get_db)):
    """
    Get a single country by name.
    """
    country = crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Country not found"}
        )
    return country

@router.delete("/countries/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_country(name: str, db: Session = Depends(get_db)):
    """
    Delete a country record by name.
    """
    success = crud.delete_country(db, name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Country not found"}
        )
    return None

@router.get("/status", response_model=StatusResponse)
def get_status(db: Session = Depends(get_db)):
    """
    Show total countries and last refresh timestamp.
    """
    metadata = crud.get_or_create_metadata(db)
    return StatusResponse(
        total_countries=metadata.total_countries,
        last_refreshed_at=metadata.last_refreshed_at
    )

@router.get("/countries/image", response_class=FileResponse)
def get_summary_image():
    """
    Serve the generated summary image.
    """
    image_path = os.getenv("IMAGE_PATH", "cache/summary.png")
    
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Summary image not found"}
        )
    
    return FileResponse(image_path, media_type="image/png")