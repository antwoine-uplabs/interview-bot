import { useState, useEffect } from 'react';
import { fetchMonitoringMetrics } from '../services/api';
import { Line, Bar } from 'react-chartjs-2';
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
  ChartData
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface MonitoringProps {
  refreshInterval?: number; // in milliseconds
}

interface MonitoringData {
  status: string;
  timestamp: string;
  langsmith_metrics: {
    total_runs: number;
    successful_runs: number;
    error_runs: number;
    success_rate: number;
    average_latency_seconds: number;
    run_types: Record<string, number>;
  };
  database_metrics: {
    total_interviews: number;
    total_evaluations: number;
    usage_statistics: {
      total_interviews: number;
      by_status: Record<string, number>;
      daily_counts: Record<string, number>;
    };
  };
}

export default function Monitoring({ refreshInterval = 60000 }: MonitoringProps) {
  const [monitoringData, setMonitoringData] = useState<MonitoringData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<number>(7); // default to 7 days

  // Load monitoring data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await fetchMonitoringMetrics(timeRange);
        // Handle possible type mismatch with defensive programming
        if (data && typeof data === 'object' && 'status' in data) {
          setMonitoringData(data as unknown as MonitoringData);
        }
        setError(null);
      } catch (err) {
        setError('Failed to load monitoring data');
        console.error('Error fetching monitoring data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Set up refresh interval
    const intervalId = setInterval(fetchData, refreshInterval);

    // Clean up interval
    return () => clearInterval(intervalId);
  }, [refreshInterval, timeRange]);

  // Prepare chart data for daily usage
  const getDailyUsageData = (): ChartData<'line'> => {
    if (!monitoringData?.database_metrics?.usage_statistics?.daily_counts) {
      return {
        labels: [],
        datasets: []
      };
    }

    const dailyCounts = monitoringData.database_metrics.usage_statistics.daily_counts;
    const sortedDates = Object.keys(dailyCounts).sort();
    
    return {
      labels: sortedDates,
      datasets: [
        {
          label: 'Interview Uploads',
          data: sortedDates.map(date => dailyCounts[date] || 0),
          borderColor: 'rgb(53, 162, 235)',
          backgroundColor: 'rgba(53, 162, 235, 0.5)',
          tension: 0.3,
        }
      ]
    };
  };

  // Prepare chart data for status breakdown
  const getStatusBreakdownData = (): ChartData<'bar'> => {
    if (!monitoringData?.database_metrics?.usage_statistics?.by_status) {
      return {
        labels: [],
        datasets: []
      };
    }

    const statusCounts = monitoringData.database_metrics.usage_statistics.by_status;
    const statuses = Object.keys(statusCounts);
    
    return {
      labels: statuses,
      datasets: [
        {
          label: 'Number of Interviews',
          data: statuses.map(status => statusCounts[status] || 0),
          backgroundColor: [
            'rgba(255, 99, 132, 0.5)',
            'rgba(53, 162, 235, 0.5)',
            'rgba(75, 192, 192, 0.5)',
            'rgba(255, 206, 86, 0.5)',
            'rgba(153, 102, 255, 0.5)',
          ],
        }
      ]
    };
  };

  // Prepare chart data for LLM run types
  const getLlmRunTypesData = (): ChartData<'bar'> => {
    if (!monitoringData?.langsmith_metrics?.run_types) {
      return {
        labels: [],
        datasets: []
      };
    }

    const runTypes = monitoringData.langsmith_metrics.run_types;
    const types = Object.keys(runTypes);
    
    return {
      labels: types,
      datasets: [
        {
          label: 'Number of Runs',
          data: types.map(type => runTypes[type] || 0),
          backgroundColor: 'rgba(75, 192, 192, 0.5)',
        }
      ]
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-md">
        <p className="text-red-700">{error}</p>
        <button 
          onClick={() => setTimeRange(timeRange)} 
          className="mt-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!monitoringData) {
    return <div>No monitoring data available</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">System Monitoring</h1>
      
      {/* Time range selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Time Range:</label>
        <div className="flex space-x-2">
          {[1, 7, 14, 30].map(days => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-3 py-1 rounded text-sm ${
                timeRange === days 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
              }`}
            >
              {days === 1 ? 'Today' : `${days} days`}
            </button>
          ))}
        </div>
      </div>
      
      {/* Summary stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-2">Interview Metrics</h2>
          <p className="text-3xl font-bold text-blue-600">
            {monitoringData.database_metrics.total_interviews || 0}
          </p>
          <p className="text-sm text-gray-500">Total interviews processed</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-2">Evaluation Metrics</h2>
          <p className="text-3xl font-bold text-green-600">
            {monitoringData.database_metrics.total_evaluations || 0}
          </p>
          <p className="text-sm text-gray-500">Total evaluations completed</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-2">LLM Metrics</h2>
          <p className="text-3xl font-bold text-purple-600">
            {monitoringData.langsmith_metrics?.total_runs || 0}
          </p>
          <p className="text-sm text-gray-500">Total LLM runs</p>
          <div className="mt-2 flex items-center">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-purple-600 h-2.5 rounded-full" 
                style={{ width: `${(monitoringData.langsmith_metrics?.success_rate || 0) * 100}%` }}
              ></div>
            </div>
            <span className="ml-2 text-sm">
              {Math.round((monitoringData.langsmith_metrics?.success_rate || 0) * 100)}% Success
            </span>
          </div>
        </div>
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Interview Uploads Over Time</h2>
          <Line data={getDailyUsageData()} />
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Interview Status Breakdown</h2>
          <Bar data={getStatusBreakdownData()} />
        </div>
      </div>
      
      {/* LLM specific metrics */}
      <div className="bg-white rounded-lg shadow p-4 mb-8">
        <h2 className="text-lg font-semibold mb-4">LLM Run Types</h2>
        <Bar data={getLlmRunTypesData()} />
      </div>
      
      {/* Last updated info */}
      <div className="text-sm text-gray-500 text-right">
        Last updated: {new Date(monitoringData.timestamp).toLocaleString()}
      </div>
    </div>
  );
}