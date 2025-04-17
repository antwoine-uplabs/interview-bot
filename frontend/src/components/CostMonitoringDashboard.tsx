import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { fetchCostProjection, fetchMonitoringData } from '../services/api';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface CostMonitoringProps {
  refreshInterval?: number; // refresh interval in ms
}

interface CostProjection {
  current_usage_tokens: number;
  projected_monthly_tokens: number;
  projected_monthly_cost_usd: number;
  error?: string;
}

interface TokenUsage {
  date: string;
  tokens: number;
  estimated_cost: number;
}

const CostMonitoringDashboard: React.FC<CostMonitoringProps> = ({ refreshInterval = 60000 }) => {
  const [costProjection, setCostProjection] = useState<CostProjection | null>(null);
  const [tokenUsageHistory, setTokenUsageHistory] = useState<TokenUsage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [modelBreakdown, setModelBreakdown] = useState<{model: string, percentage: number}[]>([]);
  
  const loadData = async () => {
    try {
      setLoading(true);
      
      // Fetch cost projection data
      const projectionData = await fetchCostProjection() as unknown as CostProjection;
      setCostProjection(projectionData);
      
      // Fetch monitoring data for token usage history
      const monitoringData = await fetchMonitoringData() as any;
      
      if (monitoringData?.metrics?.llm_tokens_used?.values) {
        const tokensData = monitoringData.metrics.llm_tokens_used.values.map((item: {timestamp: string, value: number}) => ({
          date: new Date(item.timestamp).toLocaleDateString(),
          tokens: item.value,
          estimated_cost: item.value * 0.000002, // simplified cost estimate
        }));
        
        // Group by date
        const groupedData = tokensData.reduce((acc: {[key: string]: TokenUsage}, curr: TokenUsage) => {
          if (!acc[curr.date]) {
            acc[curr.date] = {
              date: curr.date,
              tokens: 0,
              estimated_cost: 0
            };
          }
          acc[curr.date].tokens += curr.tokens;
          acc[curr.date].estimated_cost += curr.estimated_cost;
          return acc;
        }, {});
        
        // Convert to array and get typed array
        const typedArray = Object.values(groupedData) as TokenUsage[];
        
        // Sort by date
        typedArray.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
        
        setTokenUsageHistory(typedArray);
      }
      
      // Set model breakdown (sample data - replace with actual data when available)
      if (monitoringData?.langsmith_metrics) {
        // This would ideally come from the API, using placeholder for now
        setModelBreakdown([
          { model: 'gpt-4', percentage: 65 },
          { model: 'gpt-3.5-turbo', percentage: 25 },
          { model: 'claude-3', percentage: 10 }
        ]);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error loading cost monitoring data:', err);
      setError('Failed to load cost monitoring data');
      setLoading(false);
    }
  };
  
  useEffect(() => {
    loadData();
    
    // Set up refresh interval
    const intervalId = setInterval(loadData, refreshInterval);
    
    // Cleanup on unmount
    return () => clearInterval(intervalId);
  }, [refreshInterval]);
  
  // Line chart for token usage history
  const tokenHistoryChart = {
    labels: tokenUsageHistory.map(item => item.date),
    datasets: [
      {
        label: 'Token Usage',
        data: tokenUsageHistory.map(item => item.tokens),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4,
        fill: true,
        yAxisID: 'y'
      },
      {
        label: 'Estimated Cost (USD)',
        data: tokenUsageHistory.map(item => item.estimated_cost),
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.4,
        fill: true,
        yAxisID: 'y1'
      }
    ]
  };
  
  const tokenHistoryOptions = {
    responsive: true,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    stacked: false,
    plugins: {
      title: {
        display: true,
        text: 'Token Usage & Cost History'
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const label = context.dataset.label || '';
            if (label === 'Token Usage') {
              return `${label}: ${context.raw.toLocaleString()} tokens`;
            }
            return `${label}: $${context.raw.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Tokens'
        }
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        grid: {
          drawOnChartArea: false,
        },
        title: {
          display: true,
          text: 'Cost (USD)'
        }
      },
    },
  };
  
  // Doughnut chart for model breakdown
  const modelBreakdownChart = {
    labels: modelBreakdown.map(item => item.model),
    datasets: [
      {
        data: modelBreakdown.map(item => item.percentage),
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 99, 132, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
        ],
        borderWidth: 1
      }
    ]
  };
  
  // Daily cost projection bar chart
  const costProjectionChart = {
    labels: ['Current (30 days)'],
    datasets: [
      {
        label: 'Projected Cost (USD)',
        data: costProjection ? [costProjection.projected_monthly_cost_usd] : [0],
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 1
      }
    ]
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4" role="alert">
        <p>{error}</p>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">LLM Cost Monitoring</h2>
        
        {costProjection && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Current Usage</h3>
              <p className="text-3xl font-bold text-blue-600">
                {costProjection.current_usage_tokens.toLocaleString()} tokens
              </p>
            </div>
            
            <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Projected Monthly Usage</h3>
              <p className="text-3xl font-bold text-purple-600">
                {Math.round(costProjection.projected_monthly_tokens).toLocaleString()} tokens
              </p>
            </div>
            
            <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Projected Monthly Cost</h3>
              <p className="text-3xl font-bold text-green-600">
                ${costProjection.projected_monthly_cost_usd.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Approx. ${(costProjection.projected_monthly_cost_usd / 30).toFixed(2)} per day
              </p>
            </div>
          </div>
        )}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div className="h-80 bg-white p-4 rounded-lg shadow">
            <Line data={tokenHistoryChart} options={tokenHistoryOptions} />
          </div>
        </div>
        
        <div className="lg:col-span-1">
          <div className="grid grid-rows-2 gap-6 h-full">
            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2 text-gray-700">Model Usage Breakdown</h3>
              <div className="h-40">
                <Doughnut 
                  data={modelBreakdownChart} 
                  options={{
                    plugins: {
                      legend: {
                        position: 'right',
                        labels: {
                          boxWidth: 12
                        }
                      }
                    }
                  }}
                />
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2 text-gray-700">Monthly Cost Projection</h3>
              <div className="h-40">
                <Bar 
                  data={costProjectionChart}
                  options={{
                    indexAxis: 'y' as const,
                    plugins: {
                      legend: {
                        display: false
                      }
                    },
                    scales: {
                      x: {
                        beginAtZero: true,
                        ticks: {
                          callback: function(value) {
                            return '$' + value;
                          }
                        }
                      }
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-8 text-sm text-gray-600 bg-gray-50 p-4 rounded-lg">
        <h3 className="font-semibold mb-2">Notes:</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li>Cost estimates are based on current usage patterns and approximate OpenAI pricing</li>
          <li>Actual costs may vary based on model selection and API pricing changes</li>
          <li>Set up alerts for cost thresholds in the Monitoring settings</li>
          <li>Daily cost breakdown available in the detailed reports section</li>
        </ul>
      </div>
    </div>
  );
};

export default CostMonitoringDashboard;