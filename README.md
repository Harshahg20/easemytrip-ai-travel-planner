# Tripora - AI Travel Planner

Smart travel planning app using Google AI to generate personalized trip itineraries and recommendations

## 🌟 About

**Tripora** is a full-stack AI-powered travel planning platform built for the **EaseMyTrip Hackathon** under **Google's Gen AI Exchange**. It leverages Google's latest AI technologies to create personalized travel experiences.

### 🎯 Hackathon Requirements & Google Gemini AI Integration

**MANDATORY REQUIREMENT**: Tripora extensively uses **Google Gemini AI API** as required by the EaseMyTrip Hackathon under Google's Gen AI Exchange. The integration demonstrates the power of Google's latest AI technology in revolutionizing travel planning.

#### **Google Gemini AI Usage & Purpose**:

1. **Intelligent Trip Planning**:

   - Generates multiple personalized trip options (Adventure, Cultural, Balanced themes)
   - Creates detailed day-by-day itineraries with activities, meals, and accommodations
   - Provides context-aware recommendations based on user preferences

2. **Smart Content Generation**:

   - AI-powered activity suggestions with descriptions and timing
   - Restaurant recommendations with cuisine types and cost estimates
   - Accommodation suggestions with amenities and pricing
   - Transportation options with routes and duration

3. **Personalized Travel Assistant**:

   - Understands user preferences and travel themes
   - Adapts recommendations based on budget and traveler count
   - Provides local insights and travel tips
   - Generates comprehensive travel guides

4. **Hackathon Innovation**:
   - Showcases Google Gemini AI's capabilities in travel domain
   - Demonstrates real-world AI application for user benefit
   - Integrates multiple Google AI services for comprehensive solution
   - Provides scalable and intelligent travel planning experience

## 🚀 Features

- **AI-Powered Trip Planning**: Generate multiple personalized trip options using Google Gemini AI
- **Smart Itinerary Creation**: Detailed day-by-day schedules with activities, meals, and accommodations
- **Interactive Maps Integration**: Google Maps API for location services and route planning
- **Real-time Recommendations**: Dynamic suggestions based on user preferences and interests
- **Budget Management**: Comprehensive budget tracking and cost optimization
- **Multi-theme Support**: Adventure, cultural, and balanced travel experiences

## 🛠️ Tech Stack

### Frontend

- **React 19** with modern hooks and context
- **Tailwind CSS** for responsive design
- **Framer Motion** for smooth animations
- **React Router** for navigation
- **shadcn/ui** components for beautiful UI

### Backend

- **FastAPI** for high-performance API
- **SQLAlchemy** with MySQL 9.0 support
- **Google Gemini AI** (MANDATORY) for intelligent trip planning and content generation
- **Google Maps API** for location services and route planning
- **Pydantic** for data validation

### Database

- **MySQL 9.0** for production
- **SQLite** for development
- **Alembic** for database migrations

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- MySQL 9.0 (optional, SQLite works for development)

### 1. Clone the Repository

```bash
git clone https://github.com/Harshahg20/easemytrip-ai-travel-planner.git
cd easemytrip-ai-travel-planner
```

### 2. Setup Backend

```bash
cd backend
python3 setup.py
python3 init_mysql_db.py
python3 run.py
```

### 3. Setup Frontend

```bash
cd frontend
npm install
npm start
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🏆 Hackathon Details

- **Event**: EaseMyTrip Hackathon
- **Theme**: Google Gen AI Exchange
- **Focus**: AI-powered travel solutions using Google Gemini AI
- **Mandatory Requirement**: Google Gemini AI API integration
- **Technologies**: Google Gemini AI, Maps API, Modern Web Stack
- **Innovation**: Demonstrates real-world application of Google's latest AI technology

## 📁 Project Structure

```
tripora/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   ├── entities/       # Data models
│   │   └── utils/          # Utility functions
│   └── package.json
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Configuration and database
│   │   ├── models/        # Database models
│   │   └── services/      # External API integrations
│   ├── tests/             # Test files
│   └── requirements.txt
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite:///./trip_planner.db
# For MySQL: DATABASE_URL=mysql+pymysql://username:password@localhost:3306/trip_planner_db

# Google AI APIs (MANDATORY for hackathon)
GOOGLE_AI_API_KEY=your_google_ai_studio_api_key  # Required for Gemini AI integration
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Application
SECRET_KEY=your_secret_key
DEBUG=True
ENVIRONMENT=development
```

## 📚 API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

This project was built for the EaseMyTrip Hackathon. Feel free to explore the code and learn from the implementation.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Hackathon Compliance

Tripora fully complies with the EaseMyTrip Hackathon requirements:

✅ **Google Gemini AI Integration**: Extensively used for trip planning and content generation  
✅ **Real-world Application**: Demonstrates practical use of AI in travel industry  
✅ **Innovation**: Showcases cutting-edge AI capabilities for user benefit  
✅ **Technical Excellence**: Full-stack implementation with modern technologies  
✅ **User Experience**: Intuitive interface with AI-powered recommendations

## 🔗 Links

- **GitHub Repository**: https://github.com/Harshahg20/easemytrip-ai-travel-planner
- **Phase 1 Branch**: https://github.com/Harshahg20/easemytrip-ai-travel-planner/tree/phase1
- **EaseMyTrip**: https://www.easemytrip.com/
- **Google AI Studio**: https://aistudio.google.com/

---

**Tripora - Built with ❤️ for the EaseMyTrip Hackathon under Google Gen AI Exchange**
