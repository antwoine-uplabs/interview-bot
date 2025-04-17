import os
import logging
import json
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for interacting with Supabase"""
    
    def __init__(self):
        """Initialize the Supabase client"""
        self.client: Optional[Client] = None
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize the Supabase client"""
        try:
            # Make sure we load the environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            supabase_url = os.environ.get("SUPABASE_URL")
            # For server-side operations, prefer the service role key
            supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                logger.warning("Supabase URL or Key not found in environment variables")
                return
                
            self.client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized with %s key", 
                       "service role" if supabase_key == os.environ.get("SUPABASE_SERVICE_ROLE_KEY") else "regular")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}", exc_info=True)
    
    def is_connected(self) -> bool:
        """Check if the Supabase client is connected"""
        return self.client is not None
        
    def sign_up_user(self, email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Sign up a new user
        
        Args:
            email: User email
            password: User password
            user_metadata: Additional user metadata (optional)
            
        Returns:
            Auth response data if successful, None otherwise
        """
        if not self.is_connected():
            logger.error("Cannot sign up user: Supabase client not initialized")
            return None
            
        try:
            # Create user in Supabase Auth
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                } if user_metadata else {}
            })
            
            if auth_response.user and auth_response.session:
                logger.info(f"User created: {auth_response.user.id}")
                
                # Format the response
                return {
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "expires_in": auth_response.session.expires_in,
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email
                    }
                }
            else:
                logger.error("User signup failed: No user or session returned")
                return None
                
        except Exception as e:
            logger.error(f"Error signing up user: {e}", exc_info=True)
            return None
    
    def sign_in_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Sign in an existing user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Auth response data if successful, None otherwise
        """
        if not self.is_connected():
            logger.error("Cannot sign in user: Supabase client not initialized")
            return None
            
        try:
            # Sign in user with Supabase Auth
            auth_response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user and auth_response.session:
                logger.info(f"User signed in: {auth_response.user.id}")
                
                # Format the response
                return {
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "expires_in": auth_response.session.expires_in,
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email
                    }
                }
            else:
                logger.error("User signin failed: No user or session returned")
                return None
                
        except Exception as e:
            logger.error(f"Error signing in user: {e}", exc_info=True)
            return None
    
    def create_interview(self, interview_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new interview record in Supabase"""
        if not self.is_connected():
            logger.error("Cannot create interview: Supabase client not initialized")
            return None
            
        try:
            result = self.client.table('interviews').insert(interview_data).execute()
            if len(result.data) > 0:
                logger.info(f"Interview created with ID: {result.data[0]['id']}")
                return result.data[0]
            else:
                logger.error("Interview creation failed: No data returned")
                return None
        except Exception as e:
            logger.error(f"Error creating interview in Supabase: {e}", exc_info=True)
            return None
    
    def get_interview(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """Get an interview record from Supabase"""
        if not self.is_connected():
            logger.error("Cannot get interview: Supabase client not initialized")
            return None
            
        try:
            result = self.client.table('interviews').select('*').eq('id', interview_id).execute()
            if len(result.data) > 0:
                return result.data[0]
            else:
                logger.error(f"Interview with ID {interview_id} not found")
                return None
        except Exception as e:
            logger.error(f"Error retrieving interview from Supabase: {e}", exc_info=True)
            return None
    
    def update_interview_status(self, interview_id: str, status: str) -> bool:
        """Update the status of an interview"""
        if not self.is_connected():
            logger.error("Cannot update interview: Supabase client not initialized")
            return False
            
        try:
            result = self.client.table('interviews').update({'status': status}).eq('id', interview_id).execute()
            if len(result.data) > 0:
                logger.info(f"Interview {interview_id} status updated to '{status}'")
                return True
            else:
                logger.error(f"Failed to update status for interview {interview_id}")
                return False
        except Exception as e:
            logger.error(f"Error updating interview status in Supabase: {e}", exc_info=True)
            return False
    
    def store_evaluation_results(self, interview_id: str, results: Dict[str, Any]) -> bool:
        """
        Store evaluation results in Supabase
        
        Args:
            interview_id: The ID of the interview
            results: The evaluation results to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot store evaluation results: Supabase client not initialized")
            return False
        
        try:
            # First, ensure the evaluation_results table exists by creating it if needed
            self._ensure_evaluation_results_table()
            
            # Prepare the evaluation results data
            evaluation_data = {
                "interview_id": interview_id,
                "overall_score": results.get("overall_score"),
                "summary": results.get("summary"),
                "strengths": json.dumps(results.get("strengths", [])),
                "weaknesses": json.dumps(results.get("weaknesses", [])),
                "result_data": json.dumps(results),
                "created_at": datetime.now().isoformat(),
            }
            
            # Insert the evaluation results
            result = self.client.table('evaluation_results').insert(evaluation_data).execute()
            
            if len(result.data) > 0:
                logger.info(f"Stored evaluation results for interview {interview_id}")
                
                # Also store individual criteria evaluations if present
                if "criteria_evaluations" in results and isinstance(results["criteria_evaluations"], list):
                    self._store_criteria_evaluations(interview_id, results["criteria_evaluations"])
                
                return True
            else:
                logger.error(f"Failed to store evaluation results for interview {interview_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing evaluation results in Supabase: {e}", exc_info=True)
            return False
    
    def _store_criteria_evaluations(self, interview_id: str, criteria_evaluations: List[Dict[str, Any]]) -> bool:
        """
        Store individual criteria evaluations in Supabase
        
        Args:
            interview_id: The ID of the interview
            criteria_evaluations: List of criteria evaluation results
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
            
        try:
            # Ensure the criteria_evaluations table exists
            self._ensure_criteria_evaluations_table()
            
            # Prepare the data for insertion
            criteria_data = []
            for eval_item in criteria_evaluations:
                criteria_data.append({
                    "interview_id": interview_id,
                    "criterion_name": eval_item.get("criterion", ""),
                    "score": eval_item.get("score", 0),
                    "justification": eval_item.get("justification", ""),
                    "supporting_quotes": json.dumps(eval_item.get("supporting_quotes", [])),
                    "created_at": datetime.now().isoformat(),
                })
            
            # Insert the criteria evaluations
            if criteria_data:
                result = self.client.table('criteria_evaluations').insert(criteria_data).execute()
                if len(result.data) > 0:
                    logger.info(f"Stored {len(criteria_data)} criteria evaluations for interview {interview_id}")
                    return True
                else:
                    logger.error(f"Failed to store criteria evaluations for interview {interview_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing criteria evaluations in Supabase: {e}", exc_info=True)
            return False
    
    def get_all_evaluations(self, user_id: str, limit: int = 20, offset: int = 0) -> Optional[List[Dict[str, Any]]]:
        """
        Get all evaluations for a user
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List of evaluation results if found, None otherwise
        """
        if not self.is_connected():
            logger.error("Cannot get evaluations: Supabase client not initialized")
            return None
            
        try:
            # Get all evaluated interviews for the user
            interviews_query = self.client.table('interviews') \
                .select('id, candidate_name, status, created_at, updated_at') \
                .eq('user_id', user_id) \
                .eq('status', 'evaluated') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .offset(offset)
            
            interviews_result = interviews_query.execute()
            
            if len(interviews_result.data) == 0:
                logger.info(f"No evaluated interviews found for user {user_id}")
                return []
            
            # Get evaluation results for all interviews
            all_evaluations = []
            for interview in interviews_result.data:
                interview_id = interview['id']
                # Get the full evaluation result
                eval_result = self.get_evaluation_results(interview_id)
                if eval_result:
                    all_evaluations.append(eval_result)
            
            return all_evaluations
            
        except Exception as e:
            logger.error(f"Error retrieving evaluations from Supabase: {e}", exc_info=True)
            return None
    
    def get_evaluation_results(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """
        Get evaluation results for an interview
        
        Args:
            interview_id: The ID of the interview
            
        Returns:
            The evaluation results if found, None otherwise
        """
        if not self.is_connected():
            logger.error("Cannot get evaluation results: Supabase client not initialized")
            return None
            
        try:
            # Get the evaluation results
            eval_result = self.client.table('evaluation_results').select('*').eq('interview_id', interview_id).execute()
            
            if len(eval_result.data) == 0:
                logger.warning(f"No evaluation results found for interview {interview_id}")
                return None
                
            # Get the criteria evaluations
            criteria_result = self.client.table('criteria_evaluations').select('*').eq('interview_id', interview_id).execute()
            
            # Build the response
            result_data = eval_result.data[0]
            
            # Parse JSON fields
            try:
                result_data["strengths"] = json.loads(result_data.get("strengths", "[]"))
                result_data["weaknesses"] = json.loads(result_data.get("weaknesses", "[]"))
                
                # Add the full result data if available
                if "result_data" in result_data and result_data["result_data"]:
                    full_data = json.loads(result_data["result_data"])
                    # Remove fields we've already extracted
                    for key in ["overall_score", "summary", "strengths", "weaknesses"]:
                        if key in full_data:
                            del full_data[key]
                    # Add any remaining fields
                    for key, value in full_data.items():
                        if key not in result_data:
                            result_data[key] = value
                
                # Remove the raw JSON data from the response
                if "result_data" in result_data:
                    del result_data["result_data"]
            except json.JSONDecodeError:
                logger.warning("Error parsing JSON fields in evaluation results")
            
            # Add the criteria evaluations
            result_data["criteria_evaluations"] = []
            for criterion in criteria_result.data:
                try:
                    # Parse JSON fields
                    supporting_quotes = json.loads(criterion.get("supporting_quotes", "[]"))
                except json.JSONDecodeError:
                    supporting_quotes = []
                
                result_data["criteria_evaluations"].append({
                    "criterion": criterion.get("criterion_name", ""),
                    "score": criterion.get("score", 0),
                    "justification": criterion.get("justification", ""),
                    "supporting_quotes": supporting_quotes
                })
                
            return result_data
            
        except Exception as e:
            logger.error(f"Error retrieving evaluation results from Supabase: {e}", exc_info=True)
            return None
    
    def _ensure_evaluation_results_table(self) -> None:
        """Ensure the evaluation_results table exists in Supabase"""
        # In a real implementation, we would check if the table exists and create it if needed
        # For this implementation, we'll assume the table is created via migrations or manually
        pass
    
    def _ensure_criteria_evaluations_table(self) -> None:
        """Ensure the criteria_evaluations table exists in Supabase"""
        # In a real implementation, we would check if the table exists and create it if needed
        # For this implementation, we'll assume the table is created via migrations or manually
        pass


# Create a singleton instance
supabase_service = SupabaseService()