# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Python Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI development server
uvicorn app.main:app --reload --port 8000

# Run LangGraph development server
langgraph dev

# Deploy LangGraph to LangChain Cloud
langgraph deploy

# Code formatting
black app/
isort app/

# Testing
pytest
```

### Frontend
```bash
cd frontend
npm install
npm run lint    # Check code style
npm run build   # Type check and build
# DO NOT RUN npm run dev (freezes tool functionality)
```

## Code Style Guidelines

### Python
- Imports: standard library → third-party → local
- Use Black formatter with 88 char line limit
- Type hints required for all functions
- Use Pydantic models for data validation
- snake_case for functions/variables, PascalCase for classes
- Try/except blocks with specific exceptions
- Log errors with context information

### TypeScript/React
- Use TypeScript with strict mode enabled
- 2-space indentation for all files
- Components use PascalCase, interfaces with descriptive names
- Functions/variables use camelCase
- Centralize API calls in services directory
- Use functional components with hooks
- Tailwind CSS for styling
- Implement proper error handling and loading states
- Use async/await with try/catch blocks for API calls

## Project Structure
- `app/models`: Data models and schema definitions
- `app/services`: Business logic and external integrations
- `app/agents`: LangGraph agents for evaluation
  - `app/agents/evaluator`: LangGraph agent for transcript evaluation
  - `app/agents/evaluator/nodes`: Individual nodes for the LangGraph workflow
  - `app/agents/evaluator/prompts`: Prompt templates for the evaluation
  - `app/agents/evaluator/state`: State definitions for the LangGraph agent
- `app/utils`: Utility functions
- `frontend/src/components`: React components
- `frontend/src/services`: API client and services
- `langgraph.json`: LangGraph configuration for cloud deployment

## Process
- Check sprint docs in /docs/process/phase-eval/ for requirements
- Review PRD at /docs/process/phase-eval/interview_evaluator_prd.md for goals
- Update sprint files after completing work
- Create/update status.md with progress on each sprint

## Error
- When you find an error and find a fix, make a note of the mistake and fix in claude.md under the known issues heading

## Known Issues

### LangGraph Configuration
- The `langgraph.json` file requires specific formatting for cloud deployment:
  - The graph path format must be a string with module:function pattern
  - The `env` property must be at the root level of the configuration
  - The `dependencies` field must include the project root (usually ["."])
  - The END node must be a function, not a constant

### Development Environment
- For local testing, use custom mock services for Supabase and LangSmith to avoid external service dependencies
- When using `langgraph dev`, a fixed port must be specified to avoid conflicts

### Backend Server 
- The FastAPI server may fail with "Address already in use" if port 8000 is occupied. Use `--port 8001` as an alternative.
- When running the server, you may see non-critical startup errors related to cost monitoring and LangSmith synchronization when using mock services
- The `supabase_client.py` requires the `get_supabase_client()` function to be defined to return the `supabase_service` singleton
