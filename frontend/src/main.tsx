import React from 'react';
import ReactDOM from 'react-dom/client';
import { ClerkProvider } from '@clerk/clerk-react';
import App from './App';
import './index.css';

const clerkPublishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

if (!clerkPublishableKey) {
  console.warn('[Clerk] Missing VITE_CLERK_PUBLISHABLE_KEY. Please configure in your environment.');
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {clerkPublishableKey ? (
      <ClerkProvider publishableKey={clerkPublishableKey}>
        <App />
      </ClerkProvider>
    ) : (
      <App />
    )}
  </React.StrictMode>,
);
