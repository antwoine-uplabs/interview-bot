# Deployment Guide for Interview Evaluator

This document outlines the steps to deploy the Interview Evaluator application using Vercel for the frontend and your preferred hosting solution for the backend API.

## Frontend Deployment (Vercel)

### Prerequisites
- A GitHub account connected to Vercel
- Access to the repository at https://github.com/antwoine-uplabs/interview-bot
- Supabase project with the required schema (see `SUPABASE_SETUP.md`)

### Step 1: Set up Vercel Project

1. Log in to [Vercel](https://vercel.com) and create a new project
2. Import the GitHub repository (`antwoine-uplabs/interview-bot`)
3. Select the `frontend` directory as the root directory for the project

### Step 2: Configure Environment Variables

Add the following environment variables in the Vercel project settings:

- `VITE_SUPABASE_URL`: Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key (public)
- `VITE_API_URL`: The URL of your deployed backend API (see Backend Deployment section)

### Step 3: Deploy

1. Trigger a deployment in Vercel
2. Vercel will automatically build and deploy the frontend using the settings in `vercel.json`
3. After deployment, Vercel will provide a URL for your application

## Backend Deployment Options

The backend can be deployed to various hosting platforms. Here are a few options:

### Option 1: Render

1. Create a new Web Service in Render
2. Connect to the GitHub repository
3. Set the root directory to the project root (not frontend)
4. Set the build command: `pip install -r requirements.txt`
5. Set the start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key (private)
   - `SUPABASE_JWT_SECRET`: Your Supabase JWT secret
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `LANGCHAIN_API_KEY`: Your LangChain API key (for LangSmith)
   - `LANGCHAIN_PROJECT`: Your LangSmith project name

### Option 2: AWS Lambda with API Gateway

1. Package the application for Lambda using a framework like Zappa or Mangum
2. Create a Lambda function with the packaged code
3. Set up API Gateway to route requests to your Lambda function
4. Configure environment variables in the Lambda settings
5. Deploy and note the API Gateway endpoint URL

### Option 3: Docker with any container hosting service

1. Create a Dockerfile based on the example below
2. Build and push the container to a registry (Docker Hub, AWS ECR, etc.)
3. Deploy to a container hosting service (AWS ECS, Google Cloud Run, etc.)
4. Configure environment variables in the container service

Example Dockerfile:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Connecting Frontend and Backend

Once both the frontend and backend are deployed:

1. Update the `VITE_API_URL` environment variable in Vercel to point to your backend URL
2. Redeploy the frontend if necessary
3. Ensure CORS is properly configured in the backend to allow requests from your Vercel domain

## Enabling Supabase Authentication

Make sure your Supabase project has the following settings:

1. Enable Email authentication in the Auth settings
2. Configure allowed redirect URLs to include your Vercel deployment URL
3. Set up email templates for authentication emails

## Monitoring and Logging

1. Set up LangSmith for monitoring LLM operations
2. Configure monitoring for your backend hosting platform
3. Set up error tracking with a service like Sentry

## Helpful Commands

```bash
# Test the backend locally
uvicorn app.main:app --reload --port 8000

# Build the frontend
cd frontend && npm run build

# Preview the frontend build
cd frontend && npm run preview
```

## Troubleshooting

- **Authentication Issues**: Check Supabase console for auth logs
- **API Connection Errors**: Verify CORS settings and environment variables
- **Deployment Failures**: Check build logs in Vercel or your backend hosting platform