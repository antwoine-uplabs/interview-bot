# api/index.py
import sys
import os

# Add the parent directory (root) to the Python path
# This allows importing from the 'app' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your existing FastAPI application instance
# Vercel's Python runtime automatically detects the 'app' variable.
from app.main import app

# Optional: You can add a simple health check endpoint here for Vercel's checks,
# although your main app already has one at /api/health.
# @app.get("/api")
# def handle_root():
#     return {"message": "FastAPI running via Vercel handler"} 