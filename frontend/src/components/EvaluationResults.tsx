interface Criterion {
  name: string;
  score: number;
  justification: string;
  supporting_quotes?: string[];
}

interface EvaluationResultsProps {
  candidateName: string;
  overallScore: number;
  criteria: Criterion[];
  summary: string;
  strengths?: string[];
  weaknesses?: string[];
  interview_id?: string;
  onReset: () => void;
}

export default function EvaluationResults({ 
  candidateName, 
  overallScore, 
  criteria, 
  summary,
  strengths = [],
  weaknesses = [],
  interview_id,
  onReset 
}: EvaluationResultsProps) {
  // Function to determine score color
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-blue-600';
    return 'text-red-600';
  };
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Evaluation Results</h2>
        <button 
          onClick={onReset}
          className="text-blue-600 hover:text-blue-800"
        >
          Upload Another
        </button>
      </div>
      
      <div className="mb-6 bg-gray-50 p-4 rounded-lg">
        <h3 className="font-medium text-gray-800">Candidate: {candidateName}</h3>
        {interview_id && (
          <div className="text-xs text-gray-500 mt-1">ID: {interview_id}</div>
        )}
        <div className="mt-2 flex items-center">
          <span className={`font-bold text-2xl mr-2 ${getScoreColor(overallScore)}`}>
            {overallScore.toFixed(1)}/10
          </span>
          <span className="text-gray-600">Overall Score</span>
        </div>
      </div>
      
      {/* Strengths and Weaknesses */}
      {(strengths.length > 0 || weaknesses.length > 0) && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {strengths.length > 0 && (
            <div className="bg-green-50 p-4 rounded-lg border border-green-100">
              <h3 className="font-medium text-green-800 mb-2">Strengths</h3>
              <ul className="list-disc list-inside space-y-1">
                {strengths.map((strength, index) => (
                  <li key={index} className="text-gray-700 text-sm">{strength}</li>
                ))}
              </ul>
            </div>
          )}
          
          {weaknesses.length > 0 && (
            <div className="bg-orange-50 p-4 rounded-lg border border-orange-100">
              <h3 className="font-medium text-orange-800 mb-2">Areas for Improvement</h3>
              <ul className="list-disc list-inside space-y-1">
                {weaknesses.map((weakness, index) => (
                  <li key={index} className="text-gray-700 text-sm">{weakness}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      
      <div className="mb-6">
        <h3 className="font-medium text-gray-800 mb-3">Evaluation Criteria</h3>
        <div className="space-y-3">
          {criteria.map((criterion, index) => (
            <div key={index} className="border-b pb-3">
              <div className="flex justify-between items-center">
                <span className="font-medium">{criterion.name}</span>
                <span className={`font-medium ${getScoreColor(criterion.score)}`}>
                  {criterion.score}/10
                </span>
              </div>
              <p className="text-gray-600 text-sm mt-1">{criterion.justification}</p>
              
              {criterion.supporting_quotes && criterion.supporting_quotes.length > 0 && (
                <div className="mt-2 pl-3 border-l-2 border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Supporting Evidence:</p>
                  <ul className="space-y-1">
                    {criterion.supporting_quotes.map((quote, i) => (
                      <li key={i} className="text-xs text-gray-600 italic">"{quote}"</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-medium text-gray-800 mb-2">Summary</h3>
        <p className="text-gray-600">{summary}</p>
      </div>
    </div>
  );
}