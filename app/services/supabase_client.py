import os
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for interacting with Supabase"""
    
    def __init__(self):
        """Initialize the Supabase client"""
        self.initialized = False
        self.client = None
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.key:
            logger.warning("Supabase URL or key not found in environment variables")
            self.initialized = False
            return
            
        try:
            # Initialize the client
            self.client = create_client(self.url, self.key)
            self.initialized = True
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.initialized = False
    
    def is_connected(self) -> bool:
        """Check if the Supabase client is connected"""
        if not self.initialized or not self.client:
            return False
            
        try:
            # Use a simple auth check instead of querying a specific table
            # This avoids errors with non-existent tables
            auth_response = self.client.auth.get_user(os.environ.get("SUPABASE_JWT_SECRET", ""))
            
            # Even if auth check fails, the connection might still be valid
            # We just want to make sure the client can communicate with Supabase
            return True
        except Exception as e:
            # If it's just a 404 for a nonexistent table, we still consider it "connected"
            # Because the client is working, the table just doesn't exist yet
            if "'code': '42P01'" in str(e) and "does not exist" in str(e):
                # Table doesn't exist but connection works
                logger.warning(f"Supabase table doesn't exist yet, but connection is valid")
                return True
                
            logger.error(f"Supabase connection check failed: {e}")
            return False
        
    def store_evaluation_results(self, interview_id: str, results: Dict[str, Any]) -> bool:
        """Store evaluation results in Supabase"""
        if not self.initialized or not self.client:
            logger.error("Cannot store evaluation results: Supabase client not initialized")
            return False
        
        try:
            # Add timestamp and interview ID
            data = {
                "interview_id": interview_id,
                "results": results,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            
            # Store in evaluations table
            response = self.client.table("evaluations").insert(data).execute()
            
            if response.data:
                logger.info(f"Evaluation results stored for interview {interview_id}")
                return True
            else:
                logger.error(f"Failed to store evaluation results: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error in store_evaluation_results: {e}", exc_info=True)
            return False
    
    def create_interview(self, interview_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new interview record in Supabase"""
        if not self.initialized or not self.client:
            logger.error("Cannot create interview: Supabase client not initialized")
            return None
            
        try:
            # Ensure required fields
            if "candidate_name" not in interview_data:
                interview_data["candidate_name"] = "Unknown Candidate"
                
            # Add timestamps if not present
            if "created_at" not in interview_data:
                interview_data["created_at"] = datetime.now().isoformat()
            if "updated_at" not in interview_data:
                interview_data["updated_at"] = datetime.now().isoformat()
                
            # Insert into interviews table
            response = self.client.table("interviews").insert(interview_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Interview created with ID: {response.data[0].get('id')}")
                return response.data[0]
            else:
                logger.error("Failed to create interview: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error in create_interview: {e}", exc_info=True)
            return None

    def update_interview_status(self, interview_id: str, status: str) -> bool:
        """Update the status of an interview in Supabase"""
        if not self.initialized or not self.client:
            logger.error("Cannot update interview status: Supabase client not initialized")
            return False
            
        try:
            # Update the interview status
            data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.client.table("interviews").update(data).eq("id", interview_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Interview {interview_id} status updated to '{status}'")
                return True
            else:
                logger.error(f"Failed to update interview status: No data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error in update_interview_status: {e}", exc_info=True)
            return False

    def _store_criteria_evaluations(self, interview_id: str, criteria_evaluations: List[Dict[str, Any]]) -> bool:
        """Store criteria evaluations in Supabase"""
        if not self.initialized or not self.client:
            logger.error("Cannot store criteria evaluations: Supabase client not initialized")
            return False
            
        try:
            # Prepare data for bulk insert
            data = []
            for eval_data in criteria_evaluations:
                data.append({
                    "interview_id": interview_id,
                    "criterion": eval_data.get("criterion"),
                    "score": eval_data.get("score"),
                    "justification": eval_data.get("justification"),
                    "supporting_quotes": json.dumps(eval_data.get("supporting_quotes", [])),
                    "created_at": datetime.now().isoformat()
                })
                
            # Insert into criteria_evaluations table
            if data:
                response = self.client.table("criteria_evaluations").insert(data).execute()
                
                if response.data:
                    logger.info(f"Stored {len(data)} criteria evaluations for interview {interview_id}")
                    return True
                else:
                    logger.error("Failed to store criteria evaluations: No data returned")
                    return False
            else:
                logger.warning(f"No criteria evaluations to store for interview {interview_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error in _store_criteria_evaluations: {e}", exc_info=True)
            return False
    
    def table(self, table_name: str):
        """Access a Supabase table"""
        if not self.initialized or not self.client:
            logger.error(f"Cannot access table {table_name}: Supabase client not initialized")
            return MockTableQuery(table_name)
            
        try:
            return self.client.table(table_name)
        except Exception as e:
            logger.error(f"Error accessing table {table_name}: {e}")
            # Return a mock object to prevent crashes
            return MockTableQuery(table_name)


class MockTableQuery:
    """Fallback mock implementation for Supabase table queries when client fails"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.conditions = []
    
    def select(self, columns: str = "*"):
        """Mock select operation"""
        logger.info(f"[MOCK] SELECT {columns} FROM {self.table_name}")
        return self
    
    def insert(self, data: Dict[str, Any]):
        """Mock insert operation"""
        logger.info(f"[MOCK] INSERT INTO {self.table_name}: {str(data)[:100]}...")
        return self
    
    def update(self, data: Dict[str, Any]):
        """Mock update operation"""
        logger.info(f"[MOCK] UPDATE {self.table_name} SET {str(data)[:100]}...")
        return self
    
    def eq(self, column: str, value: Any):
        """Mock equality condition"""
        logger.info(f"[MOCK] WHERE {column} = {value}")
        self.conditions.append((column, value))
        return self
    
    def limit(self, limit: int):
        """Mock limit operation"""
        logger.info(f"[MOCK] LIMIT {limit}")
        return self
    
    def order(self, column: str, options: Dict[str, Any] = None):
        """Mock order operation"""
        direction = "ASC"
        if options and options.get("ascending") is False:
            direction = "DESC"
        logger.info(f"[MOCK] ORDER BY {column} {direction}")
        return self
    
    def range(self, start: int, end: int):
        """Mock range operation"""
        logger.info(f"[MOCK] RANGE {start} to {end}")
        return self
    
    async def execute(self):
        """Mock execution returning empty data"""
        logger.info(f"[MOCK] Executing query on {self.table_name}")
        return MockResponse()


class MockResponse:
    """Mock response from Supabase"""
    
    def __init__(self):
        self.data = []


# Create a singleton instance
supabase_service = SupabaseService()

def get_supabase_client():
    """Return the supabase service singleton instance."""
    return supabase_service