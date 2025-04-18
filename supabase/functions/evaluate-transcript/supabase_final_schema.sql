-- Final Supabase Schema for Interview Evaluator (Sprint 2 Completion)

-- Interviews Table
CREATE TABLE public.interviews (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth.users(id),
    candidate_name TEXT NOT NULL,
    role TEXT DEFAULT 'Data Scientist',
    interview_date TIMESTAMPTZ DEFAULT now(),
    transcript_content TEXT,
    transcript_storage_path TEXT,
    status TEXT NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Evaluation Criteria Table
CREATE TABLE public.evaluation_criteria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
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
    criterion_id uuid REFERENCES public.evaluation_criteria(id),
    criterion_name TEXT NOT NULL,
    score NUMERIC(3,1),
    justification TEXT,
    supporting_quotes JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Evaluation Summaries Table
CREATE TABLE public.evaluation_summaries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id uuid REFERENCES public.interviews(id) ON DELETE CASCADE UNIQUE,
    overall_score NUMERIC(3,1),
    overall_feedback TEXT,
    strengths TEXT,
    weaknesses TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add indexes for faster queries
CREATE INDEX idx_interviews_status ON public.interviews(status);
CREATE INDEX idx_interviews_user_id ON public.interviews(user_id);
CREATE INDEX idx_evaluation_results_interview_id ON public.evaluation_results(interview_id);
CREATE INDEX idx_criteria_evaluations_interview_id ON public.criteria_evaluations(interview_id);
CREATE INDEX idx_criteria_evaluations_criterion_id ON public.criteria_evaluations(criterion_id);
CREATE INDEX idx_evaluation_criteria_topic ON public.evaluation_criteria(topic);
CREATE INDEX idx_evaluation_criteria_is_active ON public.evaluation_criteria(is_active);
CREATE INDEX idx_evaluation_summaries_interview_id ON public.evaluation_summaries(interview_id);

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

CREATE TRIGGER set_evaluation_criteria_timestamp
BEFORE UPDATE ON public.evaluation_criteria
FOR EACH ROW
EXECUTE FUNCTION public.trigger_set_timestamp();

CREATE TRIGGER set_evaluation_summaries_timestamp
BEFORE UPDATE ON public.evaluation_summaries
FOR EACH ROW
EXECUTE FUNCTION public.trigger_set_timestamp();

-- Add Row Level Security (RLS) policies
ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evaluation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.criteria_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evaluation_criteria ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evaluation_summaries ENABLE ROW LEVEL SECURITY;

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

-- Users can see all evaluation criteria
CREATE POLICY "Users can see all evaluation criteria"
    ON public.evaluation_criteria
    FOR SELECT
    USING (true);

-- Only admins can modify evaluation criteria
CREATE POLICY "Only admins can modify evaluation criteria"
    ON public.evaluation_criteria
    FOR ALL
    USING (auth.role() = 'service_role');

-- Users can only see evaluation summaries for their own interviews
CREATE POLICY "Users can see evaluation summaries for their own interviews"
    ON public.evaluation_summaries
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.interviews
            WHERE interviews.id = evaluation_summaries.interview_id
            AND interviews.user_id = auth.uid()
        )
    );

-- Service role can manage evaluation results and criteria
CREATE POLICY "Service can manage evaluation results"
    ON public.evaluation_results
    FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service can manage criteria evaluations"
    ON public.criteria_evaluations
    FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Service can manage evaluation summaries"
    ON public.evaluation_summaries
    FOR ALL
    USING (auth.role() = 'service_role');

-- Add appropriate comments
COMMENT ON TABLE public.interviews IS 'Stores interview metadata and transcript paths';
COMMENT ON TABLE public.evaluation_results IS 'Stores overall evaluation results for interviews';
COMMENT ON TABLE public.criteria_evaluations IS 'Stores individual criteria evaluations for interviews';
COMMENT ON TABLE public.evaluation_criteria IS 'Stores predefined evaluation criteria for interviews';
COMMENT ON TABLE public.evaluation_summaries IS 'Stores overall summaries of interview evaluations';

COMMENT ON COLUMN public.interviews.status IS 'Tracks the processing state of the interview evaluation.';
COMMENT ON COLUMN public.interviews.transcript_content IS 'Direct storage for smaller transcripts.';
COMMENT ON COLUMN public.interviews.transcript_storage_path IS 'Path in Supabase Storage for larger files.';
COMMENT ON COLUMN public.interviews.role IS 'The role the candidate is being interviewed for';

-- Seed with initial criteria data
INSERT INTO public.evaluation_criteria (topic, description, is_active) VALUES
('Python Proficiency', 'Knowledge of Python programming, including standard libraries, data structures, and algorithms', true),
('SQL Skills', 'Ability to write complex SQL queries, database design knowledge, and understanding of optimization techniques', true),
('Machine Learning', 'Understanding of ML concepts, algorithms, and practical application knowledge', true),
('Statistics', 'Knowledge of statistical methods, probability theory, and data analysis techniques', true),
('Data Visualization', 'Skills in creating clear and informative visualizations, knowledge of tools and best practices', true),
('Problem Solving', 'Approach to solving complex problems, critical thinking abilities, and solution quality', true),
('Communication', 'Clarity of expression, ability to explain technical concepts, and overall communication effectiveness', true),
('Domain Knowledge', 'Understanding of relevant business domain and industry-specific knowledge', true),
('Data Engineering', 'Knowledge of data pipelines, ETL processes, and data infrastructure', true),
('System Design', 'Ability to design scalable and robust solutions for data science applications', true);