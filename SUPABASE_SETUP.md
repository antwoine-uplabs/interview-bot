# Setting Up Supabase Tables for Interview Evaluator

This guide will help you set up the necessary tables in your Supabase project for the Interview Evaluator application.

## Prerequisites

- Supabase project created
- Access to Supabase project with administrator privileges

## Important Project Information

For this project, use the following Supabase project:
- **Project URL**: https://kicnoeliggudihnepouz.supabase.co
- **Project Ref**: kicnoeliggudihnepouz
- **Anon Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpY25vZWxpZ2d1ZGlobmVwb3V6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ4NjUzMTQsImV4cCI6MjA2MDQ0MTMxNH0.mntmYC9zMsKY_dLfx_On-Y7L2Stuj5KId40lxL8Jxpo`
- **Service Role Key**: (Available in your .env file)

## Step 1: Log in to your Supabase Dashboard

Go to [app.supabase.io](https://app.supabase.io) and log in to your account.

Select the project with reference `kicnoeliggudihnepouz`.

## Step 2: Navigate to the SQL Editor

In your project dashboard, click on the **SQL Editor** tab in the left sidebar.

## Step 3: Create New Query

Click on the "New Query" button to create a new SQL query.

## Step 4: Paste the SQL Script

Copy and paste the following SQL script into the query editor:

```sql
-- Schema for Interview Evaluator (executable in Supabase SQL Editor)

-- Interviews Table
CREATE TABLE public.interviews (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth.users(id),
    candidate_name TEXT NOT NULL,
    interview_date TIMESTAMPTZ DEFAULT now(),
    transcript_content TEXT,
    transcript_storage_path TEXT,
    status TEXT NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Evaluation Results Table
CREATE TABLE public.evaluation_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id uuid REFERENCES public.interviews(id) ON DELETE CASCADE,
    overall_score NUMERIC(3,1),
    summary TEXT,
    strengths JSONB,
    weaknesses JSONB,
    result_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Criteria Evaluations Table
CREATE TABLE public.criteria_evaluations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id uuid REFERENCES public.interviews(id) ON DELETE CASCADE,
    criterion_name TEXT NOT NULL,
    score NUMERIC(3,1),
    justification TEXT,
    supporting_quotes JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add indexes for faster queries
CREATE INDEX idx_interviews_status ON public.interviews(status);
CREATE INDEX idx_interviews_user_id ON public.interviews(user_id);
CREATE INDEX idx_evaluation_results_interview_id ON public.evaluation_results(interview_id);
CREATE INDEX idx_criteria_evaluations_interview_id ON public.criteria_evaluations(interview_id);

-- Function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION public.trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER set_interviews_timestamp
BEFORE UPDATE ON public.interviews
FOR EACH ROW
EXECUTE FUNCTION public.trigger_set_timestamp();

CREATE TRIGGER set_evaluation_results_timestamp
BEFORE UPDATE ON public.evaluation_results
FOR EACH ROW
EXECUTE FUNCTION public.trigger_set_timestamp();

CREATE TRIGGER set_criteria_evaluations_timestamp
BEFORE UPDATE ON public.criteria_evaluations
FOR EACH ROW
EXECUTE FUNCTION public.trigger_set_timestamp();

-- Add Row Level Security (RLS) policies
ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evaluation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.criteria_evaluations ENABLE ROW LEVEL SECURITY;

-- Users can only see their own interviews
CREATE POLICY "Users can see their own interviews"
    ON public.interviews
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can only insert their own interviews
CREATE POLICY "Users can insert their own interviews"
    ON public.interviews
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can only update their own interviews
CREATE POLICY "Users can update their own interviews"
    ON public.interviews
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can only delete their own interviews
CREATE POLICY "Users can delete their own interviews"
    ON public.interviews
    FOR DELETE
    USING (auth.uid() = user_id);

-- Users can only see evaluation results for their own interviews
CREATE POLICY "Users can see evaluation results for their own interviews"
    ON public.evaluation_results
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.interviews
            WHERE interviews.id = evaluation_results.interview_id
            AND interviews.user_id = auth.uid()
        )
    );

-- Users can only see criteria evaluations for their own interviews
CREATE POLICY "Users can see criteria evaluations for their own interviews"
    ON public.criteria_evaluations
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.interviews
            WHERE interviews.id = criteria_evaluations.interview_id
            AND interviews.user_id = auth.uid()
        )
    );

-- Authenticated service can perform all operations on evaluation_results
CREATE POLICY "Service can manage evaluation results"
    ON public.evaluation_results
    FOR ALL
    USING (auth.role() = 'service_role');

-- Authenticated service can perform all operations on criteria_evaluations
CREATE POLICY "Service can manage criteria evaluations"
    ON public.criteria_evaluations
    FOR ALL
    USING (auth.role() = 'service_role');

-- Add appropriate comments
COMMENT ON TABLE public.interviews IS 'Stores interview metadata and transcript paths';
COMMENT ON TABLE public.evaluation_results IS 'Stores overall evaluation results for interviews';
COMMENT ON TABLE public.criteria_evaluations IS 'Stores individual criteria evaluations for interviews';

COMMENT ON COLUMN public.interviews.status IS 'Tracks the processing state of the interview evaluation.';
COMMENT ON COLUMN public.interviews.transcript_content IS 'Direct storage for smaller transcripts.';
COMMENT ON COLUMN public.interviews.transcript_storage_path IS 'Path in Supabase Storage for larger files.';
```

## Step 5: Execute the SQL Script

Click the "Run" button to execute the SQL script. This will create all the necessary tables, functions, and security policies for your Interview Evaluator application.

## Step 6: Verify the Setup

After running the script, you can verify that everything was set up correctly by checking:

1. Go to the "Table Editor" in the left sidebar
2. You should see the following tables:
   - `interviews`
   - `evaluation_results`
   - `criteria_evaluations`

3. To check the RLS policies, go to each table's settings and click on "Policies" tab.

## Step 7: Configure Storage Bucket (Optional)

If you want to store larger transcript files in Supabase Storage:

1. Go to the "Storage" section in the left sidebar
2. Click "Create a new bucket"
3. Name it `interview-transcripts`
4. Set the privacy to "Private"
5. Enable RLS on this bucket

## Step 8: Test the Tables

You can test the tables by running sample queries in the SQL Editor:

```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
AND table_name IN ('interviews', 'evaluation_results', 'criteria_evaluations');

-- Check if RLS policies are applied
SELECT tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('interviews', 'evaluation_results', 'criteria_evaluations')
ORDER BY tablename, policyname;
```

## Next Steps

Your Supabase database is now set up and ready to use with the Interview Evaluator application. You can now:

1. Configure your application's environment variables to connect to your Supabase instance
2. Create test users in the Authentication section
3. Start using the application to evaluate interviews

## Troubleshooting

If you encounter any issues during setup:

- Check the Supabase PostgreSQL logs in the Dashboard
- Ensure you have the correct permissions to create tables and policies
- If a table already exists, you might need to drop it first or modify the script accordingly