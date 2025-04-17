"""
Storage node for the Interview Evaluator.

This node is responsible for storing the evaluation results in Supabase
after the evaluation is complete.
"""

import logging
from typing import Tuple, Dict, Any

from app.agents.evaluator.state import InterviewEvaluationState, EvaluationStatus
from app.services.supabase_client import supabase_service

logger = logging.getLogger(__name__)


def store_results_node(state: InterviewEvaluationState) -> Tuple[InterviewEvaluationState, str]:
    """
    Store evaluation results in Supabase.
    
    This node:
    1. Extracts the evaluation results from the state
    2. Formats them for storage
    3. Stores them in Supabase
    
    Args:
        state: The current state of the evaluation process
        
    Returns:
        Updated state and next node to transition to
    """
    try:
        logger.info(f"Storing results for interview {state.interview_id}")
        
        # Check if we have a summary and evaluations
        if not state.summary or not state.evaluations:
            logger.warning(f"No results to store for interview {state.interview_id}")
            return state, "end"
        
        # Format the results for storage
        results = {
            "overall_score": state.summary.overall_score,
            "summary": state.summary.summary,
            "strengths": state.summary.strengths,
            "weaknesses": state.summary.weaknesses,
            "criteria_evaluations": []
        }
        
        # Add individual criteria evaluations
        for eval_item in state.evaluations:
            results["criteria_evaluations"].append({
                "criterion": eval_item.criterion_name,
                "score": eval_item.score,
                "justification": eval_item.justification,
                "supporting_quotes": eval_item.supporting_quotes
            })
        
        # Store the results in Supabase
        success = supabase_service.store_evaluation_results(state.interview_id, results)
        
        if success:
            logger.info(f"Successfully stored results for interview {state.interview_id}")
            
            # Update the status
            supabase_service.update_interview_status(state.interview_id, "evaluated")
            
            # Update the state
            state.status = EvaluationStatus.COMPLETE
        else:
            logger.warning(f"Failed to store results for interview {state.interview_id}")
            
            # If we've processed the interview but couldn't store results, still mark as complete
            # since we can return the results from memory
            state.status = EvaluationStatus.COMPLETE
        
        return state, "end"
        
    except Exception as e:
        logger.exception(f"Error in store_results_node: {e}")
        state.set_error(f"Result storage failed: {str(e)}")
        return state, "end"