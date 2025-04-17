import { EvaluationResult } from '../services/api';

/**
 * Export evaluation results to CSV
 */
export function exportToCSV(evaluation: EvaluationResult): void {
  // Create CSV content
  const rows: string[] = [];
  
  // Add header
  rows.push('Candidate Name, Overall Score, Criterion, Score, Justification');
  
  // Add data rows
  evaluation.criteria.forEach(criterion => {
    rows.push(
      `${escapeCsvValue(evaluation.candidateName)}, ${evaluation.overallScore}, ${escapeCsvValue(criterion.name)}, ${criterion.score}, ${escapeCsvValue(criterion.justification)}`
    );
  });
  
  // Create a blob from the CSV content
  const csvContent = rows.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  
  // Create a link to download the CSV file
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `${evaluation.candidateName.replace(/\s+/g, '_')}_evaluation.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Export evaluation results to JSON
 */
export function exportToJSON(evaluation: EvaluationResult): void {
  // Create a blob from the JSON content
  const jsonContent = JSON.stringify(evaluation, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
  
  // Create a link to download the JSON file
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `${evaluation.candidateName.replace(/\s+/g, '_')}_evaluation.json`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Export evaluation results to PDF
 * This is a basic implementation using the browser's print functionality
 * For a production app, you would use a library like jsPDF
 */
export function exportToPDF(evaluation: EvaluationResult): void {
  // Create a new window to print
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups for this website to export PDF');
    return;
  }
  
  // Create HTML content for the PDF
  const htmlContent = `
    <html>
      <head>
        <title>${evaluation.candidateName} - Evaluation Report</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          h1 { color: #1a56db; }
          h2 { color: #1a56db; margin-top: 20px; }
          .score { font-size: 24px; font-weight: bold; }
          .good { color: #16a34a; }
          .average { color: #2563eb; }
          .poor { color: #dc2626; }
          .criterion { margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb; }
          .criterion h3 { margin-bottom: 5px; }
          .supporting { margin-left: 20px; font-style: italic; color: #6b7280; }
          .section { margin-top: 20px; }
        </style>
      </head>
      <body>
        <h1>${evaluation.candidateName} - Evaluation Report</h1>
        
        <div class="section">
          <h2>Overall Score</h2>
          <p class="score ${getScoreClass(evaluation.overallScore)}">${evaluation.overallScore.toFixed(1)}/10</p>
        </div>
        
        <div class="section">
          <h2>Summary</h2>
          <p>${evaluation.summary}</p>
        </div>
        
        ${evaluation.strengths && evaluation.strengths.length > 0 ? `
          <div class="section">
            <h2>Strengths</h2>
            <ul>
              ${evaluation.strengths.map(strength => `<li>${strength}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
        
        ${evaluation.weaknesses && evaluation.weaknesses.length > 0 ? `
          <div class="section">
            <h2>Areas for Improvement</h2>
            <ul>
              ${evaluation.weaknesses.map(weakness => `<li>${weakness}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
        
        <div class="section">
          <h2>Criteria Evaluation</h2>
          
          ${evaluation.criteria.map(criterion => `
            <div class="criterion">
              <h3>${criterion.name}</h3>
              <p class="${getScoreClass(criterion.score)}">Score: ${criterion.score}/10</p>
              <p>${criterion.justification}</p>
              
              ${criterion.supporting_quotes && criterion.supporting_quotes.length > 0 ? `
                <div class="supporting">
                  <p>Supporting Evidence:</p>
                  <ul>
                    ${criterion.supporting_quotes.map(quote => `<li>"${quote}"</li>`).join('')}
                  </ul>
                </div>
              ` : ''}
            </div>
          `).join('')}
        </div>
        
        <div style="margin-top: 30px; text-align: center; color: #6b7280; font-size: 12px;">
          Generated on ${new Date().toLocaleString()}
        </div>
      </body>
    </html>
  `;
  
  // Write the HTML content to the new window
  printWindow.document.write(htmlContent);
  printWindow.document.close();
  
  // Wait for the window to load before printing
  printWindow.onload = () => {
    printWindow.print();
  };
}

// Helper function to escape CSV values
function escapeCsvValue(value: string): string {
  // If the value contains commas, quotes, or newlines, wrap it in quotes
  if (/[",\n\r]/.test(value)) {
    // Replace quotes with double quotes
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

// Helper function to get the CSS class for a score
function getScoreClass(score: number): string {
  if (score >= 8) return 'good';
  if (score >= 6) return 'average';
  return 'poor';
}