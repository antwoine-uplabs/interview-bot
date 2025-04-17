"""
LangSmith integration service for the Interview Evaluator.

This module provides functions for interacting with LangSmith for
tracing, monitoring, and evaluation of LangGraph agents.
"""

import logging
import os
import json
from typing import Any, Dict, List, Optional

from langsmith import Client
import langsmith
from langchain_community.callbacks.langsmith import LangSmithCallbackHandler

logger = logging.getLogger(__name__)

class LangSmithService:
    """Service for interacting with LangSmith platform."""
    
    def __init__(self):
        """Initialize the LangSmith client."""
        self.client = None
        self.project_name = os.environ.get("LANGSMITH_PROJECT", "interview-evaluator")
        self.api_key = os.environ.get("LANGSMITH_API_KEY")
        self.api_url = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        self.is_connected = False
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize the LangSmith client."""
        try:
            # Check for required environment variables
            if not self.api_key:
                logger.warning("LANGSMITH_API_KEY not found in environment. LangSmith tracing disabled.")
                return
            
            # Initialize the client
            self.client = Client(
                api_key=self.api_key,
                api_url=self.api_url
            )
            
            # Test connection by listing projects
            self.client.list_projects()
            self.is_connected = True
            
            # Enable tracing
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = self.project_name
            
            logger.info(f"LangSmith client initialized and connected to project: {self.project_name}")
            
        except Exception as e:
            logger.error(f"Error initializing LangSmith client: {e}", exc_info=True)
    
    def is_configured(self) -> bool:
        """Check if LangSmith is configured and connected."""
        return self.is_connected
    
    def get_callback_handler(self, run_name: str = None, tags: List[str] = None) -> LangSmithCallbackHandler:
        """
        Create a LangSmith callback handler for tracing LLM calls.
        
        Args:
            run_name: Optional name for the run
            tags: Optional list of tags for the run
            
        Returns:
            LangSmithCallbackHandler instance
        """
        if not self.is_connected:
            logger.debug("LangSmith client not connected. Callback handler unavailable.")
            return None
        
        try:
            return LangSmithCallbackHandler(
                project_name=self.project_name,
                client=self.client,
                tags=tags or [],
                run_name=run_name
            )
        except Exception as e:
            logger.error(f"Error creating LangSmith callback handler: {e}", exc_info=True)
            return None
    
    def trace_run(self, name: str, inputs: Dict[str, Any], **kwargs) -> Optional[str]:
        """
        Create a LangSmith trace for a run.
        
        Args:
            name: Name of the run
            inputs: Input data for the run
            **kwargs: Additional arguments to pass to the LangSmith client
            
        Returns:
            Run ID if successful, None otherwise
        """
        if not self.is_connected:
            logger.debug("LangSmith client not connected. Tracing disabled.")
            return None
        
        try:
            # Create a new run
            run = self.client.create_run(
                name=name,
                inputs=inputs,
                run_type="chain",
                project_name=self.project_name,
                **kwargs
            )
            
            logger.info(f"Created LangSmith trace run: {run.id}")
            return run.id
            
        except Exception as e:
            logger.error(f"Error tracing run in LangSmith: {e}", exc_info=True)
            return None
    
    def update_run(self, run_id: str, outputs: Dict[str, Any] = None, error: str = None) -> bool:
        """
        Update a LangSmith run with outputs or error.
        
        Args:
            run_id: ID of the run to update
            outputs: Optional outputs to add to the run
            error: Optional error to add to the run
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            logger.debug("LangSmith client not connected. Run update disabled.")
            return False
        
        try:
            if error:
                self.client.update_run(
                    run_id=run_id,
                    error=error,
                    end_time=langsmith.utils.get_current_time()
                )
            elif outputs:
                self.client.update_run(
                    run_id=run_id,
                    outputs=outputs,
                    end_time=langsmith.utils.get_current_time()
                )
            
            logger.info(f"Updated LangSmith run: {run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating run in LangSmith: {e}", exc_info=True)
            return False
    
    def evaluate_run(self, run_id: str, evaluators: List[str]) -> Dict[str, Any]:
        """
        Evaluate a run using LangSmith evaluators.
        
        Args:
            run_id: ID of the run to evaluate
            evaluators: List of evaluator names to use
            
        Returns:
            Evaluation results
        """
        if not self.is_connected:
            logger.debug("LangSmith client not connected. Evaluation disabled.")
            return {"error": "LangSmith client not connected"}
        
        try:
            results = {}
            for evaluator in evaluators:
                # Create an evaluation
                evaluation = self.client.create_evaluation(
                    run_id=run_id,
                    evaluator=evaluator
                )
                results[evaluator] = {
                    "evaluation_id": evaluation.id,
                    "score": evaluation.score,
                    "feedback": evaluation.feedback
                }
            
            logger.info(f"Evaluated LangSmith run: {run_id}")
            return {"status": "success", "evaluations": results}
            
        except Exception as e:
            logger.error(f"Error evaluating run in LangSmith: {e}", exc_info=True)
            return {"error": str(e)}
    
    def get_run_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get metrics for runs in the project.
        
        Args:
            days: Number of days to include in the metrics
            
        Returns:
            Metrics data
        """
        if not self.is_connected:
            logger.debug("LangSmith client not connected. Metrics unavailable.")
            return {"error": "LangSmith client not connected"}
        
        try:
            # Get runs for the specified time period
            runs = self.client.list_runs(
                project_name=self.project_name,
                start_time=langsmith.utils.get_time_from_days_ago(days)
            )
            
            # Calculate metrics
            total_runs = len(runs)
            successful_runs = sum(1 for run in runs if run.error is None)
            error_runs = total_runs - successful_runs
            
            # Calculate average latencies
            latencies = [run.end_time - run.start_time for run in runs if run.end_time and run.start_time]
            avg_latency = sum(latencies, 0.0) / len(latencies) if latencies else 0
            
            # Count runs by type
            run_types = {}
            for run in runs:
                run_type = run.run_type or "unknown"
                run_types[run_type] = run_types.get(run_type, 0) + 1
            
            return {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "error_runs": error_runs,
                "success_rate": successful_runs / total_runs if total_runs > 0 else 0,
                "average_latency_seconds": avg_latency,
                "run_types": run_types
            }
            
        except Exception as e:
            logger.error(f"Error getting run metrics from LangSmith: {e}", exc_info=True)
            return {"error": str(e)}


# Create a singleton instance
langsmith_service = LangSmithService()