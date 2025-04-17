import React from 'react';
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
import { EvaluationCriterion } from '../../services/api';

// Register ChartJS components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

interface RadarChartProps {
  criteria: EvaluationCriterion[];
}

export default function RadarChart({ criteria }: RadarChartProps) {
  const labels = criteria.map(c => c.name);
  const scores = criteria.map(c => c.score);
  
  const data = {
    labels,
    datasets: [
      {
        label: 'Skills Assessment',
        data: scores,
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(59, 130, 246, 1)',
      },
    ],
  };

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

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-medium mb-4">Skills Assessment Radar</h3>
      <div className="w-full">
        <Radar data={data} options={options} />
      </div>
    </div>
  );
}