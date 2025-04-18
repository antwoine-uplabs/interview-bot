// Test script to verify Supabase connection and table existence
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');

// Read .env file
const envContent = fs.readFileSync('/Users/antwoineflowers/development/uplabs/resume/.env', 'utf8');
const envVars = {};
envContent.split('\n').forEach(line => {
  const match = line.match(/^([^#=]+)=(.*)$/);
  if (match) {
    envVars[match[1].trim()] = match[2].trim();
  }
});

// For table creation, we need to use the service role key
const supabaseUrl = envVars.SUPABASE_URL;
// Prioritize service role key for admin operations
const supabaseKey = envVars.SUPABASE_SERVICE_ROLE_KEY || 
                   envVars.SUPABASE_KEY || 
                   envVars.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials in .env file');
  process.exit(1);
}

console.log('Using Supabase credentials:');
console.log(`URL: ${supabaseUrl}`);
console.log(`Key type: ${supabaseKey === envVars.SUPABASE_ANON_KEY ? 'ANON_KEY' : 
                          supabaseKey === envVars.SUPABASE_SERVICE_ROLE_KEY ? 'SERVICE_ROLE_KEY' : 
                          supabaseKey === envVars.SUPABASE_SERVICE_KEY ? 'SERVICE_KEY' : 'KEY'}`);

// Initialize Supabase client
const supabase = createClient(supabaseUrl, supabaseKey);

async function testConnection() {
  try {
    console.log('Testing Supabase connection...');
    
    // Simple health check to test connection
    const { data, error } = await supabase.from('_pgsql_health').select('*');
    
    if (error) {
      // Try a different approach - listing tables
      console.log('Health check failed, trying to list tables...');
      const { data: tables, error: tablesError } = await supabase.rpc('get_tables');
      
      if (tablesError) {
        // Try a simple query directly to auth.users
        console.log('Table list failed, trying auth check...');
        const { data: auth, error: authError } = await supabase.auth.getSession();
        
        if (authError) {
          console.error('❌ All connection attempts failed');
          console.error('Last error:', authError.message);
        } else {
          console.log('✅ Connected to Supabase auth successfully!');
          console.log('Use the instructions in SUPABASE_SETUP.md to create the necessary tables.');
        }
      } else {
        console.log('✅ Connected to Supabase successfully!');
        console.log('Tables in the database:', tables);
      }
    } else {
      console.log('✅ Connected to Supabase successfully!');
      
      // Now try to check for our specific tables
      console.log('Checking for Interview Evaluator tables...');
      const checkTables = async (tableName) => {
        try {
          const { error } = await supabase.from(tableName).select('count', { count: 'exact' }).limit(0);
          return !error;
        } catch {
          return false;
        }
      };
      
      const interviewsExists = await checkTables('interviews');
      const resultsExists = await checkTables('evaluation_results');
      const criteriaExists = await checkTables('criteria_evaluations');
      
      if (interviewsExists && resultsExists && criteriaExists) {
        console.log('✅ All required tables exist!');
      } else {
        console.log('❌ Some tables are missing:');
        console.log(`- interviews: ${interviewsExists ? '✅' : '❌'}`);
        console.log(`- evaluation_results: ${resultsExists ? '✅' : '❌'}`);
        console.log(`- criteria_evaluations: ${criteriaExists ? '✅' : '❌'}`);
        console.log('Use the instructions in SUPABASE_SETUP.md to create the missing tables.');
      }
    }
  } catch (error) {
    console.error('❌ Unexpected error:', error.message);
    console.log('Please follow the instructions in SUPABASE_SETUP.md to set up your tables manually.');
  }
}

testConnection();