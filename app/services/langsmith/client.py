"""
Mock LangSmith integration service for local development with LangGraph.
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Create a mock LangSmithCallbackHandler
class MockLangSmithCallbackHandler:
    """Mock callback handler for LangSmith tracing."""
    
    def __init__(self, project_name=None, client=None, tags=None, run_name=None):
        """Initialize the mock callback handler."""
        self.project_name = project_name
        self.tags = tags or []
        self.run_name = run_name
        logger.info(f"[MOCK] Created LangSmith callback handler for project: {project_name}")

class LangSmithService:
    """Mock service for interacting with LangSmith platform."""
    
    def __init__(self):
        """Initialize the mock LangSmith client."""
        self.client = None
        self.project_name = os.environ.get("LANGSMITH_PROJECT", "interview-evaluator")
        self.api_key = os.environ.get("LANGSMITH_API_KEY")
        self.api_url = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        self.is_connected = True  # Always set to True for the mock
        logger.info(f"[MOCK] LangSmith client initialized for project: {self.project_name}")
    
    def initialize(self) -> None:
        """Initialize the mock LangSmith client."""
        # Nothing to do for the mock
        pass
    
    def is_configured(self) -> bool:
        """Check if LangSmith is configured and connected."""
        return self.is_connected
    
    def get_callback_handler(self, run_name: str = None, tags: List[str] = None):
        """
        Create a mock LangSmith callback handler for tracing LLM calls.
        
        Args:
            run_name: Optional name for the run
            tags: Optional list of tags for the run
            
        Returns:
            MockLangSmithCallbackHandler instance
        """
        return MockLangSmithCallbackHandler(
            project_name=self.project_name,
            tags=tags or [],
            run_name=run_name
        )
    
    def trace_run(self, name: str, inputs: Dict[str, Any], **kwargs) -> Optional[str]:
        """
        Create a mock LangSmith trace for a run.
        
        Args:
            name: Name of the run
            inputs: Input data for the run
            **kwargs: Additional arguments
            
        Returns:
            Mock run ID
        """
        run_id = f"mock-run-{name}-{os.urandom(4).hex()}"
        logger.info(f"[MOCK] Created LangSmith trace run: {run_id}")
        return run_id
    
    def update_run(self, run_id: str, outputs: Dict[str, Any] = None, error: str = None) -> bool:
        """
        Update a mock LangSmith run with outputs or error.
        
        Args:
            run_id: ID of the run to update
            outputs: Optional outputs to add to the run
            error: Optional error to add to the run
            
        Returns:
            True if successful, False otherwise
        """
        if error:
            logger.info(f"[MOCK] Updated LangSmith run with error: {run_id}")
        else:
            logger.info(f"[MOCK] Updated LangSmith run with outputs: {run_id}")
        return True
    
    def evaluate_run(self, run_id: str, evaluators: List[str]) -> Dict[str, Any]:
        """
        Evaluate a run using mock LangSmith evaluators.
        
        Args:
            run_id: ID of the run to evaluate
            evaluators: List of evaluator names to use
            
        Returns:
            Mock evaluation results
        """
        results = {}
        for evaluator in evaluators:
            results[evaluator] = {
                "evaluation_id": f"mock-eval-{evaluator}-{os.urandom(4).hex()}",
                "score": 0.85,  # Mock score
                "feedback": "Mock feedback for evaluation"
            }
        
        logger.info(f"[MOCK] Evaluated LangSmith run: {run_id}")
        return {"status": "success", "evaluations": results}
    
    def get_run_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get mock metrics for runs in the project.
        
        Args:
            days: Number of days to include in the metrics
            
        Returns:
            Mock metrics data
        """
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


# Create a singleton instance
langsmith_service = LangSmithService()