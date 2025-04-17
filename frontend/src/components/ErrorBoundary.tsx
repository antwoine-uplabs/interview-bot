import { ReactNode } from 'react';
import * as Sentry from '@sentry/react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

const DefaultErrorFallback = () => (
  <div className="min-h-screen flex items-center justify-center bg-red-50">
    <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
      <div className="flex items-center justify-center mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-red-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-center text-gray-800 mb-2">Something went wrong</h1>
      <p className="text-gray-600 text-center mb-6">
        We've encountered an error and our team has been notified.
      </p>
      <div className="flex justify-center">
        <button
          onClick={() => window.location.reload()}
          className="bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded transition-colors"
        >
          Refresh the page
        </button>
      </div>
    </div>
  </div>
);

export default function ErrorBoundaryWrapper({ children, fallback }: ErrorBoundaryProps) {
  const CustomFallback = fallback ? () => <>{fallback}</> : DefaultErrorFallback;
  
  return (
    <Sentry.ErrorBoundary fallback={<CustomFallback />}>
      {children}
    </Sentry.ErrorBoundary>
  );
}