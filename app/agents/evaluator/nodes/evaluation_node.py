"""
Evaluation node for the Interview Evaluator LangGraph agent.

This module contains the node responsible for evaluating candidate responses
based on predefined criteria.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Any
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from app.agents.evaluator.state import (
    InterviewEvaluationState, 
    CriterionEvaluation,
    EvaluationStatus, 
    QAPair
)
from app.agents.evaluator.prompts.evaluation_prompts import (
    EVALUATOR_SYSTEM_PROMPT,
    CRITERIA_PROMPTS
)
from app.services.langsmith import langsmith_service

logger = logging.getLogger(__name__)

# Pydantic model for structured LLM output
class EvaluationOutput(BaseModel):
    """Structured output for evaluation."""
    score: float = Field(..., description="Score from 0-10")
    justification: str = Field(..., description="Detailed justification for the score")
    supporting_quotes: List[str] = Field(..., description="Quotes from candidate's answer that support this evaluation")
    confidence: float = Field(..., description="Confidence in this evaluation (0.0-1.0)")


async def evaluate_criterion(
    state: InterviewEvaluationState,
    criterion_name: str,
    qa_pair: QAPair
) -> CriterionEvaluation:
    """
    Evaluate a candidate's response for a specific criterion.
    
    Args:
        state: The current state of the evaluation process
        criterion_name: The name of the criterion to evaluate
        qa_pair: The question-answer pair to evaluate
        
    Returns:
        CriterionEvaluation object with the evaluation results
    """
    try:
        # Get the prompt template for this criterion
        prompt_template = CRITERIA_PROMPTS.get(
            criterion_name, 
            CRITERIA_PROMPTS.get("Communication")  # Default to communication if not found
        )
        
        # Create the evaluation prompt
        system_message = SystemMessagePromptTemplate.from_template(EVALUATOR_SYSTEM_PROMPT)
        human_message = HumanMessagePromptTemplate.from_template(prompt_template)
        chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
        
        # Format the prompt with the question and answer
        formatted_prompt = chat_prompt.format(
            question=qa_pair.question,
            answer=qa_pair.answer
        )
        
        # Get the OpenAI API key
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Create a trace for this evaluation
        trace_id = langsmith_service.trace_run(
            name=f"evaluate_{criterion_name.lower()}",
            inputs={
                "criterion": criterion_name,
                "question": qa_pair.question,
                "answer": qa_pair.answer
            }
        )
        
        # Initialize the LLM
        llm = ChatOpenAI(
            temperature=0.2,
            model="gpt-4",
            api_key=openai_api_key
        )
        
        # Create the evaluation chain
        chain = chat_prompt | llm
        
        # TODO: Use structured output parsing in Sprint 3
        # For now, we'll use a simple approach with some post-processing
        
        # Execute the chain
        response = await chain.ainvoke({"question": qa_pair.question, "answer": qa_pair.answer})
        response_text = response.content
        
        # Simple parsing for Sprint 2 (will be improved in Sprint 3)
        # Extract score
        score_line = next((line for line in response_text.split('\n') if "score" in line.lower()), "")
        try:
            score = float(next((s for s in score_line.split() if s.replace('.', '').isdigit()), "0"))
        except:
            score = 5.0  # Default score if parsing fails
            
        # Extract justification (everything after "justification" or similar words)
        justification_start = max(
            response_text.lower().find("justification:"),
            response_text.lower().find("explanation:"),
            response_text.lower().find("reasoning:")
        )
        
        if justification_start > 0:
            justification = response_text[justification_start:].split('\n\n')[0].strip()
        else:
            justification = response_text  # Use whole response if no clear justification section
            
        # Extract quotes (look for text in quotes or after "quotes:" or similar)
        quotes_start = response_text.lower().find("quotes:")
        quotes = []
        if quotes_start > 0:
            quotes_text = response_text[quotes_start:]
            import re
            # Find all text in quotes
            quotes = re.findall(r'"([^"]*)"', quotes_text)
            if not quotes:
                # If no quoted text, just take the lines after "quotes:"
                quotes = [line.strip() for line in quotes_text.split('\n')[1:] if line.strip()]
                
        if not quotes and qa_pair.answer:
            # If no quotes extracted, use the first sentence of the answer
            quotes = [qa_pair.answer.split('.')[0] + '.']
        
        # Create the evaluation result
        evaluation = CriterionEvaluation(
            criterion_name=criterion_name,
            score=min(max(score, 0), 10),  # Ensure score is in range 0-10
            justification=justification,
            supporting_quotes=quotes,
            confidence=0.8  # Default confidence for Sprint 2
        )
        
        logger.info(f"Evaluated {criterion_name}: Score {evaluation.score}")
        return evaluation
        
    except Exception as e:
        logger.error(f"Error evaluating {criterion_name}: {e}", exc_info=True)
        # Return a default evaluation in case of error
        return CriterionEvaluation(
            criterion_name=criterion_name,
            score=0.0,
            justification=f"Error during evaluation: {str(e)}",
            supporting_quotes=[],
            confidence=0.0
        )


async def evaluate_criteria_node(state: InterviewEvaluationState) -> Tuple[InterviewEvaluationState, str]:
    """
    Evaluate all relevant criteria for the extracted Q&A pairs.
    
    This node:
    1. Identifies which criteria are relevant for each Q&A pair
    2. Evaluates the candidate's responses for each criterion
    3. Adds the evaluation results to the state
    
    Args:
        state: The current state of the evaluation process
        
    Returns:
        Updated state with evaluation results
        Next node to transition to
    """
    try:
        logger.info(f"Starting criteria evaluation for interview {state.interview_id}")
        
        # Update state to indicate processing
        state.status = EvaluationStatus.IN_PROGRESS
        
        # Define default criteria if none exist in state
        if not state.criteria:
            from app.agents.evaluator.state import EvaluationCriteria
            state.criteria = [
                EvaluationCriteria(name="Python", description="Python programming skills"),
                EvaluationCriteria(name="SQL", description="SQL database querying skills"),
                EvaluationCriteria(name="Statistics", description="Statistical knowledge and applications"),
                EvaluationCriteria(name="Machine Learning", description="Machine learning concepts and applications"),
                EvaluationCriteria(name="Communication", description="Communication and explanation skills")
            ]
        
        # Map technical topics to criteria
        topic_to_criterion = {
            "Python": "Python",
            "SQL": "SQL",
            "Statistics": "Statistics",
            "Machine Learning": "Machine Learning",
            "Deep Learning": "Machine Learning",
            "Data Engineering": "Python",
            "Communication": "Communication",
            "General": "Communication"
        }
        
        # Create a dictionary to track which Q&A pairs should be evaluated for each criterion
        criterion_to_qa_pairs: Dict[str, List[QAPair]] = {}
        
        # Organize Q&A pairs by relevant criteria
        for qa_pair in state.qa_pairs:
            for topic in qa_pair.topics:
                criterion = topic_to_criterion.get(topic)
                if criterion:
                    if criterion not in criterion_to_qa_pairs:
                        criterion_to_qa_pairs[criterion] = []
                    criterion_to_qa_pairs[criterion].append(qa_pair)
        
        # Perform evaluations for each criterion using the most relevant Q&A pair
        for criterion_name, qa_pairs in criterion_to_qa_pairs.items():
            # Sort Q&A pairs by relevance (for now, just use the first one)
            # In Sprint 3, we can implement more sophisticated relevance scoring
            if qa_pairs:
                # Evaluate the criterion using the first Q&A pair
                evaluation = await evaluate_criterion(state, criterion_name, qa_pairs[0])
                state.add_evaluation(evaluation)
                
        # If no evaluations were performed, set an error
        if not state.evaluations:
            state.set_error("No evaluations could be performed on the transcript")
            return state, "end"
        
        logger.info(f"Completed {len(state.evaluations)} evaluations")
        
        # Return the updated state and indicate the next node to transition to
        return state, "generate_summary"
        
    except Exception as e:
        logger.exception(f"Error in evaluate_criteria_node: {e}")
        state.set_error(f"Criteria evaluation failed: {str(e)}")
        return state, "end"