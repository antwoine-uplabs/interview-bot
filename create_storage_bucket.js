// Script to create a Supabase storage bucket
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');

// Read .env file
try {
  const envContent = fs.readFileSync('/Users/antwoineflowers/development/uplabs/resume/.env', 'utf8');
  const envVars = {};
  envContent.split('\n').forEach(line => {
    const match = line.match(/^([^#=]+)=(.*)$/);
    if (match) {
      envVars[match[1].trim()] = match[2].trim();
    }
  });

  // For bucket creation, we need to use the service role key
  const supabaseUrl = envVars.SUPABASE_URL;
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
                           'KEY'}`);

  // Initialize Supabase client with service role key for admin operations
  const supabase = createClient(supabaseUrl, supabaseKey);

  // Create the storage bucket
  async function createBucket() {
    try {
      console.log('Creating storage bucket "interview-transcripts"...');
      
      // Create the bucket with private access and RLS enabled
      const { data, error } = await supabase.storage.createBucket('interview-transcripts', {
        public: false, // Make it private
        fileSizeLimit: 50 * 1024 * 1024, // 50MB limit
        allowedMimeTypes: ['text/plain', 'application/pdf', 'text/markdown']
      });
      
      if (error) {
        console.error('❌ Failed to create bucket:', error.message);
        process.exit(1);
      }
      
      console.log('✅ Storage bucket "interview-transcripts" created successfully!');
      
      // Verify bucket exists by listing all buckets
      const { data: buckets, error: listError } = await supabase.storage.listBuckets();
      
      if (listError) {
        console.error('❌ Failed to list buckets:', listError.message);
      } else {
        console.log('Available buckets:');
        buckets.forEach(bucket => {
          console.log(`- ${bucket.name} (${bucket.public ? 'public' : 'private'})`);
        });
        
        // Check if our bucket is in the list
        const ourBucket = buckets.find(b => b.name === 'interview-transcripts');
        if (ourBucket) {
          console.log('✅ Verified bucket "interview-transcripts" exists!');
        } else {
          console.log('❌ Could not verify bucket "interview-transcripts"');
        }
      }
    } catch (error) {
      console.error('❌ Unexpected error:', error.message);
    }
  }

  createBucket();
} catch (error) {
  console.error('Error reading .env file:', error.message);
  process.exit(1);
}