from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging

from app.database import get_db
from app.schemas.country import CountryResponse, StatusResponse, RefreshResponse
from app.crud import country as crud
from app.services.external_api import fetch_countries, fetch_exchange_rates, process_country_data
from app.services.image_generator import generate_summary_image

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/countries/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh_countries(db: Session = Depends(get_db)):
    """
    Fetch all countries and exchange rates, then cache them in the database.
    Also generates a summary image.
    """
    # Debug logs
    print("DEBUG: refresh_countries() started")
    print("DEBUG: COUNTRIES_API_URL =", os.getenv("COUNTRIES_API_URL"))
    print("DEBUG: EXCHANGE_RATE_API_URL =", os.getenv("EXCHANGE_RATE_API_URL"))

    try:
        logger.info("Starting countries refresh...")

        # Fetch data from external APIs
        logger.info("Fetching country data...")
        print("DEBUG: Fetching countries data...")
        countries_data = await fetch_countries()
        print(f"DEBUG: Fetched {len(countries_data)} countries")

        logger.info("Fetching exchange rates...")
        print("DEBUG: Fetching exchange rates...")
        exchange_rates = await fetch_exchange_rates()
        print(f"DEBUG: Fetched {len(exchange_rates)} exchange rates")

        # Process and store countries
        print("DEBUG: Processing countries...")
        processed_count = 0
        for country in countries_data:
            try:
                country_info = process_country_data(country, exchange_rates)
                crud.create_or_update_country(db, country_info)
                processed_count += 1
            except Exception as e:
                print(f"DEBUG: Error processing country {country.get('name')}: {e}")
                continue

        print("DEBUG: Updating metadata...")
        metadata = crud.update_metadata(db, processed_count)
        db.commit()

        print("DEBUG: Generating image...")
        top_countries = crud.get_top_countries_by_gdp(db, limit=5)
        generate_summary_image(processed_count, top_countries, metadata.last_refreshed_at)

        print("DEBUG: Refresh completed successfully.")
        logger.info("Summary image generated successfully")

        return RefreshResponse(
            message="Countries refreshed successfully",
            total_countries=processed_count,
            last_refreshed_at=metadata.last_refreshed_at
        )

    except Exception as e:
        print("DEBUG: Exception occurred in refresh_countries:", str(e))
        logger.exception("Error during refresh_countries")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "External data source unavailable", "details": str(e)}
        )


@router.get("/countries", response_model=List[CountryResponse])
def get_countries(
    region: Optional[str] = Query(None, description="Filter by region (e.g., Africa)"),
    currency: Optional[str] = Query(None, description="Filter by currency code (e.g., NGN)"),
    sort: Optional[str] = Query(None, description="Sort results (gdp_desc, gdp_asc, population_desc, etc.)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all countries from the database with optional filters and sorting.
    """
    countries = crud.get_countries(db, region=region, currency=currency, sort=sort)
    return countries


@router.get("/countries/image")
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

    return FileResponse(
        image_path,
        media_type="image/png",
        headers={"Content-Disposition": "inline; filename=summary.png"}
    )


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


@router.get("/countries/{name}", response_model=CountryResponse)
def get_country(name: str, db: Session = Depends(get_db)):
    """
    Retrieve a single country by name.
    """
    country = crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Country '{name}' not found"}
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
            detail={"error": f"Country '{name}' not found"}
        )
    return None
