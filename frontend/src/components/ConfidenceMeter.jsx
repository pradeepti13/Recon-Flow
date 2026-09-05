import React from 'react';
import { ShieldCheck, ArrowUpRight, AlertCircle } from 'lucide-react';

export default function ConfidenceMeter({ confidence }) {
  if (!confidence) return null;

  const { score, level, factors = [] } = confidence;

  // Derive color palette based on confidence band
  let barColor = '#10b981'; // VERY_HIGH
  if (score < 50) barColor = '#f43f5e'; // LOW
  else if (score < 75) barColor = '#f59e0b'; // MEDIUM
  else if (score < 90) barColor = '#3b82f6'; // HIGH

  return (
    <div className="panel-container">
      <h4 className="panel-title">
        <ShieldCheck size={18} style={{ color: barColor }} />
        Deterministic Evidence Confidence
      </h4>

      <div className="confidence-meter-container">
        <div className="confidence-score-hero">
          <span className="score-num" style={{ color: barColor }}>
            {score}
          </span>
          <span className="score-denom">/ 100</span>
          <span
            style={{
              marginLeft: 'auto',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '0.25rem 0.65rem',
              borderRadius: '9999px',
              backgroundColor: `${barColor}22`,
              color: barColor,
              border: `1px solid ${barColor}55`,
            }}
          >
            {level} CONFIDENCE
          </span>
        </div>

        <div className="confidence-bar-bg">
          <div
            className="confidence-bar-fill"
            style={{
              width: `${Math.max(4, score)}%`,
              backgroundColor: barColor,
            }}
          />
        </div>

        {factors.length > 0 && (
          <div style={{ marginTop: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>
              Contributing Factors:
            </span>
            <ul className="confidence-factors-list" style={{ marginTop: '0.35rem' }}>
              {factors.map((factor, idx) => (
                <li key={idx}>{factor}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
