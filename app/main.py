"""
Main FastAPI application entry point for the Interview Evaluator.
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import sentry_sdk
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from dotenv import load_dotenv

from app.models.models import (
    AuthResponse, EvaluationRequest, EvaluationResponse, HealthCheckResponse,
    InterviewStatus, MonitoringDataResponse, SystemStatus,
    UserLogin, UserSignUp
)
from app.services.alerting import get_alerting_service
from app.services.auth_service import get_current_user, auth_service
from app.services.cost_monitoring import get_cost_monitoring_service
from app.services.evaluation_service import evaluate_interview
from app.services.langsmith.client import langsmith_service as get_langsmith_client
from app.services.monitoring import get_monitoring_service
from app.services.supabase_client import get_supabase_client
from app.services.transcript_processor import transcript_processor
from app.utils.file_utils import save_uploaded_file

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry
if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        enable_tracing=True,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.2")),
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
    )
    logger.info("Sentry initialized for error tracking and monitoring")

# Create FastAPI app
app = FastAPI(
    title="Interview Evaluator API",
    description="API for evaluating data scientist interview transcripts using AI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend Vite default port (development)
        "http://localhost:3000",  # Alternative local development port
        "https://*.vercel.app",   # Vercel preview deployments
        "https://*.interview-evaluator.app"  # Production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to track API requests
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Skip monitoring for health check endpoints to avoid noise
    if not request.url.path.endswith("/health"):
        monitoring_service = get_monitoring_service()
        await monitoring_service.record_metric("api_requests", 1)
        
        # Record status code metrics
        status_code = response.status_code
        metric_name = f"status_{status_code}"
        await monitoring_service.record_metric(metric_name, 1)
        
        # Record error metrics if error occurred
        if status_code >= 400:
            await monitoring_service.record_metric("error_count", 1)
    
    return response


# Scheduled task for alert checking
@app.on_event("startup")
async def startup_event():
    """Run scheduled tasks on startup."""
    try:
        # Initialize services
        monitoring_service = get_monitoring_service()
        cost_monitoring_service = get_cost_monitoring_service()
        alerting_service = get_alerting_service()
        
        # Sync cost data
        await cost_monitoring_service.sync_with_langsmith()
        
        # Check alert conditions
        await alerting_service.check_alert_conditions()
        
        logger.info("Startup tasks completed")
    except Exception as e:
        logger.error(f"Error in startup tasks: {e}")
        sentry_sdk.capture_exception(e)


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
        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
            
        # Authenticate with Supabase
        result = await auth_service.sign_in_user(user_data.email, user_data.password)
        
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
        sentry_sdk.capture_exception(e)
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
        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
            
        # Create user in Supabase
        result = await auth_service.sign_up_user(
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
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=500,
            detail="User registration failed due to an unexpected error"
        )


# Background task for processing transcripts
async def process_interview_transcript(file_path: str, interview_id: str, user_id: str):
    """
    Process an interview transcript in the background
    
    This uses our LangGraph agent to evaluate the transcript.
    """
    try:
        logger.info(f"Starting background processing for interview {interview_id}")
        
        # Initialize services
        supabase = get_supabase_client()
        langsmith = get_langsmith_client()
        monitoring = get_monitoring_service(supabase, langsmith)
        
        # Update interview status to processing
        await supabase.table("interviews").update(
            {"status": InterviewStatus.PROCESSING}
        ).eq("id", interview_id).execute()
        
        # Extract candidate name from Supabase
        interview_data = await supabase.table("interviews").select("*").eq("id", interview_id).execute()
        candidate_name = "Candidate"
        if interview_data.data:
            candidate_name = interview_data.data[0].get("candidate_name", "Candidate")
        
        # Process the transcript
        processed_text = await transcript_processor.process_transcript(file_path)
        
        # Start monitoring the evaluation time
        start_time = datetime.now()
        
        # Perform evaluation
        result = await evaluate_interview(
            interview_id=interview_id,
            candidate_name=candidate_name,
            transcript_text=processed_text,
            user_id=user_id
        )
        
        # Record evaluation time
        end_time = datetime.now()
        evaluation_time = (end_time - start_time).total_seconds()
        await monitoring.record_metric("evaluation_count", 1)
        await monitoring.record_metric("average_evaluation_time", evaluation_time)
        
        # Update status based on result
        if result.get("status") == "success":
            logger.info(f"Evaluation completed successfully for interview {interview_id}")
            # Storage is now handled by the LangGraph agent's storage node
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Failed to evaluate interview {interview_id}: {error}")
            
            # Update interview status to error
            await supabase.table("interviews").update(
                {"status": InterviewStatus.ERROR}
            ).eq("id", interview_id).execute()
            
            # Create alert for failed evaluation
            await monitoring.create_alert(
                level="ERROR",
                message=f"Evaluation failed for interview {interview_id}: {error}",
                source="evaluation_service"
            )
    
    except Exception as e:
        logger.error(f"Error in background task for interview {interview_id}: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)
        
        # Update interview status to error
        supabase = get_supabase_client()
        await supabase.table("interviews").update(
            {"status": InterviewStatus.ERROR}
        ).eq("id", interview_id).execute()
        
        # Create alert for critical error
        monitoring = get_monitoring_service()
        await monitoring.create_alert(
            level="CRITICAL",
            message=f"Critical error processing interview {interview_id}: {str(e)}",
            source="background_task"
        )


@app.post("/evaluate", tags=["Evaluation"], response_model=EvaluationResponse)
async def evaluate_endpoint(
    request: EvaluationRequest, 
    user_id: str = Depends(get_current_user)
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
        # Initialize services
        langsmith = get_langsmith_client()
        supabase = get_supabase_client()
        monitoring = get_monitoring_service(supabase, langsmith)
        
        # Create a trace for this request
        trace_id = await langsmith.trace_run(
            name="evaluate_transcript_api",
            inputs={
                "interview_id": request.interview_id,
                "candidate_name": request.candidate_name,
                "user_id": user_id
            }
        )
        
        # Start monitoring the evaluation time
        start_time = datetime.now()
        
        # Run the evaluation
        result = await evaluate_interview(
            interview_id=request.interview_id,
            candidate_name=request.candidate_name,
            transcript_path=request.transcript_path,
            user_id=user_id
        )
        
        # Record evaluation time
        end_time = datetime.now()
        evaluation_time = (end_time - start_time).total_seconds()
        await monitoring.record_metric("evaluation_count", 1)
        await monitoring.record_metric("average_evaluation_time", evaluation_time)
        
        # Return the result
        return result
        
    except Exception as e:
        logger.exception(f"Error evaluating transcript: {e}")
        sentry_sdk.capture_exception(e)
        
        # Record error in monitoring
        monitoring = get_monitoring_service()
        await monitoring.record_metric("error_count", 1)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating transcript: {str(e)}"
        )


@app.get("/health", response_model=HealthCheckResponse, tags=["General"])
async def health_check():
    """
    Check the health of the API and its dependencies
    Returns service status and uptime information.
    """
    logger.info("Health check endpoint called")
    
    # Get monitoring service for system health
    monitoring_service = get_monitoring_service()
    health_data = await monitoring_service.get_system_health()
    
    # Check Supabase connection
    supabase_status = SystemStatus.UP
    try:
        supabase = get_supabase_client()
        if not supabase or not supabase.is_connected():
            supabase_status = SystemStatus.DOWN
    except Exception as e:
        logger.error(f"Supabase health check failed: {str(e)}")
        supabase_status = SystemStatus.DOWN
    
    # Check LangSmith connection - make this optional
    langsmith_status = SystemStatus.UP
    try:
        langsmith = get_langsmith_client()
        # Simple attribute check to see if it's initialized
        if not hasattr(langsmith, 'initialized') or not langsmith.initialized:
            langsmith_status = SystemStatus.DOWN
    except Exception as e:
        logger.error(f"LangSmith health check failed: {str(e)}")
        langsmith_status = SystemStatus.DOWN
    
    return HealthCheckResponse(
        status="healthy",  # Always return healthy for Vercel checks
        api_version="1.0.0",
        timestamp=datetime.now().isoformat(),
        supabase_status=supabase_status,
        langsmith_status=langsmith_status
    )


@app.get("/status/{interview_id}", tags=["Evaluation"])
async def get_interview_status(
    interview_id: str,
    user_id: str = Depends(get_current_user)
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
        supabase = get_supabase_client()
        if not supabase:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection unavailable"
                }
            )
        
        # Get the interview record
        response = await supabase.table("interviews").select("*").eq("id", interview_id).execute()
        
        if not response.data:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Interview with ID {interview_id} not found"
                }
            )
        
        interview = response.data[0]
        
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
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting interview status: {str(e)}"
        )


@app.get("/evaluations", tags=["Evaluation"])
async def get_all_evaluations(
    user_id: str = Depends(get_current_user),
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
        logger.info(f"Fetching evaluations for user {user_id}")
        
        # Get Supabase client
        supabase = get_supabase_client()
        if not supabase:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection unavailable"
                }
            )
        
        # Get all evaluations for the current user
        response = await supabase.table("evaluations") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", options={"ascending": False}) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        if not response.data:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "No evaluations found",
                    "data": []
                }
            )
        
        # Return the results
        return JSONResponse(content={
            "status": "success",
            "data": response.data,
            "count": len(response.data),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.exception(f"Error getting evaluations: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting evaluations: {str(e)}"
        )


@app.get("/monitoring", response_model=MonitoringDataResponse, tags=["Monitoring"])
async def get_monitoring_data(
    user_id: str = Depends(get_current_user),
    time_range_hours: Optional[int] = 24
):
    """
    Get monitoring data for the application
    
    This endpoint:
    1. Collects metrics and system health information
    2. Returns consolidated monitoring data
    
    Requires authentication via JWT Bearer token with admin role.
    """
    try:
        logger.info(f"Fetching monitoring metrics for user {user_id}")
        
        # Ensure user has permission to access monitoring data
        supabase = get_supabase_client()
        user_response = await supabase.table("profiles").select("role").eq("id", user_id).execute()
        
        if not user_response.data or user_response.data[0].get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admins can access monitoring data"
            )
        
        monitoring_service = get_monitoring_service()
        
        # Get time-filtered metrics
        time_range = timedelta(hours=time_range_hours) if time_range_hours else None
        metrics = await monitoring_service.get_metrics(time_range=time_range)
        
        # Get LangSmith metrics
        langsmith_metrics = await monitoring_service.get_langsmith_metrics()
        
        # Get cost projection from cost monitoring service
        cost_monitoring = get_cost_monitoring_service()
        cost_projection = await cost_monitoring.get_cost_projection()
        
        # Get system health
        system_health = await monitoring_service.get_system_health()
        
        return MonitoringDataResponse(
            metrics=metrics,
            langsmith_metrics=langsmith_metrics,
            cost_projection=cost_projection,
            system_health=system_health
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"Failed to fetch monitoring data: {e}")
        sentry_sdk.capture_exception(e)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch monitoring data: {str(e)}"
        )


@app.get("/alerts", tags=["Monitoring"])
async def get_alerts(
    user_id: str = Depends(get_current_user),
    resolved: Optional[bool] = None,
    severity: Optional[str] = None
):
    """
    Get system alerts
    
    This endpoint:
    1. Retrieves alerts from the alerting service
    2. Filters by resolved status and severity
    
    Requires authentication via JWT Bearer token with admin role.
    """
    try:
        # Ensure user has permission to access alerts
        supabase = get_supabase_client()
        user_response = await supabase.table("profiles").select("role").eq("id", user_id).execute()
        
        if not user_response.data or user_response.data[0].get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admins can access alerts"
            )
        
        alerting_service = get_alerting_service()
        alerts = await alerting_service.get_alerts(severity=severity, resolved=resolved)
        
        return {"alerts": alerts}
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"Failed to fetch alerts: {e}")
        sentry_sdk.capture_exception(e)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch alerts: {str(e)}"
        )


@app.post("/alerts/{alert_id}/resolve", tags=["Monitoring"])
async def resolve_alert(
    alert_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Resolve an alert by ID
    
    This endpoint:
    1. Takes an alert ID
    2. Marks the alert as resolved
    3. Returns the updated alert
    
    Requires authentication via JWT Bearer token with admin role.
    """
    try:
        # Ensure user has permission to manage alerts
        supabase = get_supabase_client()
        user_response = await supabase.table("profiles").select("role").eq("id", user_id).execute()
        
        if not user_response.data or user_response.data[0].get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admins can manage alerts"
            )
        
        alerting_service = get_alerting_service()
        alert = await alerting_service.resolve_alert(alert_id)
        
        return {"status": "success", "alert": alert}
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"Failed to resolve alert: {e}")
        sentry_sdk.capture_exception(e)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve alert: {str(e)}"
        )


@app.get("/cost-projection", tags=["Monitoring"])
async def get_cost_projection(
    user_id: str = Depends(get_current_user)
):
    """
    Get cost projection for LLM usage
    
    This endpoint:
    1. Calculates current token usage and projected cost
    2. Returns cost metrics for monitoring
    
    Requires authentication via JWT Bearer token with admin role.
    """
    try:
        # Ensure user has permission to access cost data
        supabase = get_supabase_client()
        user_response = await supabase.table("profiles").select("role").eq("id", user_id).execute()
        
        if not user_response.data or user_response.data[0].get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admins can access cost projection data"
            )
        
        cost_monitoring = get_cost_monitoring_service()
        cost_projection = await cost_monitoring.get_cost_projection()
        
        return cost_projection
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"Failed to fetch cost projection: {e}")
        sentry_sdk.capture_exception(e)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch cost projection: {str(e)}"
        )


@app.get("/cost-monthly-summary", tags=["Monitoring"])
async def get_monthly_cost_summary(
    user_id: str = Depends(get_current_user)
):
    """
    Get monthly cost summary for LLM usage
    
    This endpoint:
    1. Retrieves the current month's cost data
    2. Returns detailed breakdown and projections
    
    Requires authentication via JWT Bearer token with admin role.
    """
    try:
        # Ensure user has permission to access cost data
        supabase = get_supabase_client()
        user_response = await supabase.table("profiles").select("role").eq("id", user_id).execute()
        
        if not user_response.data or user_response.data[0].get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only admins can access cost data"
            )
        
        cost_monitoring = get_cost_monitoring_service()
        monthly_summary = await cost_monitoring.get_monthly_summary()
        
        return monthly_summary
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception(f"Failed to fetch monthly cost summary: {e}")
        sentry_sdk.capture_exception(e)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch monthly cost summary: {str(e)}"
        )


@app.get("/results/{evaluation_id}", tags=["Evaluation"])
async def get_evaluation_results(
    evaluation_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get the evaluation results for a specific evaluation
    
    This endpoint:
    1. Takes an evaluation ID
    2. Retrieves the evaluation from the database
    3. Returns the formatted results
    
    Requires authentication via JWT Bearer token.
    """
    try:
        logger.info(f"Results request for evaluation {evaluation_id}")
        
        # Get Supabase client
        supabase = get_supabase_client()
        if not supabase:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Database connection unavailable"
                }
            )
        
        # Get the evaluation record
        response = await supabase.table("evaluations").select("*").eq("id", evaluation_id).execute()
        
        if not response.data:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Evaluation with ID {evaluation_id} not found"
                }
            )
        
        evaluation = response.data[0]
        
        # Check if the evaluation belongs to the current user
        if evaluation["user_id"] != user_id:
            return JSONResponse(
                status_code=403,
                content={
                    "status": "error",
                    "message": "You don't have permission to access this evaluation"
                }
            )
        
        # Return the evaluation results
        return JSONResponse(content=evaluation)
        
    except Exception as e:
        logger.exception(f"Error getting evaluation results: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting evaluation results: {str(e)}"
        )


@app.post("/upload", tags=["Evaluation"], status_code=202)
async def upload_transcript(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    candidate_name: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """
    Upload an interview transcript for evaluation
    
    This endpoint:
    1. Validates the uploaded file
    2. Saves it to a temporary location
    3. Creates an interview record in Supabase
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
        
        # Create an interview record
        interview_id = str(uuid.uuid4())
        
        interview_data = {
            "id": interview_id,
            "user_id": user_id,
            "candidate_name": candidate_name,
            "interview_date": datetime.now().isoformat(),
            "transcript_storage_path": file_path,
            "status": InterviewStatus.UPLOADED.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # Create the record in Supabase
        supabase = get_supabase_client()
        response = await supabase.table("interviews").insert(interview_data).execute()
        
        if response.data:
            logger.info(f"Interview record created in Supabase with ID: {interview_id}")
        
        # Start a background task to process the transcript
        background_tasks.add_task(process_interview_transcript, file_path, interview_id, user_id)
        
        # Start monitoring the process
        monitoring = get_monitoring_service()
        await monitoring.record_metric("upload_count", 1)
        
        # Return response
        return JSONResponse(
            content={
                "message": "Transcript uploaded successfully, processing started",
                "interview_id": interview_id,
                "candidate_name": candidate_name,
                "filename": file.filename,
                "status": InterviewStatus.UPLOADED.value
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Log the error and return a generic error response
        logger.error(f"Error processing transcript upload: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)
        
        # Record error in monitoring
        monitoring = get_monitoring_service()
        await monitoring.record_metric("error_count", 1)
        
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the transcript"
        )


# API documentation and web page with Vercel Analytics
@app.get("/", tags=["General"])
async def root():
    """
    Root endpoint that returns a simple HTML page with documentation links
    """
    # Create a simple HTML page with Vercel Analytics script
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Interview Evaluator API</title>
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
            }
            a {
                color: #0070f3;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .container {
                background-color: #f7f7f7;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Interview Evaluator API</h1>
        <p>Welcome to the Interview Evaluator API service. This API provides endpoints for evaluating data scientist interview transcripts.</p>
        
        <div class="container">
            <h2>API Documentation</h2>
            <p>For complete API documentation and interactive testing, visit:</p>
            <ul>
                <li><a href="/docs">Swagger UI Documentation</a></li>
                <li><a href="/redoc">ReDoc Documentation</a></li>
            </ul>
            
            <h2>Health Check</h2>
            <p>To check the API health status, visit:</p>
            <ul>
                <li><a href="/health">Health Check Endpoint</a></li>
            </ul>
        </div>
        
        <!-- Vercel Web Analytics -->
        <script>
        window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
        </script>
        <script defer src="/_vercel/insights/script.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Interview Evaluator API...")
    # Use port 8000 as specified in custom instructions
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)