# HNG Backend Stage 0 - Profile API

A RESTful API endpoint that returns profile information along with dynamic cat facts fetched from an external API.

## Features

- **Dynamic Profile Endpoint**: Returns user information with real-time data
- **Cat Facts Integration**: Fetches random cat facts from Cat Facts API
- **Error Handling**: Graceful fallback when external API fails
- **ISO 8601 Timestamps**: UTC time in standard format
- **CORS Enabled**: Cross-origin requests supported
- **Health Check**: Monitoring endpoint for deployment

##  Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- httpx
- python-dotenv

##  Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Bamise2/HNG-Internship-Backend.git
cd stage0
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
USER_EMAIL=your.email@example.com
USER_NAME=Your Full Name
USER_STACK=Python/FastAPI
PORT=8000
```

### 5. Run the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Or run directly
python main.py
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### GET /me

Returns profile information with a dynamic cat fact.

**Response Format:**

```json
{
  "status": "success",
  "user": {
    "email": "your.email@example.com",
    "name": "Your Full Name",
    "stack": "Python/FastAPI"
  },
  "timestamp": "2025-10-19T12:34:56.789123+00:00",
  "fact": "Cats have over 20 different vocalizations."
}
```

**Status Codes:**
- `200 OK`: Successful response
- `500 Internal Server Error`: Server error

### GET /health

Health check endpoint for monitoring.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-10-19T12:34:56.789123+00:00"
}
```

### GET /

Root endpoint with API information.

## 🧪 Testing

### Test Locally

```bash
# Using curl
curl http://localhost:8000/me

# Using httpie
http GET http://localhost:8000/me

# Using Python requests
python -c "import requests; print(requests.get('http://localhost:8000/me').json())"
```

### Test in Browser

Open `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

## 🚢 Deployment

### Railway

1. Create a `railway.toml` file:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

2. Add environment variables in Railway dashboard
3. Deploy via GitHub integration

### Heroku

1. Create a `Procfile`:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. Create a `runtime.txt`:

```
python-3.11.0
```

3. Deploy:

```bash
heroku create your-app-name
git push heroku main
```

### AWS / Other Platforms

Refer to your platform's Python/FastAPI deployment documentation.

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| USER_EMAIL | Your email address | your.email@example.com |
| USER_NAME | Your full name | Your Full Name |
| USER_STACK | Your backend stack | Python/FastAPI |
| PORT | Server port | 8000 |

## 🏗️ Project Structure

```
hng-backend-stage0/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .gitignore          # Git ignore file
├── README.md           # Project documentation
├── Procfile            # Heroku deployment (optional)
└── railway.toml        # Railway deployment (optional)
```

## 🔧 Tech Stack

- **Framework**: FastAPI
- **Server**: Uvicorn
- **HTTP Client**: httpx
- **External API**: Cat Facts API (https://catfact.ninja/fact)

## 🛡️ Error Handling

The application includes comprehensive error handling:

- **API Timeout**: 5-second timeout with fallback cat fact
- **HTTP Errors**: Catches and logs HTTP errors with fallback
- **Network Issues**: Graceful degradation with default cat facts
- **Server Errors**: Returns appropriate 500 status with error message

## 📚 Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 👨‍💻 Author

Your Name - HNG Internship Backend Track

## 📄 License

This project is created for HNG Internship Stage 0 assessment.

## 🔗 Links

- [HNG Internship](https://hng.tech/internship)
- [HNG Premium](https://hng.tech/premium)
- [HNG Hire](https://hng.tech/hire)