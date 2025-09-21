#!/usr/bin/env python3
"""
Validate environment configuration
"""

import os
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("💡 Run 'python setup.py' to create one from template")
        return False
    
    print("✅ .env file exists")
    return True

def check_required_vars():
    """Check if required environment variables are set"""
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY"
    ]
    
    optional_vars = [
        "GOOGLE_AI_API_KEY",
        "GOOGLE_MAPS_API_KEY"
    ]
    
    missing_required = []
    missing_optional = []
    
    # Load .env file manually
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    # Check required variables
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f"your_{var.lower()}_here":
            missing_required.append(var)
    
    # Check optional variables
    for var in optional_vars:
        if not os.getenv(var) or os.getenv(var) == f"your_{var.lower()}_here":
            missing_optional.append(var)
    
    # Report results
    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        return False
    
    if missing_optional:
        print("⚠️  Missing optional environment variables:")
        for var in missing_optional:
            print(f"   - {var}")
        print("   (These are optional but recommended for full functionality)")
    
    print("✅ All required environment variables are set")
    return True

def validate_secret_key():
    """Validate that SECRET_KEY is secure"""
    secret_key = os.getenv("SECRET_KEY")
    
    if not secret_key:
        print("❌ SECRET_KEY not set")
        return False
    
    if secret_key == "your_secret_key_here":
        print("❌ SECRET_KEY is still using placeholder value")
        print("💡 Run 'python generate_secret.py' to generate a secure key")
        return False
    
    if len(secret_key) < 32:
        print("⚠️  SECRET_KEY is shorter than recommended (32+ characters)")
    
    print("✅ SECRET_KEY is properly configured")
    return True

def main():
    """Main validation function"""
    print("🔍 Validating environment configuration...\n")
    
    checks = [
        check_env_file,
        check_required_vars,
        validate_secret_key
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 Environment configuration is valid!")
        print("🚀 You can now run 'python run.py' to start the server")
    else:
        print("❌ Environment configuration has issues")
        print("💡 Please fix the issues above before running the application")

if __name__ == "__main__":
    main()
