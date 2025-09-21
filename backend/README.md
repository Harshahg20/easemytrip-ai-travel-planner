# Trip Planner Backend API

A FastAPI-based backend for AI-powered travel planning using Google AI technologies.

## Features

- **AI-Powered Trip Planning**: Uses Google Gemini AI to generate personalized trip options
- **Google Maps Integration**: Provides location-based services and recommendations
- **RESTful API**: Clean and well-documented API endpoints
- **Database Integration**: SQLAlchemy with MySQL 9.0/SQLite support
- **Real-time Recommendations**: Dynamic travel suggestions based on user preferences

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM with MySQL 9.0 support
- **Google AI APIs**: Gemini AI for intelligent trip planning
- **Google Maps API**: Location services and place search
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server

## Google AI Technologies Used

### 1. Google Gemini AI (Free Tier)

- **API**: Google AI Studio API
- **Model**: Gemini 1.5 Flash
- **Usage**: Trip option generation, itinerary planning, travel recommendations
- **Free Tier**: 15 requests per minute, 1 million tokens per day

### 2. Google Maps API (Free Tier)

- **Places API**: Search for restaurants, hotels, attractions
- **Geocoding API**: Convert addresses to coordinates
- **Directions API**: Get travel routes and directions
- **Free Tier**: $200 credit per month

### 3. Google Cloud Services (Optional)

- **Firebase**: Real-time database (if needed)
- **BigQuery**: Analytics and data processing (if needed)

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   # Option 1: Use the setup script (recommended)
   python setup.py

   # Option 2: Manual setup
   cp env.example .env
   # Edit .env with your API keys
   ```

5. **Validate your configuration**

   ```bash
   python validate_env.py
   ```

6. **Initialize the database**

   ```bash
   python init_mysql_db.py
   ```

7. **Run the application**
   ```bash
   python run.py
   ```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=sqlite:///./trip_planner.db
# For MySQL 9.0: DATABASE_URL=mysql+pymysql://username:password@localhost:3306/trip_planner_db

# Google AI APIs
GOOGLE_AI_API_KEY=your_google_ai_studio_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GOOGLE_CLOUD_PROJECT_ID=your_google_cloud_project_id

# Application
SECRET_KEY=your_secret_key
DEBUG=True
ENVIRONMENT=development
```

## Database Setup

### MySQL 9.0 Setup

1. **Install MySQL 9.0**

   ```bash
   # On macOS with Homebrew
   brew install mysql

   # On Ubuntu/Debian
   sudo apt update
   sudo apt install mysql-server-9.0

   # On Windows
   # Download from https://dev.mysql.com/downloads/mysql/
   ```

2. **Create Database and User**

   ```sql
   -- Connect to MySQL as root
   mysql -u root -p

   -- Create database
   CREATE DATABASE trip_planner_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

   -- Create user (replace 'username' and 'password' with your values)
   CREATE USER 'username'@'localhost' IDENTIFIED BY 'password';

   -- Grant privileges
   GRANT ALL PRIVILEGES ON trip_planner_db.* TO 'username'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Update .env file**
   ```env
   DATABASE_URL=mysql+pymysql://username:password@localhost:3306/trip_planner_db
   ```

### SQLite (Development)

For development, you can use SQLite which requires no setup:

```env
DATABASE_URL=sqlite:///./trip_planner.db
```

## Getting Google AI API Keys

### 1. Google AI Studio API Key (Free)

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" in the left sidebar
4. Create a new API key
5. Copy the key to your `.env` file

### 2. Google Maps API Key (Free Tier)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Places API
   - Geocoding API
   - Directions API
4. Go to "Credentials" and create an API key
5. Restrict the key to your APIs
6. Copy the key to your `.env` file

## API Endpoints

### Trips

- `POST /api/v1/trips/` - Create a new trip
- `GET /api/v1/trips/{trip_id}` - Get trip details
- `PUT /api/v1/trips/{trip_id}` - Update trip
- `DELETE /api/v1/trips/{trip_id}` - Delete trip
- `GET /api/v1/trips/` - List all trips

### Trip Options

- `POST /api/v1/trips/{trip_id}/generate-options` - Generate AI trip options
- `GET /api/v1/trips/{trip_id}/options` - Get trip options
- `POST /api/v1/trips/{trip_id}/select-option/{option_id}` - Select an option

### Itinerary

- `GET /api/v1/trips/{trip_id}/itinerary` - Get daily itinerary

### Recommendations

- `POST /api/v1/trips/{trip_id}/recommendations` - Get travel recommendations
- `POST /api/v1/trips/{trip_id}/places/search` - Search for places

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Example Usage

### Create a Trip

```bash
curl -X POST "http://localhost:8000/api/v1/trips/" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Rajasthan",
    "start_date": "2024-01-15T00:00:00",
    "end_date": "2024-01-20T00:00:00",
    "total_budget": 50000,
    "travelers": 2,
    "themes": ["cultural", "heritage"]
  }'
```

### Generate Trip Options

```bash
curl -X POST "http://localhost:8000/api/v1/trips/{trip_id}/generate-options" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Database Models

### Trip

- Basic trip information (destination, dates, budget, travelers)
- User preferences (accommodation, transportation, food)
- Status tracking (draft, planned, booked, completed)

### DailyItinerary

- Day-by-day itinerary details
- Activities, meals, accommodation, transport
- Budget allocation per day

### TripOption

- AI-generated trip options
- Different themes (adventure, cultural, balanced)
- Complete itinerary data

## Utility Scripts

### Setup Script

```bash
python setup.py
```

Automatically sets up the development environment, installs dependencies, and creates a `.env` file with a secure secret key.

### Environment Validation

```bash
python validate_env.py
```

Validates that all required environment variables are properly configured.

### Secret Key Generation

```bash
python generate_secret.py
```

Generates a secure secret key for your application.

### Database Initialization

```bash
python init_mysql_db.py
```

Initializes the database with all required tables. Works with both SQLite and MySQL.

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Linting

```bash
flake8
```

## Deployment

### Using Docker

```bash
docker build -t trip-planner-backend .
docker run -p 8000:8000 trip-planner-backend
```

### Using Railway/Heroku

1. Add `Procfile` with: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
2. Set environment variables in your deployment platform
3. Deploy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License
