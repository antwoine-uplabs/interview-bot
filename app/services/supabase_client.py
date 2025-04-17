import os
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# This is a mock SupabaseService for local development with LangGraph
class SupabaseService:
    """Mock service for interacting with Supabase during development"""
    
    def __init__(self):
        """Initialize the mock Supabase client"""
        self.initialized = True
        logger.info("Mock Supabase client initialized for development")
    
    def is_connected(self) -> bool:
        """Check if the mock Supabase client is connected"""
        return self.initialized
        
    def store_evaluation_results(self, interview_id: str, results: Dict[str, Any]) -> bool:
        """Mock storing evaluation results"""
        if not self.initialized:
            logger.error("Cannot store evaluation results: Mock client not initialized")
            return False
        
        try:
            # Log the results instead of storing them
            logger.info(f"[MOCK] Storing evaluation results for interview {interview_id}")
            logger.info(f"[MOCK] Results: {json.dumps(results)[:200]}...")
            
            # Mock successful storage
            return True
        except Exception as e:
            logger.error(f"Error in mock store_evaluation_results: {e}", exc_info=True)
            return False
    
    def create_interview(self, interview_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock creating a new interview record"""
        if not self.initialized:
            return None
            
        try:
            # Generate a mock ID
            interview_id = f"mock-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"[MOCK] Interview created with ID: {interview_id}")
            
            # Return mock data
            mock_interview = {
                "id": interview_id,
                **interview_data,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            return mock_interview
        except Exception as e:
            logger.error(f"Error in mock create_interview: {e}", exc_info=True)
            return None

    def update_interview_status(self, interview_id: str, status: str) -> bool:
        """Mock updating the status of an interview"""
        if not self.initialized:
            return False
            
        try:
            logger.info(f"[MOCK] Interview {interview_id} status updated to '{status}'")
            return True
        except Exception as e:
            logger.error(f"Error in mock update_interview_status: {e}", exc_info=True)
            return False

    # Add other mock methods as needed for development
    def _store_criteria_evaluations(self, interview_id: str, criteria_evaluations: List[Dict[str, Any]]) -> bool:
        """Mock storing criteria evaluations"""
        logger.info(f"[MOCK] Storing {len(criteria_evaluations)} criteria evaluations for interview {interview_id}")
        return True

# Create a singleton instance
supabase_service = SupabaseService()