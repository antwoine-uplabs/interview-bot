"""
Data models for the Interview Evaluator.

This module defines the Pydantic models used for request and response validation.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr


class InterviewStatus(str, Enum):
    """Constants for interview status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EVALUATED = "evaluated"
    ERROR = "error"


class SystemStatus(str, Enum):
    """Status of a service or system."""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"


class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str


class UserSignUp(BaseModel):
    """User signup request model"""
    email: EmailStr
    password: str
    name: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response model"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    expires_in: int


class EvaluationCriterion(BaseModel):
    """Model for an evaluation criterion"""
    name: str
    score: float
    justification: str
    supporting_quotes: List[str] = []


class EvaluationSummary(BaseModel):
    """Model for evaluation summary"""
    overall_score: float
    summary: str
    strengths: List[str] = []
    weaknesses: List[str] = []


class EvaluationResponse(BaseModel):
    """Model for evaluation response"""
    status: str
    interview_id: Optional[str] = None
    candidate_name: Optional[str] = None
    overall_score: Optional[float] = None
    summary: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    criteria_evaluations: Optional[List[EvaluationCriterion]] = None
    error: Optional[str] = None


class EvaluationRequest(BaseModel):
    """Request model for evaluation endpoint."""
    interview_id: str
    candidate_name: str
    transcript_path: Optional[str] = None


class MetricValue(BaseModel):
    """Model for a metric value with timestamp."""
    timestamp: datetime
    value: Union[int, float, str, bool]


class Metric(BaseModel):
    """Model for a metric with name, description, and values."""
    name: str
    description: str
    unit: Optional[str] = None
    values: List[MetricValue]


class Alert(BaseModel):
    """Model for an alert."""
    id: str
    timestamp: datetime
    level: str
    message: str
    source: str
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertRule(BaseModel):
    """Alert rule configuration."""
    id: str
    name: str
    description: str
    metric: str
    threshold: float
    comparison: str = Field(..., description="gt, lt, eq, gte, lte")
    severity: str
    enabled: bool = True


class MonitoringDataResponse(BaseModel):
    """Response model for monitoring data endpoint."""
    metrics: Dict[str, Metric]
    langsmith_metrics: Dict[str, Any]
    cost_projection: Dict[str, Any]
    system_health: Dict[str, Any]


class CostProjectionResponse(BaseModel):
    """Response model for cost projection endpoint."""
    current_usage_tokens: int
    projected_monthly_tokens: int
    projected_monthly_cost_usd: float


class DailyCostRecord(BaseModel):
    """Model for a daily cost record."""
    date: datetime
    input_tokens: int
    output_tokens: int
    cost: float
    model_breakdown: Dict[str, float]


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    api_version: str
    timestamp: str
    supabase_status: SystemStatus
    langsmith_status: SystemStatus