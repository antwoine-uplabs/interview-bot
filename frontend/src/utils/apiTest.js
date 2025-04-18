/**
 * Utility to test API connectivity from the frontend
 */

/**
 * Test CORS configuration with the API
 * @param {string} apiUrl - The base URL of the API
 * @returns {Promise<Object>} - The response from the API
 */
export const testApiConnection = async (apiUrl) => {
  try {
    // Use the specific CORS test endpoint
    const response = await fetch(`${apiUrl}/cors-test`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      // Include credentials if your API requires it
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API connection test failed:', error);
    throw error;
  }
};

/**
 * Test the health endpoint
 * @param {string} apiUrl - The base URL of the API
 * @returns {Promise<Object>} - The health status from the API
 */
export const checkApiHealth = async (apiUrl) => {
  try {
    const response = await fetch(`${apiUrl}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Health check failed with status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API health check failed:', error);
    throw error;
  }
};
