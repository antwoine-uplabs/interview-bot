import logging
import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Local imports
from app.models.models import (
    InterviewStatus, UserLogin, UserSignUp, AuthResponse, 
    EvaluationCriterion, EvaluationSummary, EvaluationResponse
)
from app.services.supabase_client import supabase_service
from app.services.transcript_processor import transcript_processor
from app.services.evaluation_service import evaluate_interview
from app.utils.file_utils import save_uploaded_file
from app.services.langsmith import langsmith_service
from app.services.auth_service import get_current_user, auth_service

# Load environment variables (for Supabase credentials, LLM API keys, etc.)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Interview Evaluator API",
    description="API for evaluating data scientist interview transcripts using AI",
    version="0.1.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model for evaluation
class EvaluationRequest(BaseModel):
    """Request model for evaluation endpoint"""
    interview_id: str
    candidate_name: str
    transcript_path: Optional[str] = None


# Authentication routes
@app.post("/auth/login", response_model=AuthResponse, tags=["Authentication"])
async def login(user_data: UserLogin):
    """
    Authenticate a user and return an access token
    
    This endpoint:
    1. Takes user email and password
    2. Authenticates against Supabase
    3. Returns a JWT token if authentication is successful
    """
    try:
        if not supabase_service.is_connected():
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
            
        # Authenticate with Supabase
        result = supabase_service.sign_in_user(user_data.email, user_data.password)
        
        if not result or not result.get("access_token"):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
            
        # Return the token response
        return AuthResponse(
            access_token=result.get("access_token"),
            user_id=result.get("user", {}).get("id", ""),
            email=user_data.email,
            expires_in=result.get("expires_in", 3600)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.exception(f"Error during login: {e}")
        raise HTTPException(
            status_code=500,
            detail="Authentication failed due to an unexpected error"
        )


@app.post("/auth/signup", response_model=AuthResponse, tags=["Authentication"])
async def signup(user_data: UserSignUp):
    """
    Register a new user
    
    This endpoint:
    1. Takes user email, password, and optional name
    2. Creates a new user in Supabase
    3. Returns a JWT token for the new user
    """
    try:
        if not supabase_service.is_connected():
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
            
        # Create user in Supabase
        result = supabase_service.sign_up_user(
            email=user_data.email, 
            password=user_data.password,
            user_metadata={"name": user_data.name} if user_data.name else None
        )
        
        if not result or not result.get("access_token"):
            raise HTTPException(
                status_code=400,
                detail="Failed to create user account"
            )
            
        # Return the token response
        return AuthResponse(
            access_token=result.get("access_token"),
            user_id=result.get("user", {}).get("id", ""),
            email=user_data.email,
            expires_in=result.get("expires_in", 3600)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.exception(f"Error during signup: {e}")
        raise HTTPException(
            status_code=500,
            detail="User registration failed due to an unexpected error"
        )


# Background task for processing transcripts
async def process_interview_transcript(file_path: str, interview_id: str):
    """
    Process an interview transcript in the background
    
    This uses our LangGraph agent to evaluate the transcript.
    """
    try:
        logger.info(f"Starting background processing for interview {interview_id}")
        
        # Update interview status to processing
        if supabase_service.is_connected():
            supabase_service.update_interview_status(interview_id, InterviewStatus.PROCESSING)
        
        # Extract candidate name from Supabase or use a default
        candidate_name = "Candidate"
        if supabase_service.is_connected():
            interview_data = supabase_service.get_interview(interview_id)
            if interview_data:
                candidate_name = interview_data.get("candidate_name", "Candidate")
        
        # Process the transcript using our evaluation service
        result = await evaluate_interview(
            interview_id=interview_id,
            candidate_name=candidate_name,
            transcript_path=file_path
        )
        
        # Update status based on result
        if result.get("status") == "success":
            logger.info(f"Evaluation completed successfully for interview {interview_id}")
            
            # In Sprint 3, we store the evaluation results in Supabase
            # This is done automatically by the LangGraph agent now
            # The storage_node will handle saving to Supabase and updating the status
            
            # Storage is now handled by the LangGraph agent (store_results_node)
            # so we don't need to explicitly update the status here
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Failed to evaluate interview {interview_id}: {error}")
            
            # Update interview status to error
            if supabase_service.is_connected():
                supabase_service.update_interview_status(interview_id, InterviewStatus.ERROR)
    
    except Exception as e:
        logger.error(f"Error in background task for interview {interview_id}: {e}", exc_info=True)
        
        # Update interview status to error
        if supabase_service.is_connected():
            supabase_service.update_interview_status(interview_id, InterviewStatus.ERROR)


@app.post("/evaluate", tags=["Evaluation"], response_model_exclude_none=True)
async def evaluate_transcript(
    request: EvaluationRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Evaluate an interview transcript using the LangGraph agent.
    
    This endpoint:
    1. Takes an interview ID and optionally a transcript path
    2. Runs the evaluation agent on the transcript
    3. Returns the evaluation results
    
    Note: This is a synchronous endpoint that will wait for the evaluation to complete.
    For large transcripts, use the /upload endpoint which processes in the background.
    
    Requires authentication via JWT Bearer token.
    """
    try:
        # Create a trace for this request
        trace_id = langsmith_service.trace_run(
            name="evaluate_transcript_api",
            inputs={
                "interview_id": request.interview_id,
                "candidate_name": request.candidate_name,
                "user_id": current_user.get("user_id")
            }
        )
        
        # Run the evaluation
        result = await evaluate_interview(
            interview_id=request.interview_id,
            candidate_name=request.candidate_name,
            transcript_path=request.transcript_path
        )
        
        # Return the result
        return result
        
    except Exception as e:
        logger.exception(f"Error evaluating transcript: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating transcript: {str(e)}"
        )


@app.get("/health", tags=["General"])
async def health_check():
    """
    Check the health of the API and its dependencies
    """
    logger.info("Health check endpoint called")
    
    # Check Supabase connection
    supabase_connected = supabase_service.is_connected()
    
    # For Sprint 1, we don't check LLM availability
    # In later sprints, we'll add checks for LlamaIndex, LangGraph, etc.
    
    return JSONResponse(content={
        "status": "ok" if supabase_connected else "degraded",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "supabase": "connected" if supabase_connected else "disconnected"
        }
    })


@app.get("/status/{interview_id}", tags=["Evaluation"])
async def get_interview_status(
    interview_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the status of an interview evaluation
    
    This endpoint:
    1. Takes an interview ID
    2. Retrieves the current status from the database
    3. Returns the status and related information
    
    Requires authentication via JWT Bearer token.
    """
    try:
        logger.info(f"Status check for interview {interview_id}")
        
        # Get the interview from Supabase
        if not supabase_service.is_connected():
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection unavailable"
                }
            )
        
        # Get the interview record
        interview = supabase_service.get_interview(interview_id)
        
        if not interview:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Interview with ID {interview_id} not found"
                }
            )
        
        # Return the status
        return JSONResponse(content={
            "interview_id": interview_id,
            "status": interview.get("status", "unknown"),
            "candidate_name": interview.get("candidate_name", "Unknown"),
            "created_at": interview.get("created_at"),
            "updated_at": interview.get("updated_at")
        })
        
    except Exception as e:
        logger.exception(f"Error getting interview status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting interview status: {str(e)}"
        )


@app.get("/evaluations", tags=["Evaluation"])
async def get_all_evaluations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """
    Get all evaluations for the current user
    
    This endpoint:
    1. Takes optional limit and offset parameters for pagination
    2. Retrieves all evaluations from the database for the current user
    3. Returns the formatted results
    
    Requires authentication via JWT Bearer token.
    """
    try:
        logger.info(f"Fetching evaluations for user {current_user.get('user_id')}")
        
        # First, check if Supabase is connected
        if not supabase_service.is_connected():
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection unavailable"
                }
            )
        
        # Get all evaluations for the current user
        evaluations = supabase_service.get_all_evaluations(
            user_id=current_user.get("user_id"),
            limit=limit,
            offset=offset
        )
        
        if not evaluations:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "No evaluations found",
                    "data": []
                }
            )
        
        # Return the results
        return JSONResponse(content=evaluations)
        
    except Exception as e:
        logger.exception(f"Error getting evaluations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting evaluations: {str(e)}"
        )

@app.get("/results/{interview_id}", tags=["Evaluation"])
async def get_evaluation_results(
    interview_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the evaluation results for an interview
    
    This endpoint:
    1. Takes an interview ID
    2. Retrieves the evaluation results from the database
    3. Returns the formatted results
    
    Note: This endpoint will return a 404 if the interview has not been evaluated yet
    
    Requires authentication via JWT Bearer token.
    """
    try:
        logger.info(f"Results request for interview {interview_id}")
        
        # First, check if Supabase is connected
        if not supabase_service.is_connected():
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection unavailable"
                }
            )
        
        # Get the interview record
        interview = supabase_service.get_interview(interview_id)
        
        if not interview:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Interview with ID {interview_id} not found"
                }
            )
        
        # Check if the interview has been evaluated
        if interview.get("status") != InterviewStatus.EVALUATED:
            return JSONResponse(
                status_code=409,
                content={
                    "status": "pending",
                    "message": f"Interview is still in '{interview.get('status')}' status",
                    "interview_id": interview_id
                }
            )
        
        # Get the evaluation results
        results = supabase_service.get_evaluation_results(interview_id)
        
        if not results:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Evaluation results not found for interview {interview_id}"
                }
            )
        
        # Add interview metadata to the results
        results["interview_id"] = interview_id
        results["candidate_name"] = interview.get("candidate_name", "Unknown")
        results["interview_date"] = interview.get("interview_date")
        results["status"] = "success"
        
        # Return the results
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.exception(f"Error getting evaluation results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting evaluation results: {str(e)}"
        )


@app.post("/upload", tags=["Evaluation"], status_code=202)
async def upload_transcript(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    candidate_name: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload an interview transcript for evaluation
    
    This endpoint:
    1. Validates the uploaded file
    2. Saves it to a temporary location
    3. Creates an interview record in Supabase (if connected)
    4. Starts a background task to process the transcript
    5. Returns the interview ID for tracking
    
    Requires authentication via JWT Bearer token.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        logger.info(f"Received file upload request: {file.filename}")
        
        # Save the file
        success, file_path, error = await save_uploaded_file(file)
        if not success or not file_path:
            raise HTTPException(status_code=400, detail=error or "Failed to save file")
        
        # Determine candidate name
        if not candidate_name:
            # Extract from filename if not provided
            candidate_name = os.path.splitext(file.filename)[0]
        
        # Create an interview record (if Supabase is connected)
        interview_id = str(uuid.uuid4())
        
        interview_data = {
            "id": interview_id,
            "user_id": current_user.get("user_id"),  # Associate with authenticated user
            "candidate_name": candidate_name,
            "interview_date": datetime.now().isoformat(),
            "transcript_storage_path": file_path,
            "status": InterviewStatus.UPLOADED,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # If Supabase is connected, create the record
        if supabase_service.is_connected():
            result = supabase_service.create_interview(interview_data)
            if result:
                interview_id = result.get("id", interview_id)
                logger.info(f"Interview record created in Supabase with ID: {interview_id}")
        else:
            logger.warning("Supabase not connected, interview record not created")
        
        # Start a background task to process the transcript
        background_tasks.add_task(process_interview_transcript, file_path, interview_id)
        
        # Return response
        return JSONResponse(
            content={
                "message": "Transcript uploaded successfully, processing started",
                "interview_id": interview_id,
                "candidate_name": candidate_name,
                "filename": file.filename,
                "status": InterviewStatus.UPLOADED
            }
        )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
        
    except Exception as e:
        # Log the error and return a generic error response
        logger.error(f"Error processing transcript upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the transcript"
        )


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Interview Evaluator API...")
    # Use port 8000 as specified in custom instructions
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)