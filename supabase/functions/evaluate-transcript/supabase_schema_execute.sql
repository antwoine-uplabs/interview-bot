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