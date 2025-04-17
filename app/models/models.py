"""
Data models for the Interview Evaluator.

This module defines the Pydantic models used for request and response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class InterviewStatus:
    """Constants for interview status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EVALUATED = "evaluated"
    ERROR = "error"


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
    interview_id: str
    candidate_name: str
    overall_score: Optional[float] = None
    summary: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    criteria_evaluations: Optional[List[EvaluationCriterion]] = None
    error: Optional[str] = None