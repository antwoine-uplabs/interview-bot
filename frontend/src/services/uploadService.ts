import { createClient } from '@supabase/supabase-js';

// Get Supabase credentials from environment variables
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Initialize Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

/**
 * Upload a transcript file directly to Supabase Storage
 */
export async function uploadTranscriptToStorage(file: File, candidateName: string): Promise<string> {
  try {
    // Create a unique filename
    const timestamp = new Date().getTime();
    const fileExtension = file.name.split('.').pop();
    const fileName = `${timestamp}_${candidateName.replace(/\s+/g, '_')}.${fileExtension}`;
    const filePath = `transcripts/${fileName}`;
    
    // Upload the file to the 'interview-transcripts' bucket
    const { data, error } = await supabase.storage
      .from('interview-transcripts')
      .upload(filePath, file, {
        cacheControl: '3600',
        upsert: false
      });
    
    if (error) throw error;
    
    return data.path;
  } catch (error) {
    console.error('Error uploading to Supabase Storage:', error);
    throw error;
  }
}

/**
 * Create an interview record in Supabase
 */
export async function createInterviewRecord(
  candidateName: string, 
  filePath: string
): Promise<{ id: string }> {
  try {
    // Get the current user
    const { data: { user } } = await supabase.auth.getUser();
    
    if (!user) {
      throw new Error('User not authenticated');
    }
    
    // Create the interview record
    const { data, error } = await supabase
      .from('interviews')
      .insert({
        user_id: user.id,
        candidate_name: candidateName,
        transcript_storage_path: filePath,
        status: 'uploaded',
        interview_date: new Date().toISOString()
      })
      .select('id')
      .single();
    
    if (error) throw error;
    
    return { id: data.id };
  } catch (error) {
    console.error('Error creating interview record:', error);
    throw error;
  }
}

/**
 * Get the status of an interview
 */
export async function getInterviewStatus(interviewId: string): Promise<string> {
  try {
    const { data, error } = await supabase
      .from('interviews')
      .select('status')
      .eq('id', interviewId)
      .single();
    
    if (error) throw error;
    
    return data.status;
  } catch (error) {
    console.error('Error getting interview status:', error);
    throw error;
  }
}

/**
 * Upload transcript and create interview record
 */
export async function uploadTranscript(
  file: File, 
  candidateName: string
): Promise<{ interviewId: string, status: string }> {
  try {
    // First upload the file to storage
    const filePath = await uploadTranscriptToStorage(file, candidateName);
    
    // Then create the interview record
    const { id } = await createInterviewRecord(candidateName, filePath);
    
    return { 
      interviewId: id,
      status: 'uploaded'
    };
  } catch (error) {
    console.error('Error in upload process:', error);
    throw error;
  }
}