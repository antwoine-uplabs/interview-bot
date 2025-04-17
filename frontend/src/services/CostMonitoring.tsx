import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  ChartOptions
} from 'chart.js';
import { fetchMonitoringData, fetchCostProjection } from './api';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface CostData {
  current_usage_tokens: number;
  projected_monthly_tokens: number;
  projected_monthly_cost_usd: number;
  error?: string;
}

interface TokenData {
  date: string;
  tokens: number;
}

const CostMonitoring: React.FC = () => {
  const [costProjection, setCostProjection] = useState<CostData | null>(null);
  const [tokenHistory, setTokenHistory] = useState<TokenData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Fetch cost projection data
        const projectionData = await fetchCostProjection() as unknown as CostData;
        setCostProjection(projectionData);
        
        // Fetch token usage history
        const monitoringData = await fetchMonitoringData() as any;
        
        if (monitoringData && monitoringData.metrics && monitoringData.metrics.llm_tokens_used) {
          const tokens = monitoringData.metrics.llm_tokens_used.values.map((item: {timestamp: string, value: number}) => ({
            date: new Date(item.timestamp).toLocaleDateString(),
            tokens: item.value
          }));
          
          // Group by date and sum tokens
          const groupedData = tokens.reduce((acc: {[key: string]: number}, curr: {date: string, tokens: number}) => {
            const { date, tokens } = curr;
            if (!acc[date]) {
              acc[date] = 0;
            }
            acc[date] += tokens;
            return acc;
          }, {});
          
          // Convert back to array format for Chart.js
          const formattedData = Object.entries(groupedData).map(([date, tokens]) => ({
            date,
            tokens
          }));
          
          // Sort by date
          formattedData.sort((a, b) => 
            new Date(a.date).getTime() - new Date(b.date).getTime()
          );
          
          setTokenHistory(formattedData as TokenData[]);
        }
        
        setLoading(false);
      } catch (err) {
        setError('Failed to load cost monitoring data');
        setLoading(false);
        console.error('Cost monitoring error:', err);
      }
    };
    
    loadData();
  }, []);

  const chartData: ChartData<'line'> = {
    labels: tokenHistory.map(item => item.date),
    datasets: [
      {
        label: 'Token Usage',
        data: tokenHistory.map(item => item.tokens),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4,
        fill: true
      }
    ]
  };

  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'LLM Token Usage History'
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const value = context.raw as number;
            return `Tokens: ${value.toLocaleString()}`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Tokens'
        }
      }
    }
  };

  if (loading) {
    return <div className="text-center p-4">Loading cost data...</div>;
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">{error}</div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">LLM Cost Monitoring</h2>
      
      {costProjection && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500">Current Usage</h3>
            <p className="text-2xl font-bold text-blue-600">
              {costProjection.current_usage_tokens.toLocaleString()} tokens
            </p>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500">Projected Monthly Usage</h3>
            <p className="text-2xl font-bold text-purple-600">
              {Math.round(costProjection.projected_monthly_tokens).toLocaleString()} tokens
            </p>
          </div>
          
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500">Projected Monthly Cost</h3>
            <p className="text-2xl font-bold text-green-600">
              ${costProjection.projected_monthly_cost_usd.toFixed(2)}
            </p>
          </div>
        </div>
      )}
      
      <div className="h-64 md:h-80">
        <Line data={chartData} options={chartOptions} />
      </div>
      
      <div className="mt-4 text-sm text-gray-500">
        <p>Cost estimates are based on current usage patterns and approximate OpenAI pricing.</p>
        <p>Actual costs may vary based on model selection and API pricing changes.</p>
      </div>
    </div>
  );
};

export default CostMonitoring;