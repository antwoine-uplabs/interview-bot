"""
Main LangGraph agent definition for the Interview Evaluator.

This module defines the structure of the LangGraph agent, connecting
the various nodes into a workflow.
"""

import logging
from typing import Dict, List, Optional, Any
import os

from langgraph.graph import StateGraph, END
from langchain_core.tracers import ConsoleCallbackHandler

from app.agents.evaluator.state import InterviewEvaluationState, EvaluationStatus
from app.agents.evaluator.nodes.qa_extraction import extract_qa_pairs
from app.agents.evaluator.nodes.evaluation_node import evaluate_criteria_node
from app.agents.evaluator.nodes.summary_node import generate_summary_node
from app.agents.evaluator.nodes.storage_node import store_results_node
from app.services.langsmith import langsmith_service

logger = logging.getLogger(__name__)


def initialize_criteria(state: InterviewEvaluationState):
    """
    Initialize evaluation criteria based on the extracted Q&A pairs.
    
    This node:
    1. Identifies the technical topics present in the Q&A pairs
    2. Maps these to evaluation criteria
    3. Adds the criteria to the state
    
    Args:
        state: The current state of the evaluation process
        
    Returns:
        Updated state with evaluation criteria
        Next node to transition to
    """
    try:
        logger.info(f"Initializing criteria for interview {state.interview_id}")
        
        # Extract all unique topics from Q&A pairs
        all_topics = set()
        for qa_pair in state.qa_pairs:
            all_topics.update(qa_pair.topics)
        
        # Map topics to criteria
        topic_to_criterion = {
            "Python": {"name": "Python", "description": "Python programming skills"},
            "SQL": {"name": "SQL", "description": "SQL database querying skills"},
            "Statistics": {"name": "Statistics", "description": "Statistical knowledge and applications"},
            "Machine Learning": {"name": "Machine Learning", "description": "Machine learning concepts and applications"},
            "Deep Learning": {"name": "Machine Learning", "description": "Machine learning concepts and applications"},
            "Data Engineering": {"name": "Python", "description": "Python programming and data engineering skills"},
            "Communication": {"name": "Communication", "description": "Communication and explanation skills"},
            "General": {"name": "Communication", "description": "Communication and explanation skills"}
        }
        
        # Create criteria based on identified topics
        from app.agents.evaluator.state import EvaluationCriteria
        criteria_map = {}
        
        for topic in all_topics:
            if topic in topic_to_criterion:
                criterion_info = topic_to_criterion[topic]
                criterion_name = criterion_info["name"]
                
                if criterion_name not in criteria_map:
                    criteria_map[criterion_name] = EvaluationCriteria(
                        name=criterion_name,
                        description=criterion_info["description"]
                    )
        
        # If no topics were identified, add a default Communication criterion
        if not criteria_map:
            criteria_map["Communication"] = EvaluationCriteria(
                name="Communication",
                description="Communication and explanation skills"
            )
        
        # Add the criteria to the state
        state.criteria = list(criteria_map.values())
        
        logger.info(f"Initialized {len(state.criteria)} criteria")
        
        # Return the updated state and indicate the next node
        return state, "evaluate_criteria"
        
    except Exception as e:
        logger.exception(f"Error in initialize_criteria: {e}")
        state.set_error(f"Criteria initialization failed: {str(e)}")
        return state, "end"


def create_evaluator_agent():
    """
    Create a LangGraph agent for evaluating interview transcripts.
    
    Returns:
        The compiled LangGraph agent
    """
    # Create the state graph
    graph = StateGraph(InterviewEvaluationState)
    
    # Add nodes to the graph
    graph.add_node("extract_qa_pairs", extract_qa_pairs)
    graph.add_node("initialize_criteria", initialize_criteria)
    graph.add_node("evaluate_criteria", evaluate_criteria_node)
    graph.add_node("generate_summary", generate_summary_node)
    graph.add_node("store_results", store_results_node)
    
    # Add the end node
    graph.add_node("end", END)
    
    # Define the workflow edges
    graph.set_entry_point("extract_qa_pairs")
    
    # Connect the nodes based on state transitions
    graph.add_conditional_edges(
        "extract_qa_pairs",
        lambda state: "end" if state.status == EvaluationStatus.ERROR else "initialize_criteria"
    )
    
    # Add conditional edges for error handling
    graph.add_conditional_edges(
        "initialize_criteria",
        lambda state: "end" if state.status == EvaluationStatus.ERROR else "evaluate_criteria"
    )
    
    graph.add_conditional_edges(
        "evaluate_criteria",
        lambda state: "end" if state.status == EvaluationStatus.ERROR else "generate_summary"
    )
    
    graph.add_conditional_edges(
        "generate_summary",
        lambda state: "end" if state.status == EvaluationStatus.ERROR else "store_results"
    )
    
    graph.add_edge("store_results", "end")
    
    # Configure tracing if enabled
    callbacks = []
    
    # Add console tracing for development
    if os.environ.get("DEBUG", "").lower() == "true":
        callbacks.append(ConsoleCallbackHandler())
    
    # Enable LangSmith tracing if configured
    if os.environ.get("LANGSMITH_API_KEY") and os.environ.get("LANGSMITH_TRACING_V2", "").lower() == "true":
        # In Sprint 3, we'll add proper LangSmith callbacks
        # from langsmith.callbacks import LangSmithCallbackHandler
        # langsmith_handler = LangSmithCallbackHandler(
        #     project_name=os.environ.get("LANGSMITH_PROJECT", "interview-evaluator")
        # )
        # callbacks.append(langsmith_handler)
        pass
    
    # Compile the graph with configured callbacks
    return graph.compile(callbacks=callbacks if callbacks else None)


# Singleton instance of the agent
evaluator_agent = create_evaluator_agent()