import { useState } from 'react';
import { useAuth } from '../context/useAuth';
import FileUpload from './FileUpload';
import EvaluationResults from './EvaluationResults';
import HistoricalEvaluations from './visualizations/HistoricalEvaluations';
import ComparativeEvaluation from './visualizations/ComparativeEvaluation';
import UserProfile from './auth/UserProfile';
import { EvaluationResult } from '../services/api';

type Tab = 'upload' | 'history' | 'compare' | 'profile';

export default function Dashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('upload');
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null);
  
  // Dummy data for the ComparativeEvaluation component
  // In a real app, this would come from an API call
  const dummyEvaluations: EvaluationResult[] = evaluationResult 
    ? [evaluationResult]
    : [];
  
  const handleReset = () => {
    setEvaluationResult(null);
  };
  
  const handleEvaluationComplete = (result: EvaluationResult) => {
    setEvaluationResult(result);
  };
  
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-semibold text-gray-900">Interview Evaluator</h1>
            {user && (
              <div className="text-sm text-gray-600">
                Logged in as <span className="font-medium">{user.email}</span>
              </div>
            )}
          </div>
        </div>
      </header>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="border-b">
            <nav className="flex">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'upload'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Upload & Evaluate
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'history'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Historical Evaluations
              </button>
              <button
                onClick={() => setActiveTab('compare')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'compare'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Compare Candidates
              </button>
              <button
                onClick={() => setActiveTab('profile')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'profile'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Profile
              </button>
            </nav>
          </div>
          
          <div className="p-6">
            {activeTab === 'upload' && (
              <>
                {evaluationResult ? (
                  <EvaluationResults 
                    candidateName={evaluationResult.candidateName}
                    overallScore={evaluationResult.overallScore}
                    criteria={evaluationResult.criteria}
                    summary={evaluationResult.summary}
                    strengths={evaluationResult.strengths}
                    weaknesses={evaluationResult.weaknesses}
                    interview_id={evaluationResult.interview_id}
                    onReset={handleReset}
                  />
                ) : (
                  <FileUpload onEvaluationComplete={handleEvaluationComplete} />
                )}
              </>
            )}
            
            {activeTab === 'history' && (
              <HistoricalEvaluations />
            )}
            
            {activeTab === 'compare' && (
              <ComparativeEvaluation evaluations={dummyEvaluations} />
            )}
            
            {activeTab === 'profile' && (
              <UserProfile />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}