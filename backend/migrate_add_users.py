#!/usr/bin/env python3
"""
Migration script to add users table and user_id column to trips table
Run this against the production database
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

def run_migration():
    """
    Add users table and user_id column to trips table
    """
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Usage: DATABASE_URL='mysql+pymysql://...' python migrate_add_users.py")
        sys.exit(1)
    
    print("=" * 70)
    print("Database Migration: Add Users & user_id to Trips")
    print("=" * 70)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    print()
    
    # Create engine
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            print("✅ Connected to database")
            print()
            
            # Step 1: Create users table if not exists
            print("Step 1: Creating users table...")
            create_users_table = text("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(255) PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            conn.execute(create_users_table)
            conn.commit()
            print("✅ Users table created (or already exists)")
            print()
            
            # Step 2: Check if user_id column exists in trips table
            print("Step 2: Checking if user_id column exists...")
            check_column = text("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'trips' 
                AND COLUMN_NAME = 'user_id'
            """)
            result = conn.execute(check_column)
            column_exists = result.fetchone()[0] > 0
            
            if column_exists:
                print("✅ user_id column already exists in trips table")
                print()
            else:
                print("Adding user_id column to trips table...")
                
                # Step 3: Create a default/guest user for existing trips
                print("Step 3: Creating default guest user...")
                import uuid
                guest_id = str(uuid.uuid4())
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                guest_password = pwd_context.hash("guest_password_change_me")
                
                insert_guest = text("""
                    INSERT INTO users (id, email, password_hash, name, is_active)
                    VALUES (:id, :email, :password_hash, :name, :is_active)
                    ON DUPLICATE KEY UPDATE id=id
                """)
                conn.execute(insert_guest, {
                    'id': guest_id,
                    'email': 'guest@tripplanner.local',
                    'password_hash': guest_password,
                    'name': 'Guest User',
                    'is_active': True
                })
                conn.commit()
                print(f"✅ Guest user created with ID: {guest_id}")
                print()
                
                # Step 4: Add user_id column (nullable first)
                print("Step 4: Adding user_id column to trips table (nullable)...")
                add_column = text("""
                    ALTER TABLE trips 
                    ADD COLUMN user_id VARCHAR(255) NULL
                """)
                conn.execute(add_column)
                conn.commit()
                print("✅ user_id column added")
                print()
                
                # Step 5: Update existing trips to use guest user
                print("Step 5: Updating existing trips with guest user_id...")
                update_trips = text("""
                    UPDATE trips 
                    SET user_id = :guest_id 
                    WHERE user_id IS NULL
                """)
                result = conn.execute(update_trips, {'guest_id': guest_id})
                conn.commit()
                print(f"✅ Updated {result.rowcount} trips with guest user_id")
                print()
                
                # Step 6: Make user_id NOT NULL and add foreign key
                print("Step 6: Making user_id NOT NULL and adding foreign key...")
                alter_column = text("""
                    ALTER TABLE trips 
                    MODIFY COLUMN user_id VARCHAR(255) NOT NULL,
                    ADD INDEX idx_user_id (user_id),
                    ADD CONSTRAINT fk_trips_user_id 
                    FOREIGN KEY (user_id) REFERENCES users(id)
                """)
                conn.execute(alter_column)
                conn.commit()
                print("✅ user_id column configured with foreign key")
                print()
            
            print("=" * 70)
            print("✅ Migration completed successfully!")
            print("=" * 70)
            print()
            print("Note: All existing trips have been assigned to a guest user.")
            print("      Email: guest@tripplanner.local")
            print()
            
    except (OperationalError, ProgrammingError) as e:
        print(f"❌ Migration failed: {e}")
        print()
        print("This might be due to:")
        print("  1. Incorrect DATABASE_URL")
        print("  2. Insufficient database permissions")
        print("  3. Database connection issues")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_migration()

