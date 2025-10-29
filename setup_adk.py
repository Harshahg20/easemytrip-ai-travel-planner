#!/usr/bin/env python3
"""
Google ADK Travel Concierge Setup Script
This script sets up the Google ADK integration for the Tripora project
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n{'='*60}")
    print(f"STEP {step}: {description}")
    print('='*60)

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, "Checking Python Version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ is required for Google ADK")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_google_cloud_cli():
    """Check if Google Cloud CLI is installed"""
    print_step(2, "Checking Google Cloud CLI")
    
    try:
        result = subprocess.run("gcloud --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Google Cloud CLI is installed")
            print(f"Version: {result.stdout.split()[0]}")
            return True
        else:
            print("❌ Google Cloud CLI not found")
            return False
    except FileNotFoundError:
        print("❌ Google Cloud CLI not found")
        return False

def install_google_cloud_cli():
    """Install Google Cloud CLI"""
    print_step(3, "Installing Google Cloud CLI")
    
    if sys.platform == "darwin":  # macOS
        command = "curl https://sdk.cloud.google.com | bash"
    elif sys.platform == "linux":  # Linux
        command = "curl https://sdk.cloud.google.com | bash"
    elif sys.platform == "win32":  # Windows
        print("Please install Google Cloud CLI manually from: https://cloud.google.com/sdk/docs/install")
        return False
    else:
        print("Unsupported platform. Please install Google Cloud CLI manually.")
        return False
    
    return run_command(command, "Installing Google Cloud CLI")

def setup_google_cloud_project():
    """Set up Google Cloud project"""
    print_step(4, "Setting up Google Cloud Project")
    
    project_id = input("Enter your Google Cloud Project ID (or press Enter for 'tripora-adk-concierge'): ").strip()
    if not project_id:
        project_id = "tripora-adk-concierge"
    
    print(f"Using project ID: {project_id}")
    
    # Set project
    if not run_command(f"gcloud config set project {project_id}", f"Setting project to {project_id}"):
        return False
    
    # Enable required APIs
    apis = [
        "aiplatform.googleapis.com",
        "dialogflow.googleapis.com",
        "translate.googleapis.com",
        "places.googleapis.com",
        "maps.googleapis.com",
        "discoveryengine.googleapis.com"
    ]
    
    for api in apis:
        if not run_command(f"gcloud services enable {api}", f"Enabling {api}"):
            print(f"⚠️  Warning: Failed to enable {api}")
    
    return True

def create_service_account():
    """Create service account for ADK"""
    print_step(5, "Creating Service Account")
    
    project_id = input("Enter your Google Cloud Project ID: ").strip()
    if not project_id:
        print("❌ Project ID is required")
        return False
    
    service_account_name = "tripora-adk-service"
    service_account_email = f"{service_account_name}@{project_id}.iam.gserviceaccount.com"
    
    # Create service account
    if not run_command(
        f"gcloud iam service-accounts create {service_account_name} --display-name='Tripora ADK Service Account'",
        "Creating service account"
    ):
        print("⚠️  Service account might already exist, continuing...")
    
    # Grant necessary roles
    roles = [
        "roles/aiplatform.user",
        "roles/dialogflow.client",
        "roles/translate.user",
        "roles/discoveryengine.viewer"
    ]
    
    for role in roles:
        run_command(
            f"gcloud projects add-iam-policy-binding {project_id} --member='serviceAccount:{service_account_email}' --role='{role}'",
            f"Granting role {role}"
        )
    
    # Create and download key
    key_file = "service-account-key.json"
    if not run_command(
        f"gcloud iam service-accounts keys create {key_file} --iam-account={service_account_email}",
        "Creating and downloading service account key"
    ):
        return False
    
    print(f"✅ Service account key saved to {key_file}")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_step(6, "Installing Python Dependencies")
    
    # Install ADK dependencies
    adk_deps = [
        "google-cloud-aiplatform[adk,agent_engine]",
        "google-cloud-dialogflow",
        "google-cloud-translate",
        "google-cloud-discoveryengine",
        "google-cloud-places",
        "websockets",
        "asyncio-mqtt"
    ]
    
    for dep in adk_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            print(f"⚠️  Warning: Failed to install {dep}")
    
    return True

def create_env_file():
    """Create .env file with ADK configuration"""
    print_step(7, "Creating Environment Configuration")
    
    env_file = Path("backend/.env")
    
    # Read existing .env if it exists
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Add ADK configuration
    adk_config = """
# Google Cloud ADK Settings
GOOGLE_CLOUD_PROJECT_ID=tripora-adk-concierge
GOOGLE_CLOUD_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# ADK Agent Settings
ADK_AGENT_TIMEOUT=30
ADK_MAX_CONVERSATION_HISTORY=50
ADK_ENABLE_SUBAGENTS=true

# External API Keys for sub-agents (optional)
OPENWEATHER_API_KEY=
AMADEUS_API_KEY=
BOOKING_API_KEY=
"""
    
    # Append ADK config if not already present
    if "GOOGLE_CLOUD_PROJECT_ID" not in env_content:
        with open(env_file, 'a') as f:
            f.write(adk_config)
        print("✅ Added ADK configuration to .env file")
    else:
        print("✅ ADK configuration already exists in .env file")
    
    return True

def test_installation():
    """Test the ADK installation"""
    print_step(8, "Testing ADK Installation")
    
    test_script = """
import sys
try:
    from google.cloud import aiplatform
    from google.cloud import dialogflow
    from google.cloud import translate_v2 as translate
    print("✅ All ADK dependencies imported successfully")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
    
    with open("test_adk.py", "w") as f:
        f.write(test_script)
    
    success = run_command("python test_adk.py", "Testing ADK imports")
    
    # Clean up test file
    if os.path.exists("test_adk.py"):
        os.remove("test_adk.py")
    
    return success

def main():
    """Main setup function"""
    print("🚀 Google ADK Travel Concierge Setup")
    print("This script will set up Google ADK integration for your Tripora project")
    
    # Check if we're in the right directory
    if not os.path.exists("backend") or not os.path.exists("frontend"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    steps = [
        check_python_version,
        check_google_cloud_cli,
        setup_google_cloud_project,
        create_service_account,
        install_dependencies,
        create_env_file,
        test_installation
    ]
    
    for i, step in enumerate(steps, 1):
        if not step():
            print(f"\n❌ Setup failed at step {i}")
            print("Please fix the error and run the script again")
            sys.exit(1)
    
    print("\n🎉 Google ADK Travel Concierge setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the backend: cd backend && python run.py")
    print("2. Start the frontend: cd frontend && npm start")
    print("3. Visit http://localhost:3000/concierge to test the Travel Concierge")
    print("\nFor more information, see the ADK_IMPLEMENTATION_GUIDE.md file")

if __name__ == "__main__":
    main()
