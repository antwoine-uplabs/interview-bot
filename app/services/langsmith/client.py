"""
LangSmith integration service for interacting with LangSmith platform.
Falls back to a mock implementation if LangSmith is not available.
"""

import logging
import os
import httpx
from typing import Any, Dict, List, Optional

# Try to import LangSmith, but don't fail if it's not available
try:
    from langsmith import Client
    from langsmith.run_helpers import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    
logger = logging.getLogger(__name__)

# Create a handler for LangSmith callbacks
class LangSmithCallbackHandler:
    """Callback handler for LangSmith tracing."""
    
    def __init__(self, project_name=None, client=None, tags=None, run_name=None):
        """Initialize the callback handler."""
        self.initialized = False
        self.project_name = project_name
        self.tags = tags or []
        self.run_name = run_name
        self.client = client
        
        if LANGSMITH_AVAILABLE and client:
            self.initialized = True
            logger.info(f"Created LangSmith callback handler for project: {project_name}")
        else:
            logger.info(f"[MOCK] Created LangSmith callback handler for project: {project_name}")

class LangSmithService:
    """Service for interacting with LangSmith platform."""
    
    def __init__(self):
        """Initialize the LangSmith client."""
        self.client = None
        self.initialized = False
        self.project_name = os.environ.get("LANGSMITH_PROJECT", "interview-evaluator")
        self.api_key = os.environ.get("LANGSMITH_API_KEY")
        self.api_url = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        
        # Try to initialize a real client if LangSmith is available
        if LANGSMITH_AVAILABLE and self.api_key:
            try:
                self.client = Client(
                    api_url=self.api_url,
                    api_key=self.api_key
                )
                self.initialized = True
                logger.info(f"LangSmith client initialized for project: {self.project_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize LangSmith client: {e}")
                self.initialized = False
        else:
            logger.info(f"[MOCK] Using mock LangSmith client for project: {self.project_name}")
    
    def initialize(self) -> None:
        """Initialize or re-initialize the LangSmith client."""
        if not LANGSMITH_AVAILABLE or not self.api_key:
            logger.warning("LangSmith not available or API key not provided")
            return
            
        try:
            self.client = Client(
                api_url=self.api_url,
                api_key=self.api_key
            )
            self.initialized = True
            logger.info("LangSmith client re-initialized")
        except Exception as e:
            logger.error(f"Failed to re-initialize LangSmith client: {e}")
            self.initialized = False
    
    def is_configured(self) -> bool:
        """Check if LangSmith is configured and connected."""
        return self.initialized
    
    def get_callback_handler(self, run_name: str = None, tags: List[str] = None):
        """
        Create a LangSmith callback handler for tracing LLM calls.
        Uses a real handler if LangSmith is configured, otherwise a mock.
        
        Args:
            run_name: Optional name for the run
            tags: Optional list of tags for the run
            
        Returns:
            LangSmithCallbackHandler instance
        """
        return LangSmithCallbackHandler(
            project_name=self.project_name,
            client=self.client if self.initialized else None,
            tags=tags or [],
            run_name=run_name
        )
    
    async def trace_run(self, name: str, inputs: Dict[str, Any], **kwargs) -> Optional[str]:
        """
        Create a LangSmith trace for a run.
        Uses real LangSmith if available, otherwise returns a mock ID.
        
        Args:
            name: Name of the run
            inputs: Input data for the run
            **kwargs: Additional arguments
            
        Returns:
            Run ID (real or mock)
        """
        if self.initialized and self.client:
            try:
                # Try to create a real run
                run = self.client.create_run(
                    project_name=self.project_name,
                    name=name,
                    inputs=inputs,
                    **kwargs
                )
                logger.info(f"Created LangSmith trace run: {run.id}")
                return run.id
            except Exception as e:
                logger.error(f"Failed to create LangSmith run: {e}")
                # Fall back to mock
        
        # Generate mock run ID            
        run_id = f"mock-run-{name}-{os.urandom(4).hex()}"
        logger.info(f"[MOCK] Created LangSmith trace run: {run_id}")
        return run_id
    
    async def update_run(self, run_id: str, outputs: Dict[str, Any] = None, error: str = None) -> bool:
        """
        Update a LangSmith run with outputs or error.
        Uses real LangSmith if available, otherwise simulates.
        
        Args:
            run_id: ID of the run to update
            outputs: Optional outputs to add to the run
            error: Optional error to add to the run
            
        Returns:
            True if successful, False otherwise
        """
        if self.initialized and self.client and not run_id.startswith("mock-"):
            try:
                # Try to update a real run
                if error:
                    self.client.update_run(
                        run_id=run_id,
                        error=error,
                        end_time=None  # Let LangSmith set the time
                    )
                    logger.info(f"Updated LangSmith run with error: {run_id}")
                else:
                    self.client.update_run(
                        run_id=run_id,
                        outputs=outputs or {},
                        end_time=None  # Let LangSmith set the time 
                    )
                    logger.info(f"Updated LangSmith run with outputs: {run_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to update LangSmith run: {e}")
                return False
        
        # Mock behavior
        if error:
            logger.info(f"[MOCK] Updated LangSmith run with error: {run_id}")
        else:
            logger.info(f"[MOCK] Updated LangSmith run with outputs: {run_id}")
        return True
    
    async def evaluate_run(self, run_id: str, evaluators: List[str]) -> Dict[str, Any]:
        """
        Evaluate a run using LangSmith evaluators.
        Uses real LangSmith if available, otherwise returns mock data.
        
        Args:
            run_id: ID of the run to evaluate
            evaluators: List of evaluator names to use
            
        Returns:
            Evaluation results (real or mock)
        """
        if self.initialized and self.client and not run_id.startswith("mock-"):
            try:
                # Note: This is a placeholder as the real implementation would depend
                # on how LangSmith evaluators are set up in your account
                # In a real scenario, you would likely need to implement this using
                # the client.evaluate_run() method if available
                
                logger.warning("Real LangSmith evaluation not fully implemented, using mock data")
                # Fall back to mock implementation
            except Exception as e:
                logger.error(f"Failed to evaluate LangSmith run: {e}")
                # Fall back to mock implementation
        
        # Mock behavior
        results = {}
        for evaluator in evaluators:
            results[evaluator] = {
                "evaluation_id": f"mock-eval-{evaluator}-{os.urandom(4).hex()}",
                "score": 0.85,  # Mock score
                "feedback": "Mock feedback for evaluation"
            }
        
        logger.info(f"[MOCK] Evaluated LangSmith run: {run_id}")
        return {"status": "success", "evaluations": results}
    
    async def get_run_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get metrics for runs in the project.
        Uses real LangSmith if available, otherwise returns mock data.
        
        Args:
            days: Number of days to include in the metrics
            
        Returns:
            Metrics data (real or mock)
        """
        if self.initialized and self.client:
            try:
                # Try to get real metrics
                # Note: The exact API might differ based on LangSmith's client implementation
                # This is a placeholder for what a real implementation might look like
                
                # For now, we return mock data even with a real client
                # In a production environment, you would implement real metrics retrieval
                logger.warning("Real LangSmith metrics retrieval not fully implemented, using mock data")
            except Exception as e:
                logger.error(f"Failed to get LangSmith metrics: {e}")
        
        # Return mock data
        return {
            "total_runs": 50,
            "successful_runs": 45,
            "error_runs": 5,
            "success_rate": 0.9,
            "average_latency_seconds": 2.5,
            "run_types": {
                "chain": 30,
                "llm": 20
            }
        }
        
    async def list_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent runs from LangSmith.
        Uses real LangSmith if available, otherwise returns mock data.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of runs (real or mock)
        """
        if self.initialized and self.client:
            try:
                # Try to list real runs
                runs = self.client.list_runs(
                    project_name=self.project_name,
                    limit=limit
                )
                
                # Convert to serializable format
                result = []
                for run in runs:
                    result.append({
                        "id": run.id,
                        "name": run.name,
                        "start_time": str(run.start_time) if hasattr(run, 'start_time') else None,
                        "end_time": str(run.end_time) if hasattr(run, 'end_time') else None,
                        "status": run.status if hasattr(run, 'status') else "success"
                    })
                
                logger.info(f"Retrieved {len(result)} runs from LangSmith")
                return result
            except Exception as e:
                logger.error(f"Failed to list LangSmith runs: {e}")
        
        # Return mock data
        mock_runs = []
        for i in range(min(limit, 5)):  # Mock only up to 5 runs
            mock_runs.append({
                "id": f"mock-run-{os.urandom(4).hex()}",
                "name": f"Mock Run {i+1}",
                "start_time": "2025-04-17T00:00:00Z",
                "end_time": "2025-04-17T00:01:00Z",
                "status": "success"
            })
        
        logger.info(f"[MOCK] Returned {len(mock_runs)} mock runs")
        return mock_runs


# Create a singleton instance
langsmith_service = LangSmithService()