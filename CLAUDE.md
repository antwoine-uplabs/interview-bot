# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Python Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000

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
- `app/utils`: Utility functions
- `frontend/src/components`: React components
- `frontend/src/services`: API client and services

## Process
- Check sprint docs in /docs/process/phase-eval/ for requirements
- Review PRD at /docs/process/phase-eval/interview_evaluator_prd.md for goals
- Update sprint files after completing work
- Create/update status.md with progress on each sprint

## Error
- When you find an error and find a fix, make a note of the mistake and fix in claude.md under the known issues heading

## Known Issues
