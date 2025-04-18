-- Initial Supabase schema for Interview Evaluator (MVP)

-- Drop tables if they exist (optional, useful for development)
-- DROP TABLE IF EXISTS criteria_evaluations;
-- DROP TABLE IF EXISTS evaluation_results;
-- DROP TABLE IF EXISTS interviews;

-- Interviews Table
CREATE TABLE interviews (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth.users(id), -- Link to Supabase Auth user
    candidate_name TEXT NOT NULL,
    interview_date TIMESTAMPTZ DEFAULT now(),
    transcript_content TEXT, -- Store short transcripts directly initially
    transcript_storage_path TEXT, -- Or use Supabase Storage for larger files
    status TEXT NOT NULL DEFAULT 'uploaded', -- e.g., 'uploaded', 'processing', 'evaluated', 'error'
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Evaluation Results Table
CREATE TABLE evaluation_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id uuid REFERENCES interviews(id) ON DELETE CASCADE,
    overall_score NUMERIC(3,1), -- Score out of 10, with 1 decimal place
    summary TEXT,
    strengths JSONB, -- Array of strengths as JSON
    weaknesses JSONB, -- Array of weaknesses as JSON
    result_data JSONB, -- Full evaluation result data as JSON
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Criteria Evaluations Table
CREATE TABLE criteria_evaluations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id uuid REFERENCES interviews(id) ON DELETE CASCADE,
    criterion_name TEXT NOT NULL,
    score NUMERIC(3,1), -- Score out of 10, with 1 decimal place
    justification TEXT,
    supporting_quotes JSONB, -- Array of quotes as JSON
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add RLS (Row Level Security) policies later for user data isolation
-- ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can see their own interviews." ON interviews FOR SELECT USING (auth.uid() = user_id);
-- CREATE POLICY "Users can insert their own interviews." ON interviews FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Add indexes for faster queries
CREATE INDEX idx_interviews_status ON interviews(status);
CREATE INDEX idx_evaluation_results_interview_id ON evaluation_results(interview_id);
CREATE INDEX idx_criteria_evaluations_interview_id ON criteria_evaluations(interview_id);

COMMENT ON COLUMN interviews.status IS 'Tracks the processing state of the interview evaluation.';
COMMENT ON COLUMN interviews.transcript_content IS 'Direct storage for smaller transcripts.';
COMMENT ON COLUMN interviews.transcript_storage_path IS 'Path in Supabase Storage for larger transcripts.';

-- Function to update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update 'updated_at' on interviews table modification
CREATE TRIGGER set_interviews_timestamp
BEFORE UPDATE ON interviews
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

-- Trigger to automatically update 'updated_at' on evaluation_results table modification
CREATE TRIGGER set_evaluation_results_timestamp
BEFORE UPDATE ON evaluation_results
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

-- Trigger to automatically update 'updated_at' on criteria_evaluations table modification
CREATE TRIGGER set_criteria_evaluations_timestamp
BEFORE UPDATE ON criteria_evaluations
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();