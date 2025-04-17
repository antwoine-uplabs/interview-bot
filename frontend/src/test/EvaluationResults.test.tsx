import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import EvaluationResults from '../components/EvaluationResults';

describe('EvaluationResults Component', () => {
  it('renders evaluation results correctly', () => {
    const mockProps = {
      candidateName: 'Test Candidate',
      overallScore: 7.5,
      summary: 'Good interview performance',
      criteria: [
        {
          name: 'Technical Knowledge',
          score: 8.0,
          justification: 'Good technical understanding',
          supporting_quotes: ['Quote 1', 'Quote 2']
        },
        {
          name: 'Problem Solving',
          score: 7.0,
          justification: 'Solved most problems well',
          supporting_quotes: ['Quote 3', 'Quote 4']
        }
      ],
      strengths: ['Technical expertise', 'Communication'],
      weaknesses: ['Time management'],
      onReset: vi.fn()
    };
    
    render(<EvaluationResults {...mockProps} />);
    
    // Check for basic elements 
    expect(screen.getByText('Evaluation Results')).toBeInTheDocument();
    
    // Use a regex to match text that might be combined with other elements
    expect(screen.getByText(/Candidate: Test Candidate/)).toBeInTheDocument();
    expect(screen.getByText(/7.5\/10/)).toBeInTheDocument();
  });
});