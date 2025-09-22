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
    
    # Database - Must be provided in .env file
    database_url: str
    
    # Security - Must be provided in .env file
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Google AI APIs - Must be provided in .env file
    google_ai_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    google_cloud_project_id: Optional[str] = None
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001"
    
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
        case_sensitive = False
        env_file_encoding = "utf-8"


# Create settings instance with error handling
try:
    settings = Settings()
except Exception as e:
    print("❌ Error loading configuration:")
    print(f"   {str(e)}")
    print("\n📝 Please ensure you have a .env file with the required variables:")
    print("   - DATABASE_URL")
    print("   - SECRET_KEY")
    print("   - GOOGLE_AI_API_KEY (optional)")
    print("   - GOOGLE_MAPS_API_KEY (optional)")
    print("\n💡 Run 'python setup.py' to create a .env file from template")
    raise
