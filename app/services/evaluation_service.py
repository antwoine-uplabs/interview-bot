"""
Evaluation service for the Interview Evaluator.

This module provides functions for evaluating interview transcripts
using the LangGraph agent.
"""

import logging
import os
import uuid
from typing import Dict, Any, Optional

from app.agents.evaluator import (
    evaluator_agent, 
    InterviewEvaluationState, 
    EvaluationStatus
)
from app.services.langsmith import langsmith_service

logger = logging.getLogger(__name__)


async def evaluate_interview(
    interview_id: str,
    candidate_name: str,
    transcript_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate an interview using the LangGraph agent.
    
    Args:
        interview_id: ID of the interview to evaluate
        candidate_name: Name of the candidate being evaluated
        transcript_path: Path to the transcript file (optional)
        
    Returns:
        Evaluation results
    """
    try:
        logger.info(f"Starting evaluation for interview {interview_id}")
        
        # Create a trace for the entire evaluation process
        trace_id = langsmith_service.trace_run(
            name="evaluate_interview",
            inputs={
                "interview_id": interview_id,
                "candidate_name": candidate_name,
                "transcript_path": transcript_path
            }
        )
        
        # If no transcript path is provided, use a default from our example content
        if not transcript_path:
            transcript_path = "interview-content/sample.txt"
            logger.warning(f"No transcript path provided, using example: {transcript_path}")
        
        # Create initial state for the agent
        initial_state = InterviewEvaluationState(
            interview_id=interview_id,
            candidate_name=candidate_name,
            status=EvaluationStatus.NOT_STARTED
        )
        
        # Invoke the agent
        try:
            result = await evaluator_agent.ainvoke(initial_state)
            
            # Check for errors in the result
            if result.status == EvaluationStatus.ERROR:
                logger.error(f"Evaluation failed: {result.error}")
                return {
                    "status": "error",
                    "error": result.error or "Unknown error occurred during evaluation",
                    "interview_id": interview_id
                }
                
            # Process successful result
            if result.summary:
                logger.info(f"Evaluation completed with overall score: {result.summary.overall_score:.1f}/10")
                
                # Prepare the response
                response = {
                    "status": "success",
                    "interview_id": interview_id,
                    "candidate_name": candidate_name,
                    "overall_score": result.summary.overall_score,
                    "summary": result.summary.summary,
                    "strengths": result.summary.strengths,
                    "weaknesses": result.summary.weaknesses,
                    "criteria_evaluations": []
                }
                
                # Add individual criteria evaluations
                for eval in result.evaluations:
                    response["criteria_evaluations"].append({
                        "criterion": eval.criterion_name,
                        "score": eval.score,
                        "justification": eval.justification,
                        "supporting_quotes": eval.supporting_quotes
                    })
                    
                return response
            else:
                # No summary was generated but no error occurred
                logger.warning(f"Evaluation completed but no summary was generated")
                return {
                    "status": "partial",
                    "interview_id": interview_id,
                    "message": "Evaluation completed but no summary was generated",
                    "qa_pairs_count": len(result.qa_pairs) if result.qa_pairs else 0,
                    "evaluations_count": len(result.evaluations) if result.evaluations else 0
                }
                
        except Exception as agent_error:
            logger.exception(f"Error invoking evaluation agent: {agent_error}")
            return {
                "status": "error",
                "error": f"Agent execution failed: {str(agent_error)}",
                "interview_id": interview_id
            }
        
    except Exception as e:
        logger.exception(f"Error in evaluate_interview: {e}")
        return {
            "status": "error",
            "error": str(e),
            "interview_id": interview_id
        }