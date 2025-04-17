"""
Q&A extraction node for the Interview Evaluator LangGraph agent.

This module contains the node responsible for extracting question-answer pairs
from an interview transcript.
"""

import logging
from typing import Tuple

from app.agents.evaluator.state import InterviewEvaluationState, QAPair, EvaluationStatus
from app.services.transcript_processor import transcript_processor

logger = logging.getLogger(__name__)


async def extract_qa_pairs(state: InterviewEvaluationState) -> Tuple[InterviewEvaluationState, str]:
    """
    Extract question-answer pairs from an interview transcript.
    
    Uses the dialogue-aware semantic chunking strategy implemented in the
    transcript processor.
    
    Args:
        state: The current state of the evaluation process
        
    Returns:
        Updated state with extracted Q&A pairs
        Next node to transition to
    """
    try:
        logger.info(f"Extracting Q&A pairs for interview {state.interview_id}")
        
        # Note: In a real implementation, this would retrieve the transcript from
        # the database using the interview_id. For now, we'll use a placeholder.
        # transcript_path = retrieve_transcript_path(state.interview_id)
        transcript_path = "interview-content/sample.txt"  # Placeholder for Sprint 2
        
        # Update state to indicate processing has started
        state.status = EvaluationStatus.IN_PROGRESS
        
        # Process the transcript using our semantic chunking approach
        success, result, error = transcript_processor.process_transcript(transcript_path)
        
        if not success or not result:
            logger.error(f"Failed to process transcript: {error}")
            state.set_error(f"Transcript processing failed: {error}")
            return state, "end"
        
        # Convert processed QA pairs to our state format
        for i, qa_pair in enumerate(result.get("all_qa_pairs", [])):
            # Create QAPair objects for each pair in the processed transcript
            state.add_qa_pair(QAPair(
                question=qa_pair["question"],
                answer=qa_pair["answer"],
                context=qa_pair["context"],
                topics=qa_pair["topics"],
                position=qa_pair["position"],
                contains_code=qa_pair["contains_code"]
            ))
        
        logger.info(f"Extracted {len(state.qa_pairs)} Q&A pairs from transcript")
        
        # If no Q&A pairs were extracted, set an error
        if not state.qa_pairs:
            state.set_error("No Q&A pairs could be extracted from the transcript")
            return state, "end"
        
        # Return the updated state and indicate the next node to transition to
        return state, "initialize_criteria"
        
    except Exception as e:
        logger.exception(f"Error in extract_qa_pairs: {e}")
        state.set_error(f"Q&A extraction failed: {str(e)}")
        return state, "end"