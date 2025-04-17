import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import './index.css'
import App from './App.tsx'

// Initialize Sentry
Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [
    // @ts-ignore - Disable React Router integration for now
    // Sentry.reactRouterV6BrowserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  // Performance monitoring
  tracesSampleRate: 1.0, // Capture 100% of transactions in development, adjust for production
  // Session replay
  replaysSessionSampleRate: 0.1, // Capture 10% of sessions for replay
  replaysOnErrorSampleRate: 1.0, // Capture all sessions with errors
  environment: import.meta.env.MODE,
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
