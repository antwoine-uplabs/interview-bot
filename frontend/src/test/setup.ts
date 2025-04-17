import { expect, afterEach, beforeAll, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// Extend Vitest's expect with Testing Library matchers
expect.extend(matchers);

// Define API mocks
const baseUrl = 'http://localhost:8000';
export const handlers = [
  // Health check mock
  http.get(`${baseUrl}/health`, () => {
    return HttpResponse.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      dependencies: {
        supabase: 'connected',
        sentry: 'configured',
        langsmith: 'configured'
      }
    });
  }),
  
  // Evaluation results mock
  http.get(`${baseUrl}/results/:interviewId`, ({ params }) => {
    return HttpResponse.json({
      interview_id: params.interviewId,
      candidate_name: 'Test Candidate',
      overall_score: 7.5,
      summary: 'Test candidate has shown good understanding of concepts.',
      criteria_evaluations: [
        {
          criterion: 'Technical Knowledge',
          score: 8,
          justification: 'Good technical answers',
          supporting_quotes: ['Quote 1', 'Quote 2']
        },
        {
          criterion: 'Problem Solving',
          score: 7,
          justification: 'Solved most problems correctly',
          supporting_quotes: ['Quote 3', 'Quote 4']
        }
      ],
      strengths: ['Technical knowledge', 'Communication'],
      weaknesses: ['Time management']
    });
  }),
  
  // File upload mock
  http.post(`${baseUrl}/upload`, () => {
    return HttpResponse.json({
      message: 'Transcript uploaded successfully, processing started',
      interview_id: 'test-interview-id',
      candidate_name: 'Test Candidate',
      filename: 'test-file.txt',
      status: 'uploaded'
    }, { status: 202 });
  })
];

// Setup MSW server
const server = setupServer(...handlers);

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));

// Clean up after each test
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// Close server after all tests
afterAll(() => server.close());