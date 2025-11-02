#!/usr/bin/env python3
"""
Migration script to add photos_base64 column to trips table
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine
from app.core.config import settings

def add_photos_column():
    """Add photos_base64 column to trips table if it doesn't exist"""
    try:
        print("🔄 Adding photos_base64 column to trips table...")
        
        with engine.connect() as connection:
            from sqlalchemy import text
            
            # Check if column exists
            if "mysql" in settings.database_url:
                # MySQL
                check_query = text("""
                    SELECT COUNT(*) 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'trips' 
                    AND COLUMN_NAME = 'photos_base64'
                """)
                result = connection.execute(check_query)
                column_exists = result.fetchone()[0] > 0
                
                if not column_exists:
                    # Add column
                    alter_query = text("""
                        ALTER TABLE trips 
                        ADD COLUMN photos_base64 JSON NULL
                    """)
                    connection.execute(alter_query)
                    connection.commit()
                    print("✅ Successfully added photos_base64 column to trips table")
                else:
                    print("ℹ️  Column photos_base64 already exists in trips table")
            else:
                # SQLite - check if column exists by attempting to select it
                try:
                    test_query = text("SELECT photos_base64 FROM trips LIMIT 1")
                    connection.execute(test_query)
                    print("ℹ️  Column photos_base64 already exists in trips table")
                except Exception:
                    # Column doesn't exist, add it
                    alter_query = text("""
                        ALTER TABLE trips 
                        ADD COLUMN photos_base64 TEXT
                    """)
                    connection.execute(alter_query)
                    connection.commit()
                    print("✅ Successfully added photos_base64 column to trips table")
        
        print("\n🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_photos_column()
    sys.exit(0 if success else 1)

