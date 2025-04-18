// Script to set up Supabase tables using the REST API
const fs = require('fs');
const https = require('https');

// Read .env file
const envContent = fs.readFileSync('/Users/antwoineflowers/development/uplabs/resume/.env', 'utf8');
const envVars = {};
envContent.split('\n').forEach(line => {
  const match = line.match(/^([^#=]+)=(.*)$/);
  if (match) {
    envVars[match[1].trim()] = match[2].trim();
  }
});

const supabaseUrl = envVars.SUPABASE_URL;
const supabaseKey = envVars.SUPABASE_KEY; // Should be the service_role key for SQL execution

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials in .env file');
  process.exit(1);
}

// Read SQL file
const sql = fs.readFileSync('/Users/antwoineflowers/development/uplabs/resume/supabase_schema_execute.sql', 'utf8');

// Prepare request data
const data = JSON.stringify({
  query: sql
});

// Prepare request options
const options = {
  hostname: new URL(supabaseUrl).hostname,
  path: '/rest/v1/sql',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': data.length,
    'apikey': supabaseKey,
    'Authorization': `Bearer ${supabaseKey}`
  }
};

// Send request
const req = https.request(options, (res) => {
  let responseData = '';
  
  res.on('data', (chunk) => {
    responseData += chunk;
  });
  
  res.on('end', () => {
    if (res.statusCode >= 200 && res.statusCode < 300) {
      console.log('Supabase tables created successfully!');
    } else {
      console.error(`Error setting up Supabase tables: ${res.statusCode}`);
      console.error(responseData);
    }
  });
});

req.on('error', (error) => {
  console.error('Error:', error);
});

req.write(data);
req.end();