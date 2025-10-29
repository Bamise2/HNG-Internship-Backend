import httpx
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

COUNTRIES_API_URL = os.getenv("COUNTRIES_API_URL")
EXCHANGE_RATE_API_URL = os.getenv("EXCHANGE_RATE_API_URL")

async def fetch_countries() -> List[Dict]:
    """Fetch all countries from REST Countries API"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(COUNTRIES_API_URL)
            response.raise_for_status()
            data = response.json()
            return data
    except httpx.TimeoutException:
        raise Exception("Could not fetch data from REST Countries API: Request timed out")
    except httpx.HTTPStatusError as e:
        raise Exception(f"Could not fetch data from REST Countries API: HTTP {e.response.status_code}")
    except httpx.HTTPError as e:
        raise Exception(f"Could not fetch data from REST Countries API: {str(e)}")
    except Exception as e:
        raise Exception(f"Could not fetch data from REST Countries API: {str(e)}")

async def fetch_exchange_rates() -> Dict[str, float]:
    """Fetch exchange rates from Exchange Rate API"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(EXCHANGE_RATE_API_URL)
            response.raise_for_status()
            data = response.json()
            return data.get('rates', {})
    except httpx.TimeoutException:
        raise Exception("Could not fetch data from Exchange Rate API: Request timed out")
    except httpx.HTTPStatusError as e:
        raise Exception(f"Could not fetch data from Exchange Rate API: HTTP {e.response.status_code}")
    except httpx.HTTPError as e:
        raise Exception(f"Could not fetch data from Exchange Rate API: {str(e)}")
    except Exception as e:
        raise Exception(f"Could not fetch data from Exchange Rate API: {str(e)}")

def extract_currency_code(currencies: List[Dict]) -> Optional[str]:
    """Extract first currency code from currencies array"""
    if not currencies or len(currencies) == 0:
        return None
    
    first_currency = currencies[0]
    return first_currency.get('code')

def process_country_data(country: Dict, exchange_rates: Dict[str, float]) -> Dict:
    """Process and transform country data"""
    # Extract currency code
    currencies = country.get('currencies', [])
    currency_code = extract_currency_code(currencies)
    
    # Get exchange rate
    exchange_rate = None
    estimated_gdp = None
    
    if currency_code:
        exchange_rate = exchange_rates.get(currency_code)
        
        if exchange_rate:
            # Calculate estimated GDP
            from app.crud.country import calculate_estimated_gdp
            population = country.get('population', 0)
            estimated_gdp = calculate_estimated_gdp(population, exchange_rate)
        else:
            # Currency not found in exchange rates
            exchange_rate = None
            estimated_gdp = None
    else:
        # No currency
        estimated_gdp = 0.0
    
    return {
        'name': country.get('name'),
        'capital': country.get('capital'),
        'region': country.get('region'),
        'population': country.get('population', 0),
        'currency_code': currency_code,
        'exchange_rate': exchange_rate,
        'estimated_gdp': estimated_gdp,
        'flag_url': country.get('flag')
    }