/**
 * API service for Interview Evaluator
 * 
 * This service handles all communication with the backend API.
 * It provides methods for uploading transcripts and retrieving evaluation results.
 */

// API base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
export const getAuthHeader = (): Record<string, string> => {
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
    const headers = getAuthHeader();
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
      headers
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
interface EvaluationResponse {
  status: string;
  overall_score: number;
  summary: string;
  criteria_evaluations: Array<{
    criterion: string;
    score: number;
    justification: string;
    supporting_quotes?: string[];
  }>;
  strengths?: string[];
  weaknesses?: string[];
  error?: string;
}

export async function evaluateTranscript(interviewId: string, candidateName: string): Promise<EvaluationResponse> {
  try {
    // This function can work with both FastAPI backend and Supabase Edge Functions
    // Determine which endpoint to use based on environment configuration
    const useEdgeFunction = import.meta.env.VITE_USE_EDGE_FUNCTIONS === 'true';
    
    if (useEdgeFunction) {
      // Use Supabase Edge Function
      const edgeFunctionUrl = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/evaluate-transcript`;
      
      const response = await fetch(edgeFunctionUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('supabase_auth_token')}`,
          'apikey': import.meta.env.VITE_SUPABASE_ANON_KEY
        },
        body: JSON.stringify({
          interview_id: interviewId,
          candidate_name: candidateName
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new ApiError(
          errorData.error || `Evaluation failed with status: ${response.status}`, 
          response.status
        );
      }
      
      return await response.json();
    } else {
      // Use FastAPI backend (original implementation)
      const authHeaders = getAuthHeader();
      const response = await fetch(`${API_BASE_URL}/evaluate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders
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
    }
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
    // Determine which approach to use based on environment configuration
    const useSupabaseDirect = import.meta.env.VITE_USE_SUPABASE_DIRECT === 'true';
    
    if (useSupabaseDirect) {
      // Import supabase client on demand to avoid circular dependencies
      const { default: supabase } = await import('./supabase');
      
      // Use Supabase client directly
      const { data: evaluations, error } = await supabase
        .from('evaluation_results')
        .select(`
          *,
          interviews!evaluation_results_interview_id_fkey(candidate_name),
          criteria_evaluations!criteria_evaluations_interview_id_fkey(*)
        `)
        .order('created_at', { ascending: false });
      
      if (error) throw error;
      
      if (!evaluations || evaluations.length === 0) {
        return [];
      }
      
      // Map the Supabase response to our frontend model
      return evaluations.map((evaluation: any) => {
        // Group criteria evaluations by interview
        const criteriaEvals = evaluation.criteria_evaluations || [];
        
        return {
          candidateName: evaluation.interviews?.candidate_name || 'Unknown',
          overallScore: evaluation.overall_score,
          criteria: criteriaEvals.map((criterion: any) => ({
            name: criterion.criterion_name,
            score: criterion.score,
            justification: criterion.justification,
            supporting_quotes: criterion.supporting_quotes || []
          })),
          summary: evaluation.summary,
          strengths: evaluation.strengths || [],
          weaknesses: evaluation.weaknesses || [],
          interview_id: evaluation.interview_id
        };
      });
    } else {
      // Use FastAPI backend (original implementation)
      const authHeaders = getAuthHeader();
      const response = await fetch(`${API_BASE_URL}/evaluations`, {
        headers: authHeaders
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
        criteria: (result.criteria_evaluations as Array<Record<string, unknown>>).map((criterion: Record<string, unknown>) => ({
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
    }
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    } else {
      throw new ApiError('An unexpected error occurred while fetching evaluations', 500);
    }
  }
}

/**
 * Fetch monitoring metrics for the application
 */
export async function fetchMonitoringMetrics(days: number = 7): Promise<Record<string, unknown>> {
  try {
    // Determine which approach to use based on environment configuration
    const useSupabaseDirect = import.meta.env.VITE_USE_SUPABASE_DIRECT === 'true';
    
    if (useSupabaseDirect) {
      // Import supabase client on demand to avoid circular dependencies
      const { default: supabase } = await import('./supabase');
      
      // Use Supabase Functions directly
      const { data, error } = await supabase.functions.invoke('monitoring-metrics', {
        body: { days }
      });
      
      if (error) throw error;
      
      return data || {
        status: 'success',
        timestamp: new Date().toISOString(),
        langsmith_metrics: {},
        database_metrics: {}
      };
    } else {
      // Use FastAPI backend
      const authHeaders = getAuthHeader();
      const response = await fetch(`${API_BASE_URL}/monitoring/metrics?days=${days}`, {
        headers: authHeaders
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new ApiError(
          errorData.detail || `Failed to fetch monitoring metrics: ${response.status}`, 
          response.status
        );
      }
      
      return await response.json();
    }
  } catch (error) {
    // Report error to Sentry
    if (import.meta.env.VITE_SENTRY_DSN) {
      import('@sentry/react').then(Sentry => {
        Sentry.captureException(error);
      });
    }
    
    // Also log to console
    console.error('Error fetching monitoring metrics:', error);
    
    if (error instanceof ApiError) {
      throw error;
    } else {
      throw new ApiError('An unexpected error occurred while fetching monitoring metrics', 500);
    }
  }
}