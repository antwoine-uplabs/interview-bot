import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.8.0'
import { Configuration, OpenAIApi } from 'https://esm.sh/openai@3.2.1'

// Define interfaces for type safety
interface EvaluationRequest {
  interview_id: string;
  candidate_name: string;
}

interface CriterionEvaluation {
  criterion: string;
  score: number;
  justification: string;
  supporting_quotes: string[];
}

interface EvaluationResult {
  overall_score: number;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  criteria_evaluations: CriterionEvaluation[];
}

// Predefined evaluation criteria
const EVALUATION_CRITERIA = [
  'Python Proficiency',
  'SQL Knowledge',
  'Data Manipulation',
  'Statistical Knowledge',
  'Machine Learning Concepts',
  'Problem Solving',
  'Communication Skills'
];

// The main function that handles requests
serve(async (req) => {
  // Set up CORS headers
  const headers = new Headers({
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Content-Type': 'application/json'
  });

  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers });
  }

  try {
    // Parse the request body
    const { interview_id, candidate_name } = await req.json() as EvaluationRequest;

    if (!interview_id) {
      return new Response(
        JSON.stringify({ error: 'Missing interview_id parameter' }),
        { headers, status: 400 }
      );
    }

    // Initialize Supabase client (server-side)
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
      { auth: { persistSession: false } }
    );

    // Get the interview record
    const { data: interview, error: interviewError } = await supabaseAdmin
      .from('interviews')
      .select('*')
      .eq('id', interview_id)
      .single();

    if (interviewError || !interview) {
      return new Response(
        JSON.stringify({ error: `Interview not found: ${interviewError?.message || 'Unknown error'}` }),
        { headers, status: 404 }
      );
    }

    // Update the interview status to processing
    await supabaseAdmin
      .from('interviews')
      .update({ status: 'processing', updated_at: new Date().toISOString() })
      .eq('id', interview_id);

    // Get the transcript from storage
    const { data: transcript, error: storageError } = await supabaseAdmin
      .storage
      .from('interview-transcripts')
      .download(interview.transcript_storage_path);

    if (storageError || !transcript) {
      return new Response(
        JSON.stringify({ error: `Transcript not found: ${storageError?.message || 'Unknown error'}` }),
        { headers, status: 404 }
      );
    }

    // Convert Blob to text
    const transcriptText = await transcript.text();

    // Initialize OpenAI
    const openai = new OpenAIApi(new Configuration({
      apiKey: Deno.env.get('OPENAI_API_KEY'),
    }));

    // Process the transcript with OpenAI
    const evaluationResult = await evaluateTranscript(openai, transcriptText, candidate_name || interview.candidate_name);
    
    // Store the evaluation results
    await storeEvaluationResults(supabaseAdmin, interview_id, evaluationResult);

    // Update the interview status to evaluated
    await supabaseAdmin
      .from('interviews')
      .update({ status: 'evaluated', updated_at: new Date().toISOString() })
      .eq('id', interview_id);

    // Return the evaluation result
    return new Response(
      JSON.stringify({ 
        status: 'success',
        interview_id,
        ...evaluationResult 
      }),
      { headers }
    );
  } catch (error) {
    console.error('Error processing evaluation:', error);
    
    return new Response(
      JSON.stringify({ error: error.message || 'An unexpected error occurred' }),
      { headers, status: 500 }
    );
  }
});

// Evaluate the transcript using OpenAI
async function evaluateTranscript(openai: OpenAIApi, transcript: string, candidateName: string): Promise<EvaluationResult> {
  try {
    // First, extract relevant Q&A pairs and key points
    const extractionPrompt = `
      You are an AI assistant helping to evaluate a data science interview.
      Please analyze this interview transcript for candidate ${candidateName}.
      
      Extract the most important questions and answers related to technical skills,
      particularly focusing on Python, SQL, statistics, machine learning, and data analysis.
      
      For each relevant exchange, include:
      1. The interviewer's question
      2. The candidate's complete answer
      3. Any follow-up questions and answers on the same topic
      
      INTERVIEW TRANSCRIPT:
      ${transcript.slice(0, 15000)}  # Truncate to avoid token limits
    `;
    
    const extractionResponse = await openai.createChatCompletion({
      model: 'gpt-4',
      messages: [
        { role: 'system', content: 'You are an expert technical interviewer for data science positions.' },
        { role: 'user', content: extractionPrompt }
      ],
      temperature: 0.3,
    });
    
    const extractedContent = extractionResponse.data.choices[0]?.message?.content || '';
    
    // Now evaluate each criterion
    const criteriaPrompt = `
      You are an AI assistant helping to evaluate a data science interview.
      Based on the extracted Q&A from the interview, evaluate the candidate ${candidateName} on the following criteria:
      
      ${EVALUATION_CRITERIA.map(criterion => `- ${criterion}`).join('\n')}
      
      For each criterion:
      1. Assign a score from 0-10 (where 10 is exceptional, 7 is good, 5 is average, 3 is poor)
      2. Provide a brief justification for the score
      3. Include 1-3 direct quotes from the candidate that support your evaluation
      
      EXTRACTED INTERVIEW CONTENT:
      ${extractedContent}
      
      Format your response as JSON with the following structure:
      {
        "criteria_evaluations": [
          {
            "criterion": "Criterion Name",
            "score": 7,
            "justification": "Justification text",
            "supporting_quotes": ["Quote 1", "Quote 2"]
          },
          ...
        ]
      }
    `;
    
    const evaluationResponse = await openai.createChatCompletion({
      model: 'gpt-4',
      messages: [
        { role: 'system', content: 'You are an expert technical interviewer for data science positions. You always respond with valid JSON.' },
        { role: 'user', content: criteriaPrompt }
      ],
      temperature: 0.2,
      response_format: { type: 'json_object' }
    });
    
    // Parse the evaluation response
    const evaluationContent = evaluationResponse.data.choices[0]?.message?.content || '{}';
    const evaluationData = JSON.parse(evaluationContent);
    
    // Generate summary, strengths, and weaknesses
    const summaryPrompt = `
      You are an AI assistant helping to evaluate a data science interview.
      Based on the detailed evaluation, please provide:
      
      1. A summary paragraph of the candidate's overall performance
      2. 3-5 specific strengths demonstrated in the interview
      3. 3-5 specific areas for improvement
      
      EVALUATION DETAILS:
      ${JSON.stringify(evaluationData.criteria_evaluations, null, 2)}
      
      Format your response as JSON with the following structure:
      {
        "summary": "Summary paragraph here...",
        "strengths": ["Strength 1", "Strength 2", ...],
        "weaknesses": ["Area for improvement 1", "Area for improvement 2", ...]
      }
    `;
    
    const summaryResponse = await openai.createChatCompletion({
      model: 'gpt-4',
      messages: [
        { role: 'system', content: 'You are an expert technical interviewer for data science positions. You always respond with valid JSON.' },
        { role: 'user', content: summaryPrompt }
      ],
      temperature: 0.3,
      response_format: { type: 'json_object' }
    });
    
    // Parse the summary response
    const summaryContent = summaryResponse.data.choices[0]?.message?.content || '{}';
    const summaryData = JSON.parse(summaryContent);
    
    // Calculate overall score as weighted average of criterion scores
    const scores = evaluationData.criteria_evaluations.map((eval: CriterionEvaluation) => eval.score);
    const overallScore = scores.reduce((sum: number, score: number) => sum + score, 0) / scores.length;
    
    // Construct the final evaluation result
    return {
      overall_score: Math.round(overallScore * 10) / 10,  // Round to 1 decimal place
      summary: summaryData.summary,
      strengths: summaryData.strengths,
      weaknesses: summaryData.weaknesses,
      criteria_evaluations: evaluationData.criteria_evaluations
    };
  } catch (error) {
    console.error('Error in evaluation:', error);
    throw new Error(`Evaluation failed: ${error.message || 'Unknown error'}`);
  }
}

// Store evaluation results in Supabase
async function storeEvaluationResults(supabase: any, interviewId: string, results: EvaluationResult): Promise<void> {
  try {
    // First, store the overall evaluation
    const { error: evalError } = await supabase
      .from('evaluation_results')
      .insert({
        interview_id: interviewId,
        overall_score: results.overall_score,
        summary: results.summary,
        strengths: results.strengths,
        weaknesses: results.weaknesses,
        result_data: JSON.stringify(results),
        created_at: new Date().toISOString()
      });
      
    if (evalError) throw evalError;
    
    // Then store individual criteria evaluations
    const criteriaData = results.criteria_evaluations.map(criterion => ({
      interview_id: interviewId,
      criterion_name: criterion.criterion,
      score: criterion.score,
      justification: criterion.justification,
      supporting_quotes: criterion.supporting_quotes,
      created_at: new Date().toISOString()
    }));
    
    const { error: criteriaError } = await supabase
      .from('criteria_evaluations')
      .insert(criteriaData);
      
    if (criteriaError) throw criteriaError;
  } catch (error) {
    console.error('Error storing evaluation results:', error);
    throw new Error(`Failed to store evaluation results: ${error.message}`);
  }
}