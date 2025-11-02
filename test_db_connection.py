#!/usr/bin/env python3
"""
Test database connection and LIMIT query
"""
import sys
import os
from pathlib import Path

# Set environment variables before importing
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/easemytrip")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "AIzaSyAmLDYoqjcmPDT3-BVV0kA6fjNpCfyoccg")

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import engine, get_db
from app.models.trip import Trip
from sqlalchemy.orm import Session
from sqlalchemy import text

def test_database_connection():
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    print()
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()
            print(f"✅ MySQL Connected: {version[0]}")
            print()
        
        # Test LIMIT query
        print("Testing LIMIT/OFFSET query...")
        db = next(get_db())
        
        try:
            # This should work with modern MySQL syntax
            trips = db.query(Trip).offset(0).limit(10).all()
            print(f"✅ LIMIT query successful! Found {len(trips)} trip(s)")
            print()
            
            if trips:
                print("Sample trip:")
                trip = trips[0]
                print(f"  ID: {trip.id}")
                print(f"  Destination: {trip.destination}")
                print(f"  Status: {trip.status}")
            else:
                print("  No trips in database yet (this is normal)")
            
            print()
            print("=" * 60)
            print("✅ All tests passed!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ LIMIT query failed: {e}")
            print()
            print("Error details:")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print()
        print("Please check:")
        print("  1. MySQL is running: brew services start mysql")
        print("  2. Database exists: mysql -u root -e 'CREATE DATABASE IF NOT EXISTS easemytrip'")
        print("  3. DATABASE_URL in backend/.env is correct")
        print()
        return False


if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)

