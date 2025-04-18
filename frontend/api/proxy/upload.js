import { fileURLToPath } from 'url';
import { createReadStream } from 'fs';
import formidable from 'formidable';
import { FormData } from 'formdata-node';
import { fileFromPath } from 'formdata-node/file-from-path';
import fetch from 'node-fetch';

// Disable body parsing for this route
export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Parse the multipart form data with ES module compatible approach
    const form = formidable({ keepExtensions: true });
    
    const formData = await new Promise((resolve, reject) => {
      let fields = {};
      let uploadedFile = null;
      
      // Handle file parts
      form.on('file', (field, file) => {
        uploadedFile = file;
      });
      
      // Handle field parts
      form.on('field', (name, value) => {
        fields[name] = value;
      });
      
      // Handle the end of the form parsing
      form.on('end', () => {
        resolve({ fields, file: uploadedFile });
      });
      
      // Handle errors
      form.on('error', (err) => {
        reject(err);
      });
      
      // Parse the request
      form.parse(req);
    });
    
    // Check if we got a file
    if (!formData.file) {
      return res.status(400).json({ error: 'No file provided' });
    }
    
    // Create a new FormData instance for the backend request
    const backendFormData = new FormData();
    
    // Add the file to the form data
    const uploadFile = await fileFromPath(formData.file.filepath, formData.file.originalFilename || 'file', {
      type: formData.file.mimetype || 'application/octet-stream',
    });
    backendFormData.append('file', uploadFile);
    
    // Add any other fields if needed
    Object.entries(formData.fields).forEach(([key, value]) => {
      backendFormData.append(key, value);
    });

    // Forward auth header if present
    const headers = {};
    if (req.headers.authorization) {
      headers['Authorization'] = req.headers.authorization;
    }

    console.log('Sending file to backend:', {
      fileName: formData.file.originalFilename,
      fileSize: formData.file.size,
      fileType: formData.file.mimetype
    });

    // Send the request to the backend
    const response = await fetch('https://interview-bot-gamma.vercel.app/upload', {
      method: 'POST',
      body: backendFormData,
      headers,
    });

    // Get the response
    const responseText = await response.text();
    let data;
    
    try {
      // Try to parse as JSON
      data = JSON.parse(responseText);
    } catch (e) {
      // If not JSON, return as is
      return res.status(response.status).send(responseText);
    }

    // Return the JSON response
    return res.status(response.status).json(data);
  } catch (error) {
    console.error('File upload proxy error:', error);
    return res.status(500).json({
      error: 'Failed to proxy file upload',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
} 