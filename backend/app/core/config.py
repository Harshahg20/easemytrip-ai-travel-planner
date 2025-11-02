from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets


class Settings(BaseSettings):
    # Application
    app_name: str = "Trip Planner API"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Database - Can be provided directly or constructed from components
    database_url: Optional[str] = None
    
    # Security - Must be provided (from .env or secrets)
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Google AI APIs - Must be provided in .env file
    google_ai_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    google_cloud_project_id: str = "gen-ai-hackathon-476317"
    
    # Google Cloud ADK Settings
    google_cloud_region: str = "us-central1"
    google_application_credentials: str = "./gen-ai-hackathon-476317-71a0d1adef93.json"
    
    # ADK Agent Settings
    adk_agent_timeout: int = 30
    adk_max_conversation_history: int = 50
    adk_enable_subagents: bool = True
    
    # External API Keys for sub-agents
    openweather_api_key: str = ""
    amadeus_api_key: str = ""
    booking_api_key: str = ""
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001"
    
    @property
    def resolved_database_url(self) -> str:
        """Get database URL, constructing it from components if needed"""
        # If DATABASE_URL is explicitly set, use it
        if self.database_url:
            return self.database_url
        
        # Try to construct from Cloud Run environment variables
        db_user = os.getenv("DB_USER")
        db_name = os.getenv("DB_NAME")
        db_password = os.getenv("DB_PASSWORD")
        cloud_sql_conn = os.getenv("CLOUD_SQL_CONNECTION_NAME")
        
        if all([db_user, db_name, db_password, cloud_sql_conn]):
            return f"mysql+pymysql://{db_user}:{db_password}@/{db_name}?unix_socket=/cloudsql/{cloud_sql_conn}"
        
        # Fallback for development
        raise ValueError(
            "DATABASE_URL must be set, or provide DB_USER, DB_NAME, DB_PASSWORD, and CLOUD_SQL_CONNECTION_NAME environment variables"
        )
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Remove quotes from environment variables
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            if raw_val and raw_val.startswith('"') and raw_val.endswith('"'):
                return raw_val[1:-1]
            return raw_val


# Create settings instance with error handling
try:
    settings = Settings()
    # Validate that we can resolve database URL (but don't fail if DATABASE_URL not set yet)
    try:
        _ = settings.resolved_database_url
    except ValueError:
        # Will be checked when database.py tries to use it
        pass
except Exception as e:
    print("❌ Error loading configuration:")
    print(f"   {str(e)}")
    print("\n📝 Please ensure you have:")
    print("   - SECRET_KEY (required)")
    print("   - DATABASE_URL OR (DB_USER, DB_NAME, DB_PASSWORD, CLOUD_SQL_CONNECTION_NAME)")
    print("   - GOOGLE_AI_API_KEY (optional)")
    print("   - GOOGLE_MAPS_API_KEY (optional)")
    print("\n💡 Run 'python setup.py' to create a .env file from template")
    raise
