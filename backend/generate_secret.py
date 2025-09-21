#!/usr/bin/env python3
"""
Generate a secure secret key for the application
"""

import secrets
import string

def generate_secret_key(length=32):
    """Generate a secure secret key"""
    return secrets.token_urlsafe(length)

def generate_database_url():
    """Generate a sample database URL"""
    return "sqlite:///./trip_planner.db"

if __name__ == "__main__":
    print("🔐 Generated secure configuration values:")
    print(f"SECRET_KEY={generate_secret_key()}")
    print(f"DATABASE_URL={generate_database_url()}")
    print("\n📝 Copy these values to your .env file")
