/**
 * API service for Interview Evaluator
 * 
 * This service handles all communication with the backend API.
 * It provides methods for uploading transcripts and retrieving evaluation results.
 */

// API base URL - would be stored in environment variables in production
const API_BASE_URL = 'http://localhost:8000'; // FastAPI backend URL

// Types
export interface EvaluationCriterion {
  name: string;
  score: number;
  justification: string;
  supporting_quotes?: string[];
}

export interface EvaluationResult {
  candidateName: string;
  overallScore: number;
  criteria: EvaluationCriterion[];
  summary: string;
  strengths?: string[];
  weaknesses?: string[];
  interview_id?: string;
}

export interface UploadResponse {
  message: string;
  interview_id: string;
  candidate_name: string;
  filename: string;
  status: string;
}

// Error handling helper
class ApiError extends Error {
  status: number;
  
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

// Check if authorization token exists
export const getAuthHeader = () => {
  const token = localStorage.getItem('supabase_auth_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

/**
 * Upload a transcript file for evaluation
 */
export async function uploadTranscript(file: File): Promise<EvaluationResult> {
  try {
    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append('file', file);
    
    // First, send the file to the backend
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
      headers: {
        ...getAuthHeader()
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new ApiError(
        errorData.detail || `Upload failed with status: ${response.status}`, 
        response.status
      );
    }
    
    const uploadResult: UploadResponse = await response.json();
    console.log('File uploaded successfully:', uploadResult);
    
    // After successful upload, wait 1 second before starting to poll for results
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Poll for results
    return await pollEvaluationResults(uploadResult.interview_id, uploadResult.candidate_name);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    } else {
      throw new ApiError('An unexpected error occurred during upload', 500);
    }
  }
}

/**
 * Poll for evaluation results
 */
async function pollEvaluationResults(interviewId: string, candidateName: string, maxAttempts = 30): Promise<EvaluationResult> {
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const result = await evaluateTranscript(interviewId, candidateName);
      
      // If we get a result with status 'success', return it
      if (result.status === 'success') {
        // Map the backend response to our frontend EvaluationResult format
        return {
          candidateName: candidateName,
          overallScore: result.overall_score,
          criteria: result.criteria_evaluations.map(criterion => ({
            name: criterion.criterion,
            score: criterion.score,
            justification: criterion.justification,
            supporting_quotes: criterion.supporting_quotes
          })),
          summary: result.summary,
          strengths: result.strengths,
          weaknesses: result.weaknesses,
          interview_id: interviewId
        };
      }
      
      // If still processing, wait and try again
      if (result.status === 'processing' || result.status === 'partial') {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds before trying again
        attempts++;
        continue;
      }
      
      // If there's an error, throw it
      throw new ApiError(result.error || 'Evaluation failed', 500);
    } catch (error) {
      if (attempts >= maxAttempts - 1) {
        throw error; // If we've tried too many times, give up
      }
      
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds before trying again
      attempts++;
    }
  }
  
  throw new ApiError('Evaluation timed out', 504);
}

/**
 * Evaluate a transcript using the /evaluate endpoint
 */
export async function evaluateTranscript(interviewId: string, candidateName: string): Promise<Record<string, unknown>> {
  try {
    const response = await fetch(`${API_BASE_URL}/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader()
      },
      body: JSON.stringify({
        interview_id: interviewId,
        candidate_name: candidateName
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new ApiError(
        errorData.detail || `Evaluation failed with status: ${response.status}`, 
        response.status
      );
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    } else {
      throw new ApiError('An unexpected error occurred during evaluation', 500);
    }
  }
}

/**
 * Get a health check from the API
 */
export async function healthCheck(): Promise<{ status: string, dependencies?: Record<string, string> }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new ApiError(`Health check failed with status: ${response.status}`, response.status);
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    } else {
      throw new ApiError('An unexpected error occurred during health check', 500);
    }
  }
}

/**
 * Get past evaluations
 */
export async function getPastEvaluations(): Promise<EvaluationResult[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/evaluations`, {
      headers: {
        ...getAuthHeader()
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new ApiError(
        errorData.detail || `Failed to fetch evaluations: ${response.status}`, 
        response.status
      );
    }
    
    const results = await response.json();
    
    return results.map((result: Record<string, unknown>) => ({
      candidateName: result.candidate_name,
      overallScore: result.overall_score,
      criteria: result.criteria_evaluations.map((criterion: Record<string, unknown>) => ({
        name: criterion.criterion,
        score: criterion.score,
        justification: criterion.justification,
        supporting_quotes: criterion.supporting_quotes
      })),
      summary: result.summary,
      strengths: result.strengths,
      weaknesses: result.weaknesses,
      interview_id: result.interview_id
    }));
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    } else {
      throw new ApiError('An unexpected error occurred while fetching evaluations', 500);
    }
  }
}