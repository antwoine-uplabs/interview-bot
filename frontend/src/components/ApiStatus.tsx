import { useState, useEffect } from 'react';
import { healthCheck } from '../services/api';
import supabase from '../services/supabase';

export default function ApiStatus() {
  const [apiStatus, setApiStatus] = useState<'loading' | 'connected' | 'disconnected'>('loading');
  const [supabaseStatus, setSupabaseStatus] = useState<'loading' | 'connected' | 'disconnected'>('loading');
  const [error, setError] = useState<string | null>(null);
  const [details, setDetails] = useState<{ [key: string]: string } | null>(null);

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const result = await healthCheck();
        setApiStatus(result.status === 'ok' ? 'connected' : 'disconnected');
        setDetails(result.dependencies || null);
        setError(null);
      } catch (err) {
        setApiStatus('disconnected');
        setError('Failed to connect to API');
        console.error('API health check failed:', err);
      }
    };
    
    const checkSupabaseStatus = async () => {
      try {
        // Simple Supabase check - get the auth configuration
        const { error } = await supabase.auth.getSession();
        
        if (error) {
          setSupabaseStatus('disconnected');
          console.error('Supabase connection error:', error);
        } else {
          setSupabaseStatus('connected');
        }
      } catch (err) {
        setSupabaseStatus('disconnected');
        console.error('Supabase check failed:', err);
      }
    };

    checkApiStatus();
    checkSupabaseStatus();
    
    // Check every 30 seconds
    const apiInterval = setInterval(checkApiStatus, 30000);
    const supabaseInterval = setInterval(checkSupabaseStatus, 30000);
    
    return () => {
      clearInterval(apiInterval);
      clearInterval(supabaseInterval);
    };
  }, []);

  return (
    <div className="mt-4 text-xs text-gray-500 flex items-center gap-2 flex-wrap">
      <span>API:</span>
      {apiStatus === 'loading' && (
        <span className="flex items-center">
          <span className="animate-pulse h-2 w-2 rounded-full bg-gray-400 mr-1"></span>
          Checking
        </span>
      )}
      {apiStatus === 'connected' && (
        <span className="flex items-center">
          <span className="h-2 w-2 rounded-full bg-green-500 mr-1"></span>
          Connected
        </span>
      )}
      {apiStatus === 'disconnected' && (
        <span className="flex items-center">
          <span className="h-2 w-2 rounded-full bg-red-500 mr-1"></span>
          Disconnected
          {error && <span className="ml-1 text-red-500">({error})</span>}
        </span>
      )}
      
      <span className="ml-3">Auth:</span>
      {supabaseStatus === 'loading' && (
        <span className="flex items-center">
          <span className="animate-pulse h-2 w-2 rounded-full bg-gray-400 mr-1"></span>
          Checking
        </span>
      )}
      {supabaseStatus === 'connected' && (
        <span className="flex items-center">
          <span className="h-2 w-2 rounded-full bg-green-500 mr-1"></span>
          Connected
        </span>
      )}
      {supabaseStatus === 'disconnected' && (
        <span className="flex items-center">
          <span className="h-2 w-2 rounded-full bg-red-500 mr-1"></span>
          Disconnected
        </span>
      )}
      
      {details && apiStatus === 'connected' && (
        <div className="ml-2">
          {Object.entries(details).map(([key, value]) => (
            <span 
              key={key}
              className={`ml-2 ${value === 'connected' ? 'text-green-600' : 'text-orange-500'}`}
            >
              {key}: {value}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}