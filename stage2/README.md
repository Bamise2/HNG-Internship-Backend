# Country Currency & Exchange API

RESTful API that fetches country data from external APIs, calculates exchange rates, and provides CRUD operations with MySQL persistence.

## 🎯 Features

- Fetch country data from REST Countries API
- Get real-time exchange rates
- Calculate estimated GDP for each country
- MySQL database persistence
- Filter and sort countries
- Generate summary images
- Full CRUD operations

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **MySQL** - Database
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **httpx** - Async HTTP client
- **Pillow** - Image generation

## 📁 Project Structure

```
country-currency-api/
├── app/
│   ├── api/
│   │   └── routes.py          # API endpoints
│   ├── crud/
│   │   └── country.py         # Database operations
│   ├── models/
│   │   └── country.py         # SQLAlchemy models
│   ├── schemas/
│   │   └── country.py         # Pydantic schemas
│   ├── services/
│   │   ├── external_api.py    # External API calls
│   │   └── image_generator.py # Image generation
│   ├── database.py            # Database config
│   └── main.py                # FastAPI app
├── cache/                     # Generated images
├── .env                       # Environment variables
├── requirements.txt
└── README.md
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip

### Step 1: Clone Repository

```bash
git clone <repo-url>
cd country-currency-api
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# Activate
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup MySQL Database

```sql
CREATE DATABASE country_api;
```

### Step 5: Configure Environment

Create `.env` file:

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/country_api
PORT=8000
COUNTRIES_API_URL=https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies
EXCHANGE_RATE_API_URL=https://open.er-api.com/v6/latest/USD
CACHE_DIR=cache
IMAGE_PATH=cache/summary.png
```

### Step 6: Run Application

```bash
uvicorn app.main:app --reload
```

Or:

```bash
python -m app.main
```

Access at: `http://localhost:8000`

API Docs: `http://localhost:8000/docs`

## 📡 API Endpoints

### 1. Refresh Countries

```http
POST /countries/refresh
```

Fetches all countries and exchange rates, caches in database, and generates summary image.

**Response:**
```json
{
  "message": "Countries refreshed successfully",
  "total_countries": 250,
  "last_refreshed_at": "2025-10-28T20:00:00Z"
}
```

### 2. Get All Countries

```http
GET /countries?region=Africa&currency=NGN&sort=gdp_desc
```

**Query Parameters:**
- `region` - Filter by region (e.g., Africa, Europe)
- `currency` - Filter by currency code (e.g., NGN, USD)
- `sort` - Sort results:
  - `gdp_desc` / `gdp_asc`
  - `population_desc` / `population_asc`
  - `name_asc` / `name_desc`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Nigeria",
    "capital": "Abuja",
    "region": "Africa",
    "population": 206139589,
    "currency_code": "NGN",
    "exchange_rate": 1600.23,
    "estimated_gdp": 25767448125.2,
    "flag_url": "https://flagcdn.com/ng.svg",
    "last_refreshed_at": "2025-10-28T20:00:00Z"
  }
]
```

### 3. Get Single Country

```http
GET /countries/Nigeria
```

**Response:** Same as array item above

### 4. Delete Country

```http
DELETE /countries/Nigeria
```

**Response:** 204 No Content

### 5. Get Status

```http
GET /status
```

**Response:**
```json
{
  "total_countries": 250,
  "last_refreshed_at": "2025-10-28T20:00:00Z"
}
```

### 6. Get Summary Image

```http
GET /countries/image
```

**Response:** PNG image file

## 🔄 Data Processing Logic

### Currency Handling

1. **Multiple Currencies**: Store only first currency code
2. **Empty Currencies**: 
   - `currency_code` = null
   - `exchange_rate` = null  
   - `estimated_gdp` = 0
3. **Currency Not Found**: 
   - `exchange_rate` = null
   - `estimated_gdp` = null

### Update vs Insert

- Match by name (case-insensitive)
- If exists: Update all fields + recalculate GDP
- If new: Insert record
- Random multiplier regenerated on each refresh

### GDP Calculation

```python
estimated_gdp = population × random(1000-2000) ÷ exchange_rate
```

## 🚨 Error Handling

### 400 Bad Request
```json
{
  "error": "Validation failed",
  "details": {
    "currency_code": "is required"
  }
}
```

### 404 Not Found
```json
{
  "error": "Country not found"
}
```

### 503 Service Unavailable
```json
{
  "error": "External data source unavailable",
  "details": "Could not fetch data from REST Countries API"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

## 🧪 Testing

### Test Endpoints with cURL

```bash
# Refresh data
curl -X POST http://localhost:8000/countries/refresh

# Get all countries
curl http://localhost:8000/countries

# Filter by region
curl "http://localhost:8000/countries?region=Africa"

# Get status
curl http://localhost:8000/status

# Get image
curl http://localhost:8000/countries/image --output summary.png
```

### Test with Python

```python
import requests

# Refresh
response = requests.post('http://localhost:8000/countries/refresh')
print(response.json())

# Get countries
response = requests.get('http://localhost:8000/countries?region=Africa&sort=gdp_desc')
print(response.json())
```

## 📊 Database Schema

### countries table

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT |
| name | VARCHAR(255) | NOT NULL, UNIQUE |
| capital | VARCHAR(255) | NULL |
| region | VARCHAR(255) | NULL |
| population | BIGINT | NOT NULL |
| currency_code | VARCHAR(10) | NULL |
| exchange_rate | FLOAT | NULL |
| estimated_gdp | FLOAT | NULL |
| flag_url | VARCHAR(500) | NULL |
| last_refreshed_at | DATETIME | AUTO_UPDATE |

### refresh_metadata table

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY |
| total_countries | INT | NOT NULL |
| last_refreshed_at | DATETIME | AUTO_UPDATE |

## 🎨 Image Generation

Summary image includes:
- Total countries count
- Top 5 countries by estimated GDP
- Last refresh timestamp

Generated automatically after `/countries/refresh`

## 🔐 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | MySQL connection string | mysql+pymysql://user:pass@host:port/db |
| PORT | Server port | 8000 |
| COUNTRIES_API_URL | Countries API endpoint | https://restcountries.com/... |
| EXCHANGE_RATE_API_URL | Exchange rate API endpoint | https://open.er-api.com/... |
| CACHE_DIR | Cache directory | cache |
| IMAGE_PATH | Summary image path | cache/summary.png |

## 🚀 Deployment

### Railway

1. Add MySQL plugin
2. Set environment variables
3. Deploy from GitHub

### Heroku

```bash
heroku create
heroku addons:create jawsdb:kitefin
git push heroku main
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🐛 Troubleshooting

### MySQL Connection Error

```bash
# Check MySQL is running
mysql --version
mysql -u root -p

# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('mysql+pymysql://root:password@localhost/country_api'); print('Connected!')"
```

### External API Timeout

- Check internet connection
- Verify API URLs are correct
- Increase timeout in `external_api.py`

## 📝 License

Created for HNG Internship - Educational purposes

## 👨‍💻 Author

Your Name - HNG Internship

---

**Built with FastAPI for HNG Internship** 🚀