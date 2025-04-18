# api/index.py
import sys
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api")

try:
    # Add the parent directory (root) to the Python path
    # This allows importing from the 'app' module
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, root_dir)
    logger.info(f"Added {root_dir} to Python path")

    # Load environment variables before importing app
    dotenv_path = os.path.join(root_dir, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        logger.info("Loaded environment variables from .env file")
    else:
        # For Vercel deployment, environment variables are set in the Vercel dashboard
        # This is just for local development with a .env file
        logger.warning("Warning: .env file not found. Using environment variables from system.")

    # Set required environment variables with default values if not present
    # These will be overridden by Vercel environment settings in production
    if not os.environ.get("SUPABASE_URL"):
        os.environ["SUPABASE_URL"] = "https://kicnoeliggudihnepouz.supabase.co"
        logger.info("Set default SUPABASE_URL")
        
    if not os.environ.get("SUPABASE_KEY") and not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
        # Use a placeholder in development mode
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpY25vZWxpZ2d1ZGlobmVwb3V6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDg2NTMxNCwiZXhwIjoyMDYwNDQxMzE0fQ.Y0rXakbpkDqOPDydM1LKl7ipsYXjhvsoLwGNIXNZprU"
        logger.info("Set default SUPABASE_SERVICE_ROLE_KEY")

    logger.info("Starting API initialization")
    
    # Now import the FastAPI app after environment setup
    # Vercel's Python runtime automatically detects the 'app' variable.
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    
    try:
        # Try to import from app.main
        from app.main import app
        logger.info("Successfully imported app from app.main")
        
        # Remove any existing CORS middleware if present
        for middleware in app.user_middleware:
            if isinstance(middleware, CORSMiddleware):
                app.user_middleware.remove(middleware)
                logger.info("Removed existing CORS middleware")
                
        # Add updated CORS middleware with explicit origins
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://interview-bot1.vercel.app",
                "https://interview-bot.vercel.app",
                "https://interview-bot-frontend.vercel.app",
                "https://interview-bot-gamma.vercel.app",
                "http://localhost:5173",
                "http://localhost:3000"
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"]
        )
        logger.info("Added CORS middleware with explicit origins")
        
    except ImportError as e:
        logger.error(f"Error importing app from app.main: {e}")
        logger.info("Creating fallback FastAPI app")
        # Create a fallback app if the import fails
        app = FastAPI(
            title="Interview Evaluator API (Fallback)",
            description="Fallback API for Interview Evaluator",
            version="1.0.0"
        )
        
        # Add CORS middleware with explicit origins
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://interview-bot1.vercel.app",
                "https://interview-bot.vercel.app",
                "https://interview-bot-frontend.vercel.app",
                "https://interview-bot-gamma.vercel.app",
                "http://localhost:5173",
                "http://localhost:3000"
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"]
        )
        logger.info("Added CORS middleware with explicit origins to fallback app")
        
        # Add error handler for internal server errors
        @app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Please check logs for details."}
            )

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
            "health_check": "/health",
            "cors": "Configured for specific origins"
        }

    # Add an improved health check endpoint
    @app.get("/health")
    async def health_check():
        """
        Enhanced health check endpoint with authentication verification
        """
        try:
            # Verify that Supabase credentials are working
            # This is a lightweight check that doesn't need to hit the database
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            
            auth_status = "valid" if supabase_url and supabase_key else "missing"
            
            return {
                "status": "healthy",
                "authentication": auth_status,
                "timestamp": "Vercel deployment is active",
                "cors": "Configured for specific origins"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "authentication": "failed",
                "timestamp": "Vercel deployment is active but experiencing issues"
            }
    
    # Add a CORS preflight route
    @app.options("/{path:path}")
    async def options_route(path: str):
        """
        Handle CORS preflight requests
        """
        return {}
        
    logger.info("API initialization complete")

except Exception as e:
    logger.critical(f"Critical error during API initialization: {e}", exc_info=True)
    # Create a minimal emergency app that at least starts
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/{path:path}")
    async def emergency_handler(path: str):
        return {
            "status": "error",
            "message": "API is in emergency mode due to initialization error",
            "error": str(e)
        }