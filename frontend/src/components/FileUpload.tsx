import { useState } from 'react';
import { uploadTranscript, EvaluationResult } from '../services/api';

interface FileUploadProps {
  onEvaluationComplete: (result: EvaluationResult) => void;
}

export default function FileUpload({ onEvaluationComplete }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<string | null>(null);
  
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        await processFile(file);
      } else {
        setError('Please upload a .txt or .md file');
      }
    }
  };
  
  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        await processFile(file);
      } else {
        setError('Please upload a .txt or .md file');
      }
    }
  };
  
  const processFile = async (file: File) => {
    try {
      setUploading(true);
      setError(null);
      setProgress('Uploading file...');
      
      // Upload the file and start the evaluation process
      const result = await uploadTranscript(file);
      
      // Pass the result to the parent component
      onEvaluationComplete(result);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred during upload');
      }
    } finally {
      setUploading(false);
      setProgress(null);
    }
  };
  
  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-6">Upload Interview Transcript</h2>
      
      <div 
        className={`relative border-2 border-dashed rounded-lg p-8 text-center ${
          dragActive ? 'border-blue-600 bg-blue-50' : 'border-gray-300'
        } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          accept=".txt,.md"
          onChange={handleChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={uploading}
        />
        <div className="space-y-3">
          <svg 
            className="mx-auto h-12 w-12 text-gray-400" 
            stroke="currentColor" 
            fill="none" 
            viewBox="0 0 48 48" 
            aria-hidden="true"
          >
            <path 
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" 
              strokeWidth={2} 
              strokeLinecap="round" 
              strokeLinejoin="round" 
            />
          </svg>
          <div className="text-sm text-gray-600">
            <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
          </div>
          <p className="text-xs text-gray-500">
            .txt or .md files (Max 5MB)
          </p>
        </div>
      </div>
      
      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 rounded border border-red-200">
          <p className="text-sm">{error}</p>
        </div>
      )}
      
      {uploading && (
        <div className="mt-4">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500 mr-3"></div>
            <p className="text-gray-600">{progress || 'Processing...'}</p>
          </div>
          <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 animate-pulse" style={{ width: '100%' }}></div>
          </div>
          <p className="text-xs text-gray-500 text-center mt-2">
            This may take up to 1-2 minutes depending on the transcript length
          </p>
        </div>
      )}
      
      <div className="mt-6">
        <h3 className="text-lg font-medium">Instructions</h3>
        <ul className="mt-2 text-gray-600 text-sm list-disc list-inside space-y-1">
          <li>Upload an interview transcript in .txt or .md format</li>
          <li>The system will automatically analyze the interview</li>
          <li>The analysis will evaluate technical skills, problem-solving ability, and communication</li>
          <li>Results will include scores, strengths, areas for improvement, and supporting evidence</li>
        </ul>
      </div>
    </div>
  );
}