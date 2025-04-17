"""
Summary generation node for the Interview Evaluator LangGraph agent.

This module contains the node responsible for generating an overall
summary of the candidate's performance.
"""

import logging
import os
from typing import Tuple, List
import statistics

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

from app.agents.evaluator.state import (
    InterviewEvaluationState, 
    EvaluationSummary,
    EvaluationStatus
)
from app.agents.evaluator.prompts.evaluation_prompts import SUMMARY_GENERATION_PROMPT
from app.services.langsmith import langsmith_service

logger = logging.getLogger(__name__)


async def generate_summary_node(state: InterviewEvaluationState) -> Tuple[InterviewEvaluationState, str]:
    """
    Generate an overall summary of the candidate's performance.
    
    This node:
    1. Analyzes all individual criteria evaluations
    2. Calculates an overall score
    3. Identifies key strengths and weaknesses
    4. Generates a comprehensive summary
    
    Args:
        state: The current state of the evaluation process
        
    Returns:
        Updated state with evaluation summary
        Next node to transition to
    """
    try:
        logger.info(f"Generating summary for interview {state.interview_id}")
        
        # Check if there are evaluations to summarize
        if not state.evaluations:
            state.set_error("No evaluations available for summary generation")
            return state, "end"
        
        # Calculate overall score
        scores = [eval.score for eval in state.evaluations]
        overall_score = statistics.mean(scores) if scores else 0.0
        
        # For Sprint 2, we'll create a simple summary without using an LLM
        # In Sprint 3, we'll enhance this with LLM-generated insights
        
        # Format all evaluations for the prompt
        criteria_evaluations_text = ""
        for eval in state.evaluations:
            criteria_evaluations_text += f"## {eval.criterion_name} (Score: {eval.score}/10)\n\n"
            criteria_evaluations_text += f"Justification: {eval.justification}\n\n"
            if eval.supporting_quotes:
                criteria_evaluations_text += "Supporting Quotes:\n"
                for quote in eval.supporting_quotes:
                    criteria_evaluations_text += f"- \"{quote}\"\n"
            criteria_evaluations_text += "\n"
        
        # Get the OpenAI API key
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Create a trace for this summary generation
        trace_id = langsmith_service.trace_run(
            name="generate_summary",
            inputs={
                "candidate_name": state.candidate_name,
                "evaluations": [eval.dict() for eval in state.evaluations]
            }
        )
        
        # Initialize the LLM
        llm = ChatOpenAI(
            temperature=0.3,
            model="gpt-4",
            api_key=openai_api_key
        )
        
        # Create and format the prompt
        chat_prompt = ChatPromptTemplate.from_template(SUMMARY_GENERATION_PROMPT)
        chain = chat_prompt | llm
        
        # Execute the chain
        response = await chain.ainvoke({
            "candidate_name": state.candidate_name,
            "criteria_evaluations": criteria_evaluations_text
        })
        response_text = response.content
        
        # Simple parsing for Sprint 2
        # Extract strengths, weaknesses, and summary
        lines = response_text.split('\n')
        strengths_start = next((i for i, line in enumerate(lines) if "strength" in line.lower()), -1)
        weaknesses_start = next((i for i, line in enumerate(lines) if "weakness" in line.lower() or "improvement" in line.lower()), -1)
        summary_start = next((i for i, line in enumerate(lines) if "summary" in line.lower()), -1)
        
        # Extract strengths
        strengths = []
        if strengths_start >= 0:
            i = strengths_start + 1
            while i < len(lines) and (i < weaknesses_start or weaknesses_start < 0) and (i < summary_start or summary_start < 0):
                line = lines[i].strip()
                if line and line.startswith("-"):
                    strengths.append(line[1:].strip())
                i += 1
                
        # Extract weaknesses
        weaknesses = []
        if weaknesses_start >= 0:
            i = weaknesses_start + 1
            while i < len(lines) and (i < summary_start or summary_start < 0):
                line = lines[i].strip()
                if line and line.startswith("-"):
                    weaknesses.append(line[1:].strip())
                i += 1
                
        # Extract summary
        summary = ""
        if summary_start >= 0:
            summary_lines = []
            i = summary_start + 1
            while i < len(lines):
                line = lines[i].strip()
                if line:
                    summary_lines.append(line)
                i += 1
            summary = " ".join(summary_lines)
        
        # If parsing failed, create default values
        if not strengths:
            high_scores = sorted(state.evaluations, key=lambda x: x.score, reverse=True)
            strengths = [f"Strong {eval.criterion_name} skills" for eval in high_scores[:2]]
            
        if not weaknesses:
            low_scores = sorted(state.evaluations, key=lambda x: x.score)
            weaknesses = [f"Could improve {eval.criterion_name} skills" for eval in low_scores[:2]]
            
        if not summary:
            summary = (
                f"The candidate demonstrated an overall performance level of {overall_score:.1f}/10. "
                f"They showed strength in {', '.join(e.criterion_name for e in sorted(state.evaluations, key=lambda x: x.score, reverse=True)[:2])} "
                f"but could benefit from improvement in {', '.join(e.criterion_name for e in sorted(state.evaluations, key=lambda x: x.score)[:2])}."
            )
        
        # Create the summary
        evaluation_summary = EvaluationSummary(
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            summary=summary
        )
        
        # Add the summary to the state
        state.set_summary(evaluation_summary)
        
        # Update status to completed
        state.status = EvaluationStatus.COMPLETED
        
        logger.info(f"Generated summary with overall score: {overall_score:.1f}/10")
        
        # Return the updated state and indicate the next node to transition to
        return state, "end"
        
    except Exception as e:
        logger.exception(f"Error in generate_summary_node: {e}")
        state.set_error(f"Summary generation failed: {str(e)}")
        return state, "end"