import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
} from 'chart.js';
import { Radar } from 'react-chartjs-2';
import { EvaluationResult, getPastEvaluations } from '../../services/api';

// Register ChartJS components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

interface ComparativeEvaluationProps {
  evaluations: EvaluationResult[];
}

export default function ComparativeEvaluation({ evaluations: initialEvaluations }: ComparativeEvaluationProps) {
  const [evaluations, setEvaluations] = useState<EvaluationResult[]>(initialEvaluations);
  const [selectedEvaluations, setSelectedEvaluations] = useState<string[]>([]);
  const [chartData, setChartData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch evaluations from the API if none provided initially
  useEffect(() => {
    async function fetchEvaluations() {
      if (initialEvaluations.length === 0) {
        try {
          setLoading(true);
          setError(null);
          const data = await getPastEvaluations();
          setEvaluations(data);
        } catch (err) {
          if (err instanceof Error) {
            setError(err.message);
          } else {
            setError('Failed to fetch evaluations');
          }
        } finally {
          setLoading(false);
        }
      }
    }
    
    fetchEvaluations();
  }, [initialEvaluations.length]);
  
  // Function to toggle selection of an evaluation
  const toggleEvaluation = (evaluationId: string) => {
    if (selectedEvaluations.includes(evaluationId)) {
      setSelectedEvaluations(selectedEvaluations.filter(id => id !== evaluationId));
    } else {
      // Limit to comparing 4 evaluations at once
      if (selectedEvaluations.length < 4) {
        setSelectedEvaluations([...selectedEvaluations, evaluationId]);
      }
    }
  };
  
  // Colors for each dataset are defined inside useEffect to avoid dependency issues
  
  // Update chart data when selected evaluations change
  useEffect(() => {
    // Colors for each dataset
    const colors = [
      { bg: 'rgba(59, 130, 246, 0.2)', border: 'rgba(59, 130, 246, 1)' }, // Blue
      { bg: 'rgba(16, 185, 129, 0.2)', border: 'rgba(16, 185, 129, 1)' }, // Green
      { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgba(245, 158, 11, 1)' }, // Amber
      { bg: 'rgba(239, 68, 68, 0.2)', border: 'rgba(239, 68, 68, 1)' },   // Red
    ];
    if (selectedEvaluations.length === 0) {
      setChartData(null);
      return;
    }
    
    // Get all unique criteria names across selected evaluations
    const allCriteria = new Set<string>();
    selectedEvaluations.forEach(evalId => {
      const evaluation = evaluations.find(e => e.interview_id === evalId);
      if (evaluation) {
        evaluation.criteria.forEach(c => allCriteria.add(c.name));
      }
    });
    
    const labels = Array.from(allCriteria);
    
    // Create datasets for each selected evaluation
    const datasets = selectedEvaluations.map((evalId, index) => {
      const evaluation = evaluations.find(e => e.interview_id === evalId);
      if (!evaluation) return null;
      
      // Create a map of criterion name to score
      const criteriaMap = Object.fromEntries(
        evaluation.criteria.map(c => [c.name, c.score])
      );
      
      // Create data array, using the score if available or 0 if not
      const data = labels.map(label => criteriaMap[label] || 0);
      
      // Get color for this dataset
      const colorIndex = index % colors.length;
      
      return {
        label: evaluation.candidateName,
        data,
        backgroundColor: colors[colorIndex].bg,
        borderColor: colors[colorIndex].border,
        borderWidth: 2,
        pointBackgroundColor: colors[colorIndex].border,
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: colors[colorIndex].border,
      };
    }).filter(Boolean);
    
    setChartData({
      labels,
      datasets,
    });
  }, [selectedEvaluations, evaluations]);
  
  const options = {
    scales: {
      r: {
        angleLines: {
          display: true,
        },
        suggestedMin: 0,
        suggestedMax: 10,
      },
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: function(context: { dataset: { label: string }, formattedValue: string }) {
            return `${context.dataset.label}: ${context.formattedValue}/10`;
          }
        }
      }
    },
    responsive: true,
    maintainAspectRatio: true,
  };
  
  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="bg-red-50 p-4 rounded-lg border border-red-200 text-red-700">
          <p>Error: {error}</p>
          <p className="mt-2">Please try again later or contact support if the issue persists.</p>
        </div>
      </div>
    );
  }
  
  if (evaluations.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="bg-gray-50 p-8 rounded-lg border border-gray-200 text-center">
          <h3 className="text-lg font-medium text-gray-700">No Evaluations Found</h3>
          <p className="mt-2 text-gray-500">
            There are no evaluation results to compare. Upload interview transcripts to create evaluations.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Comparative Evaluation</h2>
      
      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Select Candidates to Compare (max 4)</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {evaluations.map(evaluation => (
            <div 
              key={evaluation.interview_id} 
              className={`p-3 border rounded cursor-pointer flex items-center ${
                selectedEvaluations.includes(evaluation.interview_id!) 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-blue-300'
              }`}
              onClick={() => toggleEvaluation(evaluation.interview_id!)}
            >
              <input 
                type="checkbox" 
                checked={selectedEvaluations.includes(evaluation.interview_id!)}
                onChange={() => {}}
                className="mr-2"
              />
              <div>
                <div className="font-medium">{evaluation.candidateName}</div>
                <div className="text-sm text-gray-500">
                  Overall Score: {evaluation.overallScore.toFixed(1)}/10
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {chartData && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-4">Comparative Skills Analysis</h3>
          <div className="w-full h-[400px]">
            <Radar data={chartData} options={options} />
          </div>
        </div>
      )}
      
      {selectedEvaluations.length === 0 && (
        <div className="text-center py-10 text-gray-500">
          Select at least one candidate to display comparative analysis
        </div>
      )}
      
      {selectedEvaluations.length > 0 && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {selectedEvaluations.map(evalId => {
            const evaluation = evaluations.find(e => e.interview_id === evalId);
            if (!evaluation) return null;
            
            return (
              <div key={evalId} className="border rounded-lg p-4">
                <h4 className="font-medium text-lg">{evaluation.candidateName}</h4>
                <div className="flex items-center mt-1 mb-3">
                  <span className={`font-bold text-lg mr-2 ${
                    evaluation.overallScore >= 8 
                      ? 'text-green-600' 
                      : evaluation.overallScore >= 6 
                        ? 'text-blue-600' 
                        : 'text-red-600'
                  }`}>
                    {evaluation.overallScore.toFixed(1)}/10
                  </span>
                  <span className="text-gray-600">Overall Score</span>
                </div>
                
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <div>
                    <h5 className="font-medium text-green-800">Strengths</h5>
                    <ul className="list-disc list-inside text-sm text-gray-700 mt-1">
                      {evaluation.strengths?.map((strength, i) => (
                        <li key={i}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-medium text-orange-800">Areas for Improvement</h5>
                    <ul className="list-disc list-inside text-sm text-gray-700 mt-1">
                      {evaluation.weaknesses?.map((weakness, i) => (
                        <li key={i}>{weakness}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}