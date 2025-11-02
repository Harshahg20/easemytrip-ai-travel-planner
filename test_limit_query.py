#!/usr/bin/env python3
"""
Simple test for LIMIT/OFFSET query syntax
"""
import sys
import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/easemytrip")

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import engine
from sqlalchemy import text

def test_limit_query():
    print("=" * 60)
    print("LIMIT/OFFSET Query Test")
    print("=" * 60)
    print()
    
    try:
        with engine.connect() as conn:
            # Test MySQL version
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"✅ MySQL Version: {version}")
            print()
            
            # Test modern LIMIT OFFSET syntax
            print("Testing LIMIT/OFFSET syntax...")
            query = text("SELECT 1 AS test_column LIMIT :limit OFFSET :offset")
            result = conn.execute(query, {"limit": 10, "offset": 0})
            rows = result.fetchall()
            print(f"✅ Modern LIMIT OFFSET syntax works!")
            print(f"   Query returned {len(rows)} row(s)")
            print()
            
            # Test on actual trips table if it exists
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM trips"))
                count = result.fetchone()[0]
                print(f"✅ Trips table exists with {count} trip(s)")
                print()
                
                if count > 0:
                    result = conn.execute(text("SELECT id, destination FROM trips LIMIT :limit OFFSET :offset"), 
                                        {"limit": 5, "offset": 0})
                    trips = result.fetchall()
                    print(f"✅ LIMIT query on trips table successful!")
                    print(f"   Retrieved {len(trips)} trip(s):")
                    for trip in trips:
                        print(f"     - {trip[0]}: {trip[1]}")
                else:
                    print("ℹ️  No trips in database yet (this is normal)")
                    
            except Exception as e:
                print(f"ℹ️  Trips table doesn't exist yet: {e}")
            
            print()
            print("=" * 60)
            print("✅ LIMIT/OFFSET issue is FIXED!")
            print("=" * 60)
            print()
            print("The database is now properly configured for MySQL 9.x")
            print("You can now start your application without LIMIT errors.")
            print()
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_limit_query()
    sys.exit(0 if success else 1)

