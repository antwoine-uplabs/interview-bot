import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { EvaluationCriterion } from '../../services/api';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartProps {
  criteria: EvaluationCriterion[];
}

export default function BarChart({ criteria }: BarChartProps) {
  // Sort criteria by score in descending order
  const sortedCriteria = [...criteria].sort((a, b) => b.score - a.score);
  
  const labels = sortedCriteria.map(c => c.name);
  const scores = sortedCriteria.map(c => c.score);
  
  // Assign colors based on score
  const getBarColor = (score: number) => {
    if (score >= 8) return 'rgba(34, 197, 94, 0.7)'; // green
    if (score >= 6) return 'rgba(59, 130, 246, 0.7)'; // blue
    return 'rgba(239, 68, 68, 0.7)'; // red
  };
  
  const barColors = scores.map(score => getBarColor(score));
  const borderColors = barColors.map(color => color.replace('0.7', '1'));
  
  const data = {
    labels,
    datasets: [
      {
        label: 'Score',
        data: scores,
        backgroundColor: barColors,
        borderColor: borderColors,
        borderWidth: 1,
      },
    ],
  };
  
  const options = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: { formattedValue: string }) {
            return `Score: ${context.formattedValue}/10`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 10,
        ticks: {
          stepSize: 2,
        },
        title: {
          display: true,
          text: 'Score',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Skills',
        },
      },
    },
  };
  
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-medium mb-4">Skills Comparison</h3>
      <div className="w-full">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}