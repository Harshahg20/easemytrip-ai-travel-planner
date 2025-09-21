#!/usr/bin/env python3
"""
MySQL Database Initialization Script
Creates the database and tables for the Trip Planner application
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine, Base
from app.models.trip import Trip, DailyItinerary, TripOption
from app.core.config import settings

def init_database():
    """Initialize the database with tables"""
    try:
        print("🔄 Initializing database...")
        
        # Check if we're using MySQL
        if "mysql" in settings.database_url:
            print("📊 Using MySQL database")
            
            # Test connection
            with engine.connect() as connection:
                result = connection.execute("SELECT VERSION()")
                version = result.fetchone()[0]
                print(f"✅ Connected to MySQL {version}")
        else:
            print("📊 Using SQLite database")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Show created tables
        print("\n📋 Created tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")
        
        print("\n🎉 Database initialization completed!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure MySQL is running")
        print("2. Check your DATABASE_URL in .env file")
        print("3. Verify database credentials")
        print("4. Ensure the database exists")
        return False
    
    return True

def test_connection():
    """Test database connection"""
    try:
        print("🔍 Testing database connection...")
        with engine.connect() as connection:
            if "mysql" in settings.database_url:
                result = connection.execute("SELECT 1")
            else:
                result = connection.execute("SELECT 1")
            print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Trip Planner Database Initialization")
    print("=" * 50)
    
    # Test connection first
    if not test_connection():
        return False
    
    # Initialize database
    if not init_database():
        return False
    
    print("\n📝 Next steps:")
    print("1. Run 'python run.py' to start the application")
    print("2. Visit http://localhost:8000/docs for API documentation")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
