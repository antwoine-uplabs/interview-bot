import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import ResetPassword from './components/auth/ResetPassword';
import Dashboard from './components/Dashboard';
import ProtectedRoute from './components/auth/ProtectedRoute';
import ApiStatus from './components/ApiStatus';
import ErrorBoundaryWrapper from './components/ErrorBoundary';
import './App.css';

function App() {
  const [debug, setDebug] = useState({
    error: null as string | null,
    supabaseUrl: import.meta.env.VITE_SUPABASE_URL || 'Not set',
    hasAnonKey: !!import.meta.env.VITE_SUPABASE_ANON_KEY,
    baseUrl: window.location.href
  });

  useEffect(() => {
    // Add an error handler to catch unhandled errors
    const handleError = (event: ErrorEvent) => {
      setDebug(prev => ({
        ...prev,
        error: `${event.message} at ${event.filename}:${event.lineno}`
      }));
      console.error("Captured in error handler:", event);
    };

    window.addEventListener('error', handleError);
    
    return () => {
      window.removeEventListener('error', handleError);
    };
  }, []);

  // Simple debug view to help identify the issue
  const showDebugInfo = import.meta.env.MODE === 'development' || window.location.href.includes('debug=true');
  
  if (showDebugInfo) {
    return (
      <div className="p-8 bg-gray-100 min-h-screen">
        <h1 className="text-2xl font-bold mb-4">Frontend Debug Page</h1>
        
        <div className="mb-6 p-4 bg-white rounded shadow">
          <h2 className="text-xl font-semibold mb-2">Environment Information</h2>
          <ul className="list-disc pl-5">
            <li>Base URL: {debug.baseUrl}</li>
            <li>Supabase URL: {debug.supabaseUrl}</li>
            <li>Supabase Anon Key: {debug.hasAnonKey ? 'Set' : 'Not set'}</li>
            <li>Mode: {import.meta.env.MODE}</li>
          </ul>
        </div>
        
        {debug.error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-300 rounded shadow">
            <h2 className="text-xl font-semibold mb-2 text-red-600">Error Detected</h2>
            <p className="font-mono text-red-800">{debug.error}</p>
          </div>
        )}
        
        <div className="mb-6">
          <button
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded"
            onClick={() => {
              try {
                localStorage.setItem('test', 'test');
                alert('LocalStorage is working!');
              } catch (err) {
                alert('LocalStorage error: ' + (err instanceof Error ? err.message : String(err)));
              }
            }}
          >
            Test LocalStorage
          </button>
        </div>
        
        <div className="mt-8">
          <a href="/" className="text-blue-500 hover:underline">
            Continue to App
          </a>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundaryWrapper>
      <AuthProvider>
        <Router>
          <div className="App min-h-screen bg-gray-100">
            <ApiStatus />
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/debug" element={<div>Debug Mode</div>} />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ErrorBoundaryWrapper>
  );
}

export default App;