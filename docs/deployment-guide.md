# Deployment Guide for Interview Evaluator

This document outlines the process for deploying the Interview Evaluator application to a production environment. The application consists of two main components:

1. **Backend API (FastAPI)**: Handles interview transcript processing and evaluation using LLMs.
2. **Frontend (React)**: Provides the user interface for uploading transcripts and viewing evaluations.

## Prerequisites

Before deploying, ensure you have the following:

- Docker and Docker Compose installed on the target server
- Supabase project set up with the correct schema
- API keys for:
  - OpenAI or another LLM provider
  - Supabase (service role key)
  - Sentry (for error monitoring)
  - LangSmith (for LLM monitoring)
- Domain name (for production deployment)

## Deployment Options

### Option 1: Docker Compose (Self-Hosted)

1. **Clone the Repository**

   ```bash
   git clone https://github.com/antwoine-uplabs/interview-bot.git
   cd interview-bot
   ```

2. **Configure Environment Variables**

   Create a `.env` file in the root directory with the required environment variables:

   ```bash
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-service-role-key
   
   # LLM Configuration
   OPENAI_API_KEY=your-openai-key
   
   # Monitoring
   SENTRY_DSN=your-sentry-backend-dsn
   LANGSMITH_API_KEY=your-langsmith-api-key
   ```

3. **Update Domain in Caddyfile**

   Edit the `Caddyfile` to use your domain:

   ```
   your-domain.com {
     # Configuration...
   }
   ```

4. **Build and Start Services**

   ```bash
   docker-compose up -d
   ```

5. **Verify Deployment**

   Check that all services are running:

   ```bash
   docker-compose ps
   ```

   Test the API:

   ```bash
   curl https://your-domain.com/api/health
   ```

### Option 2: Cloud Deployment

#### Backend API (Any Cloud Provider)

1. **Build the Docker Image**

   ```bash
   docker build -t interview-evaluator-api .
   ```

2. **Push to Container Registry**

   ```bash
   # Example for AWS ECR
   aws ecr get-login-password --region region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.region.amazonaws.com
   docker tag interview-evaluator-api:latest your-account-id.dkr.ecr.region.amazonaws.com/interview-evaluator-api:latest
   docker push your-account-id.dkr.ecr.region.amazonaws.com/interview-evaluator-api:latest
   ```

3. **Deploy to Cloud Service**

   - AWS: Deploy to ECS, Fargate, or EKS
   - Google Cloud: Deploy to Cloud Run or GKE
   - Azure: Deploy to AKS or App Service

   Ensure you configure the required environment variables.

#### Frontend (Vercel)

1. **Connect Repository to Vercel**

   - Link your GitHub repository to Vercel
   - Configure build settings:
     - Build Command: `npm run build`
     - Output Directory: `dist`

2. **Configure Environment Variables in Vercel**

   Set the following environment variables:

   ```
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
   VITE_API_URL=https://your-api-domain.com
   VITE_SENTRY_DSN=your-sentry-frontend-dsn
   ```

3. **Deploy**

   Trigger a deployment in Vercel.

## Monitoring Setup

### Sentry

1. **View Error Dashboards**

   Access your Sentry dashboards to monitor:
   - Frontend errors
   - Backend exceptions
   - Performance metrics

2. **Configure Alerts**

   Set up notification rules for critical errors.

### LangSmith

1. **Monitor LLM Performance**

   Use the LangSmith dashboard to:
   - Track LLM calls
   - Monitor latency
   - Analyze prompt effectiveness

2. **Set Up Tracing**

   Ensure `LANGSMITH_TRACING_V2=true` is set to enable detailed tracing.

## CI/CD Pipeline

The repository is configured with GitHub Actions for continuous integration:

- **Frontend CI**: Runs on changes to frontend code
  - Lints and type-checks TypeScript
  - Runs unit tests
  - Builds the application

- **Backend CI**: Runs on changes to Python code
  - Runs pytest
  - Checks code style with Black and isort
  - Builds the Docker image

- **Deployment**: Triggered on main branch updates
  - Deploys frontend to Vercel
  - Deploys backend to your configured cloud service (requires setup)

## Backup and Recovery

1. **Database Backups**

   Supabase provides automatic backups. Additionally:
   - Set up scheduled exports of critical data
   - Store backups in a separate storage service

2. **Recovery Process**

   In case of failure:
   - Restore from latest Supabase backup
   - Redeploy application containers
   - Verify system integrity with health checks

## Security Considerations

1. **API Security**

   - All endpoints are protected with JWT authentication
   - Rate limiting is configured in the Caddy proxy
   - Sensitive environment variables are securely stored

2. **Frontend Security**

   - Content Security Policy (CSP) is configured
   - HTTPS is enforced
   - Authentication tokens are securely stored

3. **Regular Updates**

   - Keep dependencies updated
   - Rotate API keys periodically
   - Monitor security advisories

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check network connectivity
   - Verify API URL configuration
   - Ensure environment variables are correctly set

2. **Authentication Problems**
   - Verify Supabase configuration
   - Check JWT token expiration settings
   - Review authentication logs in Supabase

3. **LLM Integration Issues**
   - Verify API key validity
   - Check rate limits
   - Monitor LangSmith for errors

### Support Resources

- GitHub Issues: [https://github.com/antwoine-uplabs/interview-bot/issues](https://github.com/antwoine-uplabs/interview-bot/issues)
- Documentation: [Repository Wiki](https://github.com/antwoine-uplabs/interview-bot/wiki)

## Maintenance

1. **Regular Tasks**
   - Monitor error rates in Sentry
   - Review system logs
   - Check for security updates

2. **Scaling Considerations**
   - Increase instance size for higher load
   - Consider implementing a distributed architecture for high volume
   - Set up autoscaling for variable loads

3. **Cost Optimization**
   - Monitor LLM API usage
   - Analyze performance metrics
   - Optimize container resources