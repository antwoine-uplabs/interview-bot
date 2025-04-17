# Interview Evaluator

An AI-powered tool for evaluating technical interviews using LangGraph.

## Overview

The Interview Evaluator processes interview transcripts and provides detailed evaluations of candidates' technical skills, communication abilities, and overall performance. The system uses a state-based LangGraph agent to identify strengths and weaknesses in candidates and provides quantifiable assessments.

## Features

- Upload interview transcripts for automated evaluation
- Evaluate technical skills across multiple domains (Python, SQL, Statistics, ML)
- Generate detailed feedback with supporting evidence from the transcript
- Track candidate strengths and areas for improvement
- Monitor and trace evaluations with LangSmith

## Project Status

- **Sprint 1**: Completed - Frontend and basic backend setup
- **Sprint 2**: Completed - LangGraph agent implementation and LangSmith integration
- **Sprint 3**: In Progress - End-to-end workflow and API integration (55% complete)

## Getting Started

### Backend

1. Create a Python virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Run the FastAPI backend:
```bash
python -m app.main
```

### Frontend

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## Architecture

The application follows a modular architecture:

- **FastAPI Backend**: Handles file uploads, API endpoints, and communication with LangGraph agent
- **React Frontend**: Provides user interface for uploading transcripts and viewing results
- **LangGraph Agent**: State-based agent for processing and evaluating interview transcripts
- **LangSmith Integration**: Provides tracing and monitoring for LLM-based evaluation
- **Supabase**: Database for storing interview data and evaluation results

## Evaluation Criteria

Interviews are evaluated across the following dimensions:

- **Python**: Understanding of Python fundamentals, libraries, and coding patterns
- **SQL**: Knowledge of database queries, joins, and optimizations
- **Statistics**: Understanding of statistical concepts and methods
- **Machine Learning**: Knowledge of ML algorithms, evaluation metrics, and model building
- **Communication**: Clarity, precision, and technical vocabulary

## Tech Stack

- **Backend**: Python, FastAPI, LangGraph, LangChain, OpenAI
- **Frontend**: TypeScript, React, Tailwind CSS
- **Database**: Supabase
- **Monitoring**: LangSmith
- **Deployment**: [TBD]