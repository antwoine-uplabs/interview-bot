// Direct SQL execution script using the Supabase REST API
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

// Use the service role key
const supabaseUrl = envVars.SUPABASE_URL;
const supabaseKey = envVars.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase credentials in .env file');
  process.exit(1);
}

console.log('Using Supabase service role key for SQL execution');
console.log(`URL: ${supabaseUrl}`);

// Read SQL file
const sql = fs.readFileSync('/Users/antwoineflowers/development/uplabs/resume/supabase_schema_execute.sql', 'utf8');

// Function to execute SQL via the REST API
function executeSQL(sql) {
  return new Promise((resolve, reject) => {
    // Parse URL
    const url = new URL(supabaseUrl);
    
    // SQL API endpoint
    const endpoint = '/rest/v1/sql';
    
    // Create request options
    const options = {
      hostname: url.hostname,
      path: endpoint,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      }
    };
    
    // Create request
    const req = https.request(options, (res) => {
      let data = '';
      
      // Collect data
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      // Process response
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          console.log('SQL executed successfully');
          resolve(data);
        } else {
          console.error(`Error: ${res.statusCode}`);
          reject(new Error(`Request failed with status code ${res.statusCode}: ${data}`));
        }
      });
    });
    
    // Handle errors
    req.on('error', (error) => {
      console.error('Error:', error.message);
      reject(error);
    });
    
    // Send request with SQL data
    req.write(JSON.stringify({ query: sql }));
    req.end();
  });
}

// Execute SQL and display results
async function runSQLSetup() {
  try {
    console.log('Executing SQL setup script...');
    const result = await executeSQL(sql);
    console.log('SQL setup completed successfully!');
    console.log('Result:', result);
  } catch (error) {
    console.error('Error executing SQL setup:', error.message);
    console.log('Please follow the manual setup instructions in SUPABASE_SETUP.md');
  }
}

// Run the setup
runSQLSetup();