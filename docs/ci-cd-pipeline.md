# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline implemented for the Interview Evaluator Application.

## Overview

The CI/CD pipeline automates testing, building, and deployment processes to ensure code quality and reliability. It is implemented using GitHub Actions and consists of the following workflows:

1. **Frontend CI** - Tests and builds the frontend React application
2. **Backend CI** - Tests and builds the backend FastAPI application
3. **Production Deployment** - Manages deployment to staging and production environments

## Workflow Details

### Frontend CI (`.github/workflows/ci.yml`)

Triggered on:
- Push to main branch (files in `/frontend`)
- Pull requests to main branch (files in `/frontend`)

Jobs:
1. **Test**:
   - Run linting checks
   - Type checking with TypeScript
   - Execute unit tests
   - Upload test coverage reports

2. **Build**:
   - Build production assets
   - Upload build artifacts

3. **Deploy Preview** (Pull Requests only):
   - Deploy to Vercel preview environment
   - Comment on PR with preview URL

### Backend CI (`.github/workflows/backend-ci.yml`)

Triggered on:
- Push to main branch (files in `/app` or `requirements.txt`)
- Pull requests to main branch (files in `/app` or `requirements.txt`)

Jobs:
1. **Test**:
   - Check code formatting with Black and isort
   - Run unit tests with pytest
   - Generate coverage reports

2. **Build**:
   - Build Docker image
   - Upload Docker image as artifact

3. **Deploy Staging** (main branch only):
   - Deploy to staging environment

### Production Deployment (`.github/workflows/deploy.yml`)

Triggered manually via workflow_dispatch with environment selection (staging or production).

Jobs:
1. **Approve Production** (for production deployments only):
   - Require manual approval via GitHub Environments

2. **Deploy Backend**:
   - Build and push Docker image to container registry
   - Deploy to selected environment

3. **Deploy Frontend**:
   - Build frontend with environment-specific variables
   - Deploy to Vercel production

4. **Post-Deployment**:
   - Run health checks
   - Send deployment notifications

## Secrets Configuration

The following secrets need to be configured in GitHub:

### Backend Secrets:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service key
- `OPENAI_API_KEY` - OpenAI API key
- `LANGSMITH_API_KEY` - LangSmith API key
- `BACKEND_SENTRY_DSN` - Sentry DSN for backend
- `CONTAINER_REGISTRY` - Container registry URL
- `REGISTRY_USERNAME` - Container registry username
- `REGISTRY_PASSWORD` - Container registry password

### Frontend Secrets:
- `VITE_API_URL` - Backend API URL
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `VITE_SENTRY_DSN` - Sentry DSN for frontend
- `VERCEL_TOKEN` - Vercel API token
- `VERCEL_ORG_ID` - Vercel organization ID
- `VERCEL_PROJECT_ID` - Vercel project ID

### Notification Secrets:
- `SLACK_WEBHOOK` - Slack webhook URL for notifications

## Environment Configuration

Two environments are defined:
1. **Staging** - For testing features before production release
2. **Production** - The live environment for end users

Each environment has its own set of secrets and protection rules.

## Pull Request Workflow

1. Developer creates a feature branch from main
2. Developer submits a pull request to main
3. CI pipeline runs frontend and backend tests
4. For frontend changes, a preview deployment is created
5. Code owners review the pull request
6. After approval, PR is merged to main
7. CI pipeline deploys changes to staging environment

## Production Deployment

1. Navigate to Actions tab in GitHub repository
2. Select "Production Deployment" workflow
3. Click "Run workflow"
4. Select "production" from the environment dropdown
5. Click "Run workflow"
6. Approve deployment in the GitHub interface
7. Monitor deployment progress

## Monitoring and Notifications

- Deployment status updates are sent to Slack
- Build and test failures trigger notifications
- Deployment health checks verify successful deployments