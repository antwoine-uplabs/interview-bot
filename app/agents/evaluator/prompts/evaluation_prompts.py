"""
Prompts for the Interview Evaluator LangGraph agent.

This module contains the prompt templates used by the agent to extract
information from transcripts and evaluate candidate responses.
"""

# Base system prompt for evaluation
EVALUATOR_SYSTEM_PROMPT = """You are an expert technical interviewer tasked with evaluating data science interview responses.
You will be given a question and answer from a data science interview and asked to evaluate specific criteria.
Provide thorough, objective assessments based on industry standards and best practices.
Support your evaluation with specific quotes or examples from the candidate's response.
Be fair and consistent in your scoring, using the full range from 0 to 10.
"""

# Prompt for evaluating Python skills
PYTHON_EVALUATION_PROMPT = """
# Python Proficiency Evaluation

## Question:
{question}

## Candidate's Answer:
{answer}

## Evaluation Task:
Evaluate the candidate's Python proficiency based on their answer above.
Consider:
- Syntax correctness and code style
- Use of appropriate Python features and libraries
- Problem-solving approach
- Code efficiency and best practices
- Error handling and edge cases

## Scoring Guidelines:
- 0-3: Fundamental misunderstandings of Python
- 4-5: Basic knowledge but significant gaps
- 6-7: Solid practical knowledge with minor issues
- 8-9: Strong Python skills with good practices
- 10: Expert-level Python knowledge with advanced concepts

Provide a score from 0-10 and a detailed justification with specific examples from their answer.
Include strengths and areas for improvement.
"""

# Prompt for evaluating SQL skills
SQL_EVALUATION_PROMPT = """
# SQL Proficiency Evaluation

## Question:
{question}

## Candidate's Answer:
{answer}

## Evaluation Task:
Evaluate the candidate's SQL proficiency based on their answer above.
Consider:
- Query correctness and syntax
- Use of appropriate SQL features
- Query efficiency and organization
- Understanding of relational database concepts
- Handling of complex joins or subqueries if applicable

## Scoring Guidelines:
- 0-3: Fundamental misunderstandings of SQL
- 4-5: Basic knowledge but significant gaps
- 6-7: Solid practical knowledge with minor issues
- 8-9: Strong SQL skills with good practices
- 10: Expert-level SQL knowledge with advanced concepts

Provide a score from 0-10 and a detailed justification with specific examples from their answer.
Include strengths and areas for improvement.
"""

# Prompt for evaluating statistics skills
STATISTICS_EVALUATION_PROMPT = """
# Statistics Proficiency Evaluation

## Question:
{question}

## Candidate's Answer:
{answer}

## Evaluation Task:
Evaluate the candidate's statistics proficiency based on their answer above.
Consider:
- Understanding of statistical concepts
- Proper interpretation of statistical measures
- Knowledge of probability theory
- Ability to explain complex concepts clearly
- Awareness of assumptions and limitations

## Scoring Guidelines:
- 0-3: Fundamental misunderstandings of statistics
- 4-5: Basic knowledge but significant gaps
- 6-7: Solid practical knowledge with minor issues
- 8-9: Strong statistics skills with good understanding
- 10: Expert-level statistics knowledge with advanced concepts

Provide a score from 0-10 and a detailed justification with specific examples from their answer.
Include strengths and areas for improvement.
"""

# Prompt for evaluating machine learning skills
ML_EVALUATION_PROMPT = """
# Machine Learning Proficiency Evaluation

## Question:
{question}

## Candidate's Answer:
{answer}

## Evaluation Task:
Evaluate the candidate's machine learning proficiency based on their answer above.
Consider:
- Understanding of ML algorithms and their applications
- Knowledge of model evaluation techniques
- Awareness of ML pipeline components
- Ability to explain model trade-offs
- Understanding of feature engineering

## Scoring Guidelines:
- 0-3: Fundamental misunderstandings of machine learning
- 4-5: Basic knowledge but significant gaps
- 6-7: Solid practical knowledge with minor issues
- 8-9: Strong ML skills with good understanding
- 10: Expert-level ML knowledge with advanced concepts

Provide a score from 0-10 and a detailed justification with specific examples from their answer.
Include strengths and areas for improvement.
"""

# Prompt for evaluating communication skills
COMMUNICATION_EVALUATION_PROMPT = """
# Communication Skills Evaluation

## Question:
{question}

## Candidate's Answer:
{answer}

## Evaluation Task:
Evaluate the candidate's communication skills based on their answer above.
Consider:
- Clarity and structure of the explanation
- Ability to translate technical concepts for different audiences
- Conciseness and relevance of the response
- Use of appropriate technical terminology
- Ability to provide illustrative examples

## Scoring Guidelines:
- 0-3: Highly unclear or incoherent communication
- 4-5: Basic communication with significant clarity issues
- 6-7: Clear communication with occasional issues
- 8-9: Very clear, well-structured communication
- 10: Exceptional communication with expert-level clarity

Provide a score from 0-10 and a detailed justification with specific examples from their answer.
Include strengths and areas for improvement.
"""

# Overall summary generation prompt
SUMMARY_GENERATION_PROMPT = """
# Overall Evaluation Summary

## Candidate: {candidate_name}

## Individual Criteria Evaluations:
{criteria_evaluations}

## Task:
Based on the individual criteria evaluations above, provide an overall assessment of the candidate.

Include:
1. An overall score from 0-10 that reflects the candidate's overall performance
2. 3-5 key strengths demonstrated by the candidate
3. 2-4 areas for improvement
4. A 2-3 sentence summary of the candidate's performance

Be balanced and fair in your assessment, taking into account the relative importance of different skills for a data science role.
"""

# Dictionary mapping criteria to their respective prompts
CRITERIA_PROMPTS = {
    "Python": PYTHON_EVALUATION_PROMPT,
    "SQL": SQL_EVALUATION_PROMPT,
    "Statistics": STATISTICS_EVALUATION_PROMPT,
    "Machine Learning": ML_EVALUATION_PROMPT,
    "Communication": COMMUNICATION_EVALUATION_PROMPT
}