# Supabase-Centric Deployment Guide

This document outlines how to deploy the Interview Evaluator application using Vercel for the frontend and Supabase for the backend services.

## Architecture Overview

In this deployment approach:

1. **Vercel** hosts the React frontend
2. **Supabase** provides:
   - Database for storing interviews and evaluations
   - Authentication services
   - Storage for interview transcripts
   - Edge Functions (optional) for serverless API endpoints

## Frontend Deployment (Vercel)

### Prerequisites
- A GitHub account connected to Vercel
- Access to the repository at https://github.com/antwoine-uplabs/interview-bot
- A configured Supabase project

### Step 1: Set up Vercel Project

1. Log in to [Vercel](https://vercel.com) and create a new project
2. Import the GitHub repository (`antwoine-uplabs/interview-bot`)
3. Select the `frontend` directory as the root directory for the project

### Step 2: Configure Environment Variables

Add the following environment variables in the Vercel project settings:

- `VITE_SUPABASE_URL`: Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key (public)
- `VITE_API_URL`: Your OpenAI API proxy URL (if using Edge Functions)

### Step 3: Deploy

1. Trigger a deployment in Vercel
2. Vercel will automatically build and deploy the frontend using the settings in `vercel.json`
3. After deployment, Vercel will provide a URL for your application

## Supabase Setup

### Step 1: Database Setup

1. Run the schema creation scripts from `supabase_final_schema.sql` in the SQL Editor
2. Ensure all tables and indexes are created correctly
3. Set up Row Level Security (RLS) policies to restrict access to data

### Step 2: Authentication Configuration

1. Enable Email authentication in the Auth settings
2. Configure allowed redirect URLs to include your Vercel deployment URL
3. Set up email templates for authentication emails

### Step 3: Storage Setup

1. Create a storage bucket named `interview-transcripts`
2. Configure access policies to allow authenticated users to upload transcripts
3. Set up a lifecycle policy to clean up old files if needed

### Step 4: Edge Functions (Optional)

If you want to move the LLM processing to Supabase Edge Functions:

1. Navigate to the Edge Functions section in Supabase
2. Create a new function for transcript evaluation
3. Implement the evaluation logic using the OpenAI API
4. Deploy the function

Example Edge Function code:
```typescript
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.8.0'
import { Configuration, OpenAIApi } from 'https://esm.sh/openai@3.2.1'

serve(async (req) => {
  // Initialize Supabase client
  const supabaseClient = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
  )

  // Initialize OpenAI
  const configuration = new Configuration({
    apiKey: Deno.env.get('OPENAI_API_KEY'),
  })
  const openai = new OpenAIApi(configuration)

  // Handle the request
  try {
    const { interview_id } = await req.json()
    
    // Get the transcript from storage
    // Process with OpenAI
    // Store results in database
    
    return new Response(
      JSON.stringify({ success: true }),
      { headers: { 'Content-Type': 'application/json' } },
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { headers: { 'Content-Type': 'application/json' }, status: 400 },
    )
  }
})
```

## Connecting Frontend to Supabase

The frontend is already configured to use Supabase for:

1. Authentication via the Supabase JavaScript client
2. Data storage and retrieval
3. User management

Make sure your frontend environment variables point to your Supabase project.

## Migrating from FastAPI to Supabase

If you're moving from the FastAPI backend to a fully Supabase-powered backend:

1. Move the LLM evaluation logic to Edge Functions or a serverless platform
2. Update API endpoints in the frontend to use Supabase methods directly
3. Implement Row Level Security policies to handle data access controls
4. Set up webhooks to trigger evaluation processes when new transcripts are uploaded

### Database Access

Instead of the FastAPI endpoints, use Supabase queries in the frontend:

```typescript
// Example: Fetching evaluations
const fetchEvaluations = async () => {
  const { data, error } = await supabase
    .from('evaluation_results')
    .select('*, criteria_evaluations(*)')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });
    
  if (error) throw error;
  return data;
};
```

## Security Considerations

1. Implement proper Row Level Security (RLS) policies for all tables
2. Store sensitive keys (OpenAI API key) securely in Supabase environment variables
3. Use the appropriate Supabase keys for frontend vs. backend operations
4. Set up proper authentication redirects and session handling

## Monitoring and Logging

1. Set up Supabase monitoring for database operations
2. Configure Vercel Analytics for frontend monitoring
3. Implement logging within Edge Functions for debugging
4. Set up error tracking with a service like Sentry

## Cost Optimization

1. Monitor usage of OpenAI API calls
2. Set up budgets and alerts for Supabase and Vercel
3. Consider caching strategies for frequent queries
4. Optimize storage by cleaning up old or unused files

## Going to Production

Before launching to production:

1. Set up a custom domain in Vercel
2. Configure SSL certificates
3. Perform security audits
4. Test all authentication flows
5. Set up backup strategies for Supabase data
6. Implement proper monitoring and alerting