import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import FileUpload from '../components/FileUpload';

// Mock the API service
vi.mock('../services/api', () => ({
  uploadTranscript: vi.fn().mockResolvedValue({
    interview_id: 'test-id',
    status: 'uploaded',
    message: 'Transcript uploaded successfully, processing started'
  })
}));

describe('FileUpload Component', () => {
  it('renders the file upload component', () => {
    const onEvaluationComplete = vi.fn();
    render(<FileUpload onEvaluationComplete={onEvaluationComplete} />);
    
    expect(screen.getByText('Upload Interview Transcript')).toBeInTheDocument();
    expect(screen.getByText('Click to upload')).toBeInTheDocument();
    expect(screen.getByText('.txt or .md files (Max 5MB)')).toBeInTheDocument();
  });
});