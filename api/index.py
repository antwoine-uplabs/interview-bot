# api/index.py
import sys
import os
from dotenv import load_dotenv

# Add the parent directory (root) to the Python path
# This allows importing from the 'app' module
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

# Load environment variables before importing app
dotenv_path = os.path.join(root_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    # For Vercel deployment, environment variables are set in the Vercel dashboard
    # This is just for local development with a .env file
    print("Warning: .env file not found. Using environment variables from system.")

# Set required environment variables with default values if not present
# These will be overridden by Vercel environment settings in production
if not os.environ.get("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://kicnoeliggudihnepouz.supabase.co"
    
if not os.environ.get("SUPABASE_KEY") and not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
    # Use a placeholder in development mode
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpY25vZWxpZ2d1ZGlobmVwb3V6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDg2NTMxNCwiZXhwIjoyMDYwNDQxMzE0fQ.Y0rXakbpkDqOPDydM1LKl7ipsYXjhvsoLwGNIXNZprU"

# Now import the FastAPI app after environment setup
# Vercel's Python runtime automatically detects the 'app' variable.
from app.main import app

# Add a Vercel-specific root endpoint
@app.get("/")
async def vercel_root():
    """
    Root endpoint for Vercel deployment
    Provides basic API information and status
    """
    return {
        "status": "online",
        "service": "Interview Evaluator API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health"
    }