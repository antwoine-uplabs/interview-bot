export default async function handler(req, res) {
  const targetUrl = 'https://interview-bot-gamma.vercel.app';
  const path = req.url.replace(/^\/api\/proxy/, '');
  
  // Add a trailing slash if needed
  const requestPath = path || '/';
  
  try {
    console.log(`Proxying request to: ${targetUrl}${requestPath}`);
    
    // Extract the content type from the request
    const contentType = req.headers['content-type'] || '';
    
    // Set up base fetch options
    const fetchOptions = {
      method: req.method,
      headers: {
        // Don't set content-type for multipart requests, let the browser set it with the boundary
        ...(!contentType.includes('multipart/form-data') && { 'Content-Type': contentType }),
        // Forward authorization headers if present
        ...(req.headers.authorization && { 
          'Authorization': req.headers.authorization 
        })
      }
    };
    
    // Handle different types of request bodies
    if (req.method !== 'GET' && req.method !== 'HEAD' && req.body) {
      if (contentType.includes('multipart/form-data')) {
        // For file uploads, we need to pass the raw request
        // This requires special handling in Vercel serverless functions
        const { readBody } = await import('@vercel/node');
        const rawBody = await readBody(req, true);
        fetchOptions.body = rawBody;
        
        // Pass through content-type with boundary
        fetchOptions.headers['Content-Type'] = contentType;
      } else if (contentType.includes('application/json')) {
        // For JSON data, we can stringify
        fetchOptions.body = JSON.stringify(req.body);
      } else {
        // For other data types, pass as is
        fetchOptions.body = req.body;
      }
    }
    
    const response = await fetch(`${targetUrl}${requestPath}`, fetchOptions);
    
    // Get response data
    let data;
    const responseContentType = response.headers.get('content-type');
    if (responseContentType && responseContentType.includes('application/json')) {
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