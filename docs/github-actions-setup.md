# GitHub Actions Setup Guide

This guide provides instructions for setting up the GitHub Actions CI/CD pipeline for the Interview Evaluator Application.

## Prerequisites

1. GitHub repository for the project
2. Admin access to the repository
3. Vercel account (for frontend deployment)
4. Container registry access (Docker Hub, GitHub Container Registry, etc.)
5. Supabase project
6. OpenAI API key
7. LangSmith API key
8. Sentry account

## Step 1: Configure GitHub Secrets

Navigate to your repository on GitHub, go to Settings > Secrets and Variables > Actions, and add the following secrets:

### Backend Secrets

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-key
OPENAI_API_KEY=your-openai-api-key
LANGSMITH_API_KEY=your-langsmith-api-key
BACKEND_SENTRY_DSN=https://your-sentry-dsn
CONTAINER_REGISTRY=your-container-registry-url
REGISTRY_USERNAME=your-registry-username
REGISTRY_PASSWORD=your-registry-password
```

### Frontend Secrets

```
VITE_API_URL=https://api.your-domain.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
VITE_SENTRY_DSN=https://your-frontend-sentry-dsn
VERCEL_TOKEN=your-vercel-token
VERCEL_ORG_ID=your-vercel-org-id
VERCEL_PROJECT_ID=your-vercel-project-id
```

### Notification Secrets

```
SLACK_WEBHOOK=https://hooks.slack.com/services/your-slack-webhook
```

## Step 2: Configure GitHub Environments

1. Go to Settings > Environments
2. Create two environments: "staging" and "production"
3. For the "production" environment, enable "Required reviewers" and add required approvers
4. Add environment-specific secrets if needed

## Step 3: Set Up Workflow Files

Create the following directories and files in your repository:

```
.github/
  workflows/
    ci.yml
    backend-ci.yml
    deploy.yml
  dependabot.yml
```

The content for these files is provided in the repository.

## Step 4: Vercel Project Setup

1. Create a new project in Vercel
2. Link it to your GitHub repository
3. Configure the project settings:
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Add environment variables (same as VITE_* secrets in GitHub)
5. Get the Vercel project ID and org ID from the project settings
6. Create a Vercel access token from your account settings

## Step 5: Container Registry Setup

1. Create an account with a container registry service
2. Create a repository for your backend images
3. Create access credentials (username/password or token)

## Step 6: Test the Workflows

1. Make a small change to the frontend or backend code
2. Push the change to main or create a pull request
3. Verify that the workflows run correctly
4. Check the logs for any errors

## Step 7: Manual Production Deployment

1. Go to the Actions tab in your GitHub repository
2. Select the "Production Deployment" workflow
3. Click "Run workflow"
4. Select "production" from the dropdown
5. Click "Run workflow"
6. Approve the deployment when prompted

## Troubleshooting

### Common Issues

1. **Secret Configuration**: Ensure all secrets are correctly set up in GitHub
2. **Vercel Integration**: Check Vercel project settings and access token
3. **Container Registry Authentication**: Verify registry credentials
4. **Docker Build Failures**: Check Dockerfile and context path
5. **Environment Variable References**: Ensure all env var references match the secret names

### Workflow Debugging

1. Check workflow run logs in the GitHub Actions tab
2. For failed steps, expand the logs to see detailed error messages
3. Use `actions/setup-debug@v1` to enable debugging for complex issues
4. Test parts of the workflow locally when possible

## Customizations

### Adding Custom Deployment Targets

Modify the `.github/workflows/deploy.yml` file to include additional deployment targets:

1. Add new environment option in the workflow_dispatch inputs
2. Create corresponding environment in GitHub settings
3. Add condition checks in the workflow jobs
4. Add deployment steps for the new environment

### Adding Quality Gates

To add additional quality gates:

1. Add code coverage thresholds to test jobs
2. Implement security scanning (e.g., CodeQL)
3. Add performance testing jobs
4. Configure branch protection rules with status checks