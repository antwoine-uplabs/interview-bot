export default async function handler(req, res) {
  try {
    const response = await fetch('https://interview-bot-gamma.vercel.app/health');
    
    if (!response.ok) {
      return res.status(response.status).json({
        status: 'unhealthy',
        error: `Backend returned status ${response.status}`
      });
    }
    
    const data = await response.json();
    return res.status(200).json(data);
  } catch (error) {
    console.error('Health check proxy error:', error);
    return res.status(500).json({
      status: 'unhealthy',
      error: error.message || 'Failed to connect to backend'
    });
  }
} 