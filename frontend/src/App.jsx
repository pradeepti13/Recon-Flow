import React, { useState, useEffect } from 'react';
import { checkHealth } from './api';

function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0f172a',
      color: '#f8fafc',
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      padding: '2rem'
    }}>
      <header style={{
        borderBottom: '1px solid #334155',
        paddingBottom: '1.5rem',
        marginBottom: '2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.025em' }}>
            Settlement Intelligence
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', color: '#94a3b8', fontSize: '0.875rem' }}>
            AI-Powered Settlement Investigation & Systemic Incident Detection
          </p>
        </div>
        <span style={{
          fontSize: '0.75rem',
          padding: '0.25rem 0.75rem',
          borderRadius: '9999px',
          backgroundColor: '#1e293b',
          color: '#38bdf8',
          border: '1px solid #38bdf833'
        }}>
          Phase 0: Environment Ready
        </span>
      </header>

      <main style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{
          backgroundColor: '#1e293b',
          borderRadius: '8px',
          padding: '1.5rem',
          border: '1px solid #334155'
        }}>
          <h2 style={{ fontSize: '1.125rem', marginTop: 0, marginBottom: '1rem' }}>
            System Status Check
          </h2>
          {loading && (
            <p style={{ color: '#94a3b8' }}>Checking backend connectivity...</p>
          )}
          {error && (
            <div style={{
              backgroundColor: '#ef44441a',
              border: '1px solid #ef4444',
              color: '#fca5a5',
              padding: '0.75rem 1rem',
              borderRadius: '6px'
            }}>
              Backend connection error: {error}
            </div>
          )}
          {health && (
            <div>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                backgroundColor: '#10b9811a',
                border: '1px solid #10b981',
                color: '#6ee7b7',
                padding: '0.5rem 0.75rem',
                borderRadius: '6px',
                marginBottom: '1rem',
                fontSize: '0.875rem'
              }}>
                <span>●</span>
                <span>FastAPI Backend Connected ({health.service} v{health.version})</span>
              </div>
              <pre style={{
                backgroundColor: '#0f172a',
                padding: '1rem',
                borderRadius: '6px',
                fontSize: '0.8125rem',
                color: '#cbd5e1',
                overflowX: 'auto',
                border: '1px solid #334155'
              }}>
                {JSON.stringify(health, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
