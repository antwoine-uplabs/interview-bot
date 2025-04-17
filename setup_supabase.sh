#!/bin/bash

# Load environment variables from .env file
set -a
source "/Users/antwoineflowers/development/uplabs/resume/.env"
set +a

# Check if Supabase credentials are available
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
  echo "Error: Supabase credentials not found in .env file"
  exit 1
fi

# Display setup information
echo "Setting up Supabase tables for the Interview Evaluator"
echo "Supabase URL: $SUPABASE_URL"

# Create SQL query for API call
SQL_FILE="/Users/antwoineflowers/development/uplabs/resume/supabase_schema_execute.sql"
SQL_QUERY=$(cat "$SQL_FILE")

# Make the API call to execute SQL
curl -s -X POST \
  "${SUPABASE_URL}/rest/v1/rpc/exec_sql" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"query\": $(echo "$SQL_QUERY" | jq -s -R .)}" > /tmp/supabase_response.json

# Check response
if grep -q "error" /tmp/supabase_response.json; then
  echo "Error setting up Supabase tables:"
  cat /tmp/supabase_response.json
  exit 1
else
  echo "Supabase tables created successfully!"
  echo "You can now use the Interview Evaluator API with your Supabase database."
  echo "------"
  echo "Tables created:"
  echo "- interviews"
  echo "- evaluation_results"
  echo "- criteria_evaluations"
  echo "------"
  echo "RLS (Row Level Security) policies have been applied to ensure data isolation."
  exit 0
fi