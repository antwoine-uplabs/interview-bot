export default async function handler(req, res) {
  const targetUrl = 'https://interview-bot-gamma.vercel.app';
  const path = req.url.replace(/^\/api\/proxy/, '');
  
  // Add a trailing slash if needed
  const requestPath = path || '/';
  
  try {
    console.log(`Proxying request to: ${targetUrl}${requestPath}`);
    
    const fetchOptions = {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        // Forward authorization headers if present
        ...(req.headers.authorization && { 
          'Authorization': req.headers.authorization 
        })
      }
    };
    
    // Add body for non-GET requests
    if (req.method !== 'GET' && req.method !== 'HEAD' && req.body) {
      fetchOptions.body = JSON.stringify(req.body);
    }
    
    const response = await fetch(`${targetUrl}${requestPath}`, fetchOptions);
    
    // Get response data
    let data;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }
    
    // Set response status and headers
    res.status(response.status);
    
    // Forward response headers
    const headers = response.headers;
    headers.forEach((value, key) => {
      // Skip host-related headers
      if (!['connection', 'content-length'].includes(key.toLowerCase())) {
        res.setHeader(key, value);
      }
    });
    
    // Send the response
    if (typeof data === 'object') {
      res.json(data);
    } else {
      res.send(data);
    }
  } catch (error) {
    console.error('API proxy error:', error);
    res.status(500).json({ 
      error: 'Failed to proxy request',
      message: error.message
    });
  }
} 