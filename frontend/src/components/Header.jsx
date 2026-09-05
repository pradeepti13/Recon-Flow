import React from 'react';

export default function Header({ health, healthError }) {
  return (
    <header className="paper-header">
      <div className="paper-brand">
        <h1 className="paper-title">RECON FLOW</h1>
        <span className="paper-subtitle">
          SETTLEMENT INVESTIGATION RECEIPT
        </span>
      </div>

      <div className="paper-stamps">
        <span className="stamp-badge simulated">
          SIMULATED ENVIRONMENT
        </span>

        {health && (
          <span className="stamp-badge online">
            API CONNECTED (v{health.version})
          </span>
        )}
        {healthError && (
          <span className="stamp-badge offline" style={{ borderColor: '#dc2626', color: '#dc2626' }}>
            API OFFLINE
          </span>
        )}
      </div>
    </header>
  );
}
