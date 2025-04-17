// Script to create Supabase tables using the service role key
const fs = require('fs');
const { createClient } = require('@supabase/supabase-js');

// Read .env file
const envContent = fs.readFileSync('/Users/antwoineflowers/development/uplabs/resume/.env', 'utf8');
const envVars = {};
envContent.split('\n').forEach(line => {
  const match = line.match(/^([^#=]+)=(.*)$/);
  if (match) {
    envVars[match[1].trim()] = match[2].trim();
  }
});

// Get Supabase credentials
const supabaseUrl = envVars.SUPABASE_URL;
const supabaseKey = envVars.SUPABASE_SERVICE_ROLE_KEY || envVars.SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials in .env file');
  process.exit(1);
}

console.log('Using Supabase service role key for table creation');
console.log(`URL: ${supabaseUrl}`);

// Initialize Supabase client with service role key
const supabase = createClient(supabaseUrl, supabaseKey);

// SQL statements for creating tables
const createInterviewsTable = `
CREATE TABLE IF NOT EXISTS public.interviews (
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
`;

const createEvaluationResultsTable = `
CREATE TABLE IF NOT EXISTS public.evaluation_results (
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
`;

const createCriteriaEvaluationsTable = `
CREATE TABLE IF NOT EXISTS public.criteria_evaluations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  interview_id uuid REFERENCES public.interviews(id) ON DELETE CASCADE,
  criterion_name TEXT NOT NULL,
  score NUMERIC(3,1),
  justification TEXT,
  supporting_quotes JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
`;

// Function to execute SQL statements
async function executeSql(sql, description) {
  try {
    console.log(`Creating ${description}...`);
    const { data, error } = await supabase.rpc('exec_sql', { query: sql });
    
    if (error) {
      console.error(`Error creating ${description}:`, error.message);
      
      // Try a direct query to the database for admin operations
      // Note: This is a simplified approach and may not work in all environments
      console.log(`Attempting alternative approach for ${description}...`);
      try {
        // Using Supabase's REST API for administrative SQL
        const response = await fetch(`${supabaseUrl}/rest/v1/?apikey=${supabaseKey}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${supabaseKey}`,
            'Prefer': 'tx=commit'
          },
          body: JSON.stringify({ query: sql })
        });
        
        if (response.ok) {
          console.log(`✅ Successfully created ${description} (alternative method)`);
        } else {
          console.error(`❌ Failed to create ${description} using alternative method`);
        }
      } catch (fetchError) {
        console.error(`❌ Alternative method failed:`, fetchError.message);
      }
    } else {
      console.log(`✅ Successfully created ${description}`);
    }
  } catch (error) {
    console.error(`❌ Unexpected error creating ${description}:`, error.message);
  }
}

// Main function to create all tables
async function createTables() {
  console.log('Starting table creation process...');
  
  try {
    // Create tables
    await executeSql(createInterviewsTable, 'interviews table');
    await executeSql(createEvaluationResultsTable, 'evaluation_results table');
    await executeSql(createCriteriaEvaluationsTable, 'criteria_evaluations table');
    
    console.log('\nTable creation process completed.');
    console.log('For full schema setup including indexes, triggers, and security policies,');
    console.log('follow the instructions in SUPABASE_SETUP.md to run the complete SQL script.');
  } catch (error) {
    console.error('❌ Error in table creation process:', error.message);
    console.log('Please follow the instructions in SUPABASE_SETUP.md to set up your tables manually.');
  }
}

// Run the table creation process
createTables();