"""
Authentication service for the Interview Evaluator.

This module provides functions for authenticating API requests using
Supabase JWT tokens.
"""

import os
import logging
import jwt
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthService:
    """Service for authenticating API requests"""

    def __init__(self):
        """Initialize the auth service"""
        self.jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
        if not self.jwt_secret:
            logger.warning("Supabase JWT secret not found in environment variables")
        
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token and return the decoded payload
        
        Args:
            token: The JWT token to verify
            
        Returns:
            The decoded token payload if valid, None otherwise
        """
        if not self.jwt_secret:
            logger.warning("Cannot verify token: JWT secret not configured")
            return None
            
        try:
            # Decode and verify the token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={"verify_signature": True}
            )
            
            return payload
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extract the user ID from a JWT token
        
        Args:
            token: The JWT token
            
        Returns:
            The user ID if found, None otherwise
        """
        payload = self.verify_token(token)
        if not payload:
            return None
            
        # Extract user ID from token payload
        # The structure depends on Supabase JWT format
        user_id = payload.get("sub")
        
        return user_id


# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get the current authenticated user from JWT token
    
    This function is used as a FastAPI dependency to protect routes.
    
    Args:
        credentials: The HTTP Authorization credentials
        
    Returns:
        User information from the token
        
    Raises:
        HTTPException: If the token is invalid or authentication fails
    """
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    # Extract user information from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID not found in token",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    # Return user information
    return {
        "user_id": user_id,
        "email": payload.get("email", ""),
        "role": payload.get("role", "user")
    }


# Create a singleton instance
auth_service = AuthService()