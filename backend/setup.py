#!/usr/bin/env python3
"""
Setup script for Trip Planner Backend
This script helps set up the development environment
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_environment():
    """Set up the development environment"""
    print("🚀 Setting up Trip Planner Backend...")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create virtual environment
    if not os.path.exists("venv"):
        if not run_command("python3 -m venv venv", "Creating virtual environment"):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install dependencies
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            run_command("cp env.example .env", "Creating .env file from template")
            
            # Generate and set a secure secret key
            import secrets
            secret_key = secrets.token_urlsafe(32)
            
            # Read the .env file and replace the placeholder
            with open(".env", "r") as f:
                content = f.read()
            
            content = content.replace("your_secret_key_here", secret_key)
            
            with open(".env", "w") as f:
                f.write(content)
            
            print("🔐 Generated secure SECRET_KEY automatically")
            print("📝 Please edit .env file with your Google AI API keys")
        else:
            print("⚠️  env.example not found, please create .env file manually")
    else:
        print("✅ .env file already exists")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Configure your database:")
    print("   - For SQLite (development): No changes needed")
    print("   - For MySQL 9.0: Update DATABASE_URL in .env file")
    print("2. Edit .env file with your Google AI API keys")
    print("3. Get API keys from:")
    print("   - Google AI Studio: https://aistudio.google.com/")
    print("   - Google Maps API: https://console.cloud.google.com/")
    print("4. Initialize database: python init_mysql_db.py")
    print("5. Run the application: python run.py")
    print("6. Visit http://localhost:8000/docs for API documentation")
    
    return True

if __name__ == "__main__":
    setup_environment()
