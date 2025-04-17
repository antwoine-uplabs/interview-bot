"""
State definitions for the Interview Evaluator LangGraph agent.

This module defines the Pydantic models that represent the state
of the evaluation process.
"""

from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class EvaluationStatus(str, Enum):
    """Status of the evaluation process"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class QAPair(BaseModel):
    """A question-answer pair extracted from the interview transcript"""
    question: str = Field(..., description="The question asked by the interviewer")
    answer: str = Field(..., description="The answer provided by the candidate")
    context: str = Field("", description="Any relevant context from previous exchanges")
    topics: List[str] = Field(default_factory=list, description="Technical topics covered in this exchange")
    position: int = Field(..., description="Position in the interview sequence")
    contains_code: bool = Field(False, description="Whether the answer contains code examples")


class EvaluationCriteria(BaseModel):
    """Evaluation criteria for a specific technical skill"""
    name: str = Field(..., description="Name of the criterion")
    description: str = Field(..., description="Description of what is being evaluated")
    max_score: float = Field(10.0, description="Maximum possible score")
    min_score: float = Field(0.0, description="Minimum possible score")
    weight: float = Field(1.0, description="Weight of this criterion in the overall evaluation")


class CriterionEvaluation(BaseModel):
    """Evaluation result for a specific criterion"""
    criterion_name: str = Field(..., description="Name of the criterion being evaluated")
    score: float = Field(..., description="Score assigned to this criterion")
    justification: str = Field(..., description="Justification for the assigned score")
    supporting_quotes: List[str] = Field(default_factory=list, description="Quotes from the transcript supporting the evaluation")
    confidence: float = Field(1.0, description="Confidence in this evaluation (0.0-1.0)")


class EvaluationSummary(BaseModel):
    """Overall evaluation summary"""
    overall_score: float = Field(..., description="Overall evaluation score")
    strengths: List[str] = Field(..., description="Candidate's strengths")
    weaknesses: List[str] = Field(..., description="Areas for improvement")
    summary: str = Field(..., description="Overall summary of the evaluation")


class InterviewEvaluationState(BaseModel):
    """
    State of the interview evaluation process.
    
    This is the main state object that is passed between nodes in the LangGraph.
    """
    interview_id: str = Field(..., description="ID of the interview being evaluated")
    candidate_name: str = Field(..., description="Name of the candidate")
    status: EvaluationStatus = Field(EvaluationStatus.NOT_STARTED, description="Current status of the evaluation")
    qa_pairs: List[QAPair] = Field(default_factory=list, description="Question-answer pairs extracted from the transcript")
    criteria: List[EvaluationCriteria] = Field(default_factory=list, description="Criteria used for evaluation")
    evaluations: List[CriterionEvaluation] = Field(default_factory=list, description="Evaluation results per criterion")
    summary: Optional[EvaluationSummary] = Field(None, description="Overall evaluation summary")
    error: Optional[str] = Field(None, description="Error message if status is ERROR")
    
    def add_qa_pair(self, qa_pair: QAPair) -> None:
        """Add a Q&A pair to the state"""
        self.qa_pairs.append(qa_pair)
    
    def add_evaluation(self, evaluation: CriterionEvaluation) -> None:
        """Add a criterion evaluation to the state"""
        self.evaluations.append(evaluation)
    
    def set_summary(self, summary: EvaluationSummary) -> None:
        """Set the overall evaluation summary"""
        self.summary = summary
    
    def set_error(self, error: str) -> None:
        """Set an error message and update status"""
        self.error = error
        self.status = EvaluationStatus.ERROR