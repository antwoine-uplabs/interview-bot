import React, { useState, useEffect } from 'react';
import { EvaluationResult, getPastEvaluations } from '../../services/api';
import RadarChart from './RadarChart';
import BarChart from './BarChart';
import { getAuthHeader } from '../../services/api';
import { exportToCSV, exportToJSON, exportToPDF } from '../../utils/exportUtils';

export default function HistoricalEvaluations() {
  const [evaluations, setEvaluations] = useState<EvaluationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvaluation, setSelectedEvaluation] = useState<EvaluationResult | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'score' | 'name'>('date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const evaluationsPerPage = 10;
  
  // Fetch evaluations on component mount
  useEffect(() => {
    async function fetchEvaluations() {
      try {
        setLoading(true);
        setError(null);
        const data = await getPastEvaluations();
        setEvaluations(data);
        
        // Select the first evaluation by default
        if (data.length > 0) {
          setSelectedEvaluation(data[0]);
        }
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
    
    fetchEvaluations();
  }, []);
  
  // Filter evaluations based on search term
  const filteredEvaluations = evaluations.filter(evaluation => 
    evaluation.candidateName.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // Sort evaluations
  const sortedEvaluations = [...filteredEvaluations].sort((a, b) => {
    if (sortBy === 'score') {
      return sortDirection === 'asc' 
        ? a.overallScore - b.overallScore 
        : b.overallScore - a.overallScore;
    } else if (sortBy === 'name') {
      return sortDirection === 'asc'
        ? a.candidateName.localeCompare(b.candidateName)
        : b.candidateName.localeCompare(a.candidateName);
    } else {
      // Sort by date (using interview_id as proxy since it's likely sequential)
      return sortDirection === 'asc'
        ? (a.interview_id || '').localeCompare(b.interview_id || '')
        : (b.interview_id || '').localeCompare(a.interview_id || '');
    }
  });
  
  // Paginate evaluations
  const indexOfLastEvaluation = currentPage * evaluationsPerPage;
  const indexOfFirstEvaluation = indexOfLastEvaluation - evaluationsPerPage;
  const currentEvaluations = sortedEvaluations.slice(indexOfFirstEvaluation, indexOfLastEvaluation);
  const totalPages = Math.ceil(sortedEvaluations.length / evaluationsPerPage);
  
  // Toggle sort direction
  const toggleSort = (sortOption: 'date' | 'score' | 'name') => {
    if (sortBy === sortOption) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(sortOption);
      setSortDirection('desc');
    }
  };
  
  // Format date (dummy implementation since we don't have actual dates)
  const formatDate = (interviewId: string | undefined) => {
    if (!interviewId) return 'Unknown Date';
    
    // This is just a placeholder - in a real app you'd use actual date data
    return new Date().toLocaleDateString();
  };
  
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-blue-600';
    return 'text-red-600';
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-lg border border-red-200 text-red-700">
        <p>Error: {error}</p>
        <p className="mt-2">Please try again later or contact support if the issue persists.</p>
      </div>
    );
  }
  
  if (evaluations.length === 0) {
    return (
      <div className="bg-gray-50 p-8 rounded-lg border border-gray-200 text-center">
        <h3 className="text-lg font-medium text-gray-700">No Evaluations Found</h3>
        <p className="mt-2 text-gray-500">
          There are no evaluation results to display. Upload an interview transcript to create an evaluation.
        </p>
      </div>
    );
  }
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-6">Historical Evaluations</h2>
      
      <div className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="w-full md:w-64">
            <input
              type="text"
              placeholder="Search by candidate name..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1); // Reset to first page when searching
              }}
            />
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">Sort by:</span>
            <button 
              className={`text-sm ${sortBy === 'date' ? 'font-medium text-blue-600' : 'text-gray-600'}`}
              onClick={() => toggleSort('date')}
            >
              Date {sortBy === 'date' && (sortDirection === 'asc' ? '↑' : '↓')}
            </button>
            <button 
              className={`text-sm ${sortBy === 'score' ? 'font-medium text-blue-600' : 'text-gray-600'}`}
              onClick={() => toggleSort('score')}
            >
              Score {sortBy === 'score' && (sortDirection === 'asc' ? '↑' : '↓')}
            </button>
            <button 
              className={`text-sm ${sortBy === 'name' ? 'font-medium text-blue-600' : 'text-gray-600'}`}
              onClick={() => toggleSort('name')}
            >
              Name {sortBy === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
            </button>
          </div>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Candidate
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Overall Score
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {currentEvaluations.map((evaluation) => (
              <tr key={evaluation.interview_id} className={`hover:bg-gray-50 ${selectedEvaluation?.interview_id === evaluation.interview_id ? 'bg-blue-50' : ''}`}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{evaluation.candidateName}</div>
                  <div className="text-xs text-gray-500">ID: {evaluation.interview_id}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(evaluation.interview_id)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`font-medium ${getScoreColor(evaluation.overallScore)}`}>
                    {evaluation.overallScore.toFixed(1)}/10
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <button
                    onClick={() => setSelectedEvaluation(evaluation)}
                    className="text-blue-600 hover:text-blue-900"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3 sm:px-6 mt-4">
          <div className="flex flex-1 justify-between sm:hidden">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing <span className="font-medium">{indexOfFirstEvaluation + 1}</span> to <span className="font-medium">
                  {Math.min(indexOfLastEvaluation, sortedEvaluations.length)}
                </span> of <span className="font-medium">{sortedEvaluations.length}</span> results
              </p>
            </div>
            <div>
              <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  <span className="sr-only">Previous</span>
                  &lt;
                </button>
                
                {/* Page numbers */}
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                      page === currentPage
                        ? 'z-10 bg-blue-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                        : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0'
                    }`}
                  >
                    {page}
                  </button>
                ))}
                
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  <span className="sr-only">Next</span>
                  &gt;
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
      
      {/* Selected Evaluation Details */}
      {selectedEvaluation && (
        <div className="mt-8 border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">
            {selectedEvaluation.candidateName} - Detailed Evaluation
          </h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <RadarChart criteria={selectedEvaluation.criteria} />
            <BarChart criteria={selectedEvaluation.criteria} />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-green-50 p-4 rounded-lg border border-green-100">
              <h4 className="font-medium text-green-800 mb-2">Strengths</h4>
              <ul className="list-disc list-inside space-y-1">
                {selectedEvaluation.strengths?.map((strength, index) => (
                  <li key={index} className="text-gray-700 text-sm">{strength}</li>
                ))}
              </ul>
            </div>
            
            <div className="bg-orange-50 p-4 rounded-lg border border-orange-100">
              <h4 className="font-medium text-orange-800 mb-2">Areas for Improvement</h4>
              <ul className="list-disc list-inside space-y-1">
                {selectedEvaluation.weaknesses?.map((weakness, index) => (
                  <li key={index} className="text-gray-700 text-sm">{weakness}</li>
                ))}
              </ul>
            </div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-800 mb-2">Summary</h4>
            <p className="text-gray-600">{selectedEvaluation.summary}</p>
          </div>
          
          <div className="mt-6">
            <h4 className="font-medium text-gray-800 mb-3">Detailed Skill Assessment</h4>
            <div className="space-y-4">
              {selectedEvaluation.criteria.map((criterion, index) => (
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
          
          <div className="mt-6 flex justify-end space-x-3">
            <div className="relative inline-block text-left">
              <div>
                <button 
                  type="button" 
                  className="inline-flex justify-center w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none"
                  onClick={() => {
                    const dropdown = document.getElementById('export-dropdown');
                    if (dropdown) {
                      dropdown.classList.toggle('hidden');
                    }
                  }}
                >
                  Export Results
                  <svg className="-mr-1 ml-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
              <div 
                id="export-dropdown" 
                className="hidden origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5"
              >
                <div className="py-1">
                  <button
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                    onClick={() => {
                      if (selectedEvaluation) {
                        exportToCSV(selectedEvaluation);
                        document.getElementById('export-dropdown')?.classList.add('hidden');
                      }
                    }}
                  >
                    Export as CSV
                  </button>
                  <button
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                    onClick={() => {
                      if (selectedEvaluation) {
                        exportToJSON(selectedEvaluation);
                        document.getElementById('export-dropdown')?.classList.add('hidden');
                      }
                    }}
                  >
                    Export as JSON
                  </button>
                  <button
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                    onClick={() => {
                      if (selectedEvaluation) {
                        exportToPDF(selectedEvaluation);
                        document.getElementById('export-dropdown')?.classList.add('hidden');
                      }
                    }}
                  >
                    Export as PDF
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}