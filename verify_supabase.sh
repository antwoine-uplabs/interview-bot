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

echo "Verifying Supabase tables for the Interview Evaluator..."

# SQL query to list tables and their row counts
VERIFY_QUERY="
SELECT table_name, 
       (SELECT count(*) FROM information_schema.columns WHERE table_name = t.table_name) AS column_count,
       has_table_privilege(t.table_name, 'select') AS has_select_privilege,
       has_table_privilege(t.table_name, 'insert') AS has_insert_privilege
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN ('interviews', 'evaluation_results', 'criteria_evaluations')
ORDER BY table_name;
"

# Make the API call to execute SQL verification
curl -s -X POST \
  "${SUPABASE_URL}/rest/v1/rpc/exec_sql" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"query\": $(echo "$VERIFY_QUERY" | jq -s -R .)}" | jq . > /tmp/supabase_verify.json

# Display the tables found
echo "Results of verification:"
cat /tmp/supabase_verify.json

# Check RLS policies
echo -e "\nVerifying Row Level Security (RLS) policies..."

RLS_QUERY="
SELECT t.table_name, p.policyname, p.cmd AS operation, p.roles, p.permissive
FROM pg_policies p
JOIN information_schema.tables t ON p.tablename = t.table_name
WHERE t.table_schema = 'public'
AND t.table_name IN ('interviews', 'evaluation_results', 'criteria_evaluations')
ORDER BY t.table_name, p.policyname;
"

# Make the API call to execute SQL verification for RLS policies
curl -s -X POST \
  "${SUPABASE_URL}/rest/v1/rpc/exec_sql" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"query\": $(echo "$RLS_QUERY" | jq -s -R .)}" | jq . > /tmp/supabase_rls.json

# Display the RLS policies found
echo "RLS Policies:"
cat /tmp/supabase_rls.json