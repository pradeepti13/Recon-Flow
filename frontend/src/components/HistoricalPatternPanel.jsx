import React from 'react';
import { AlertTriangle, History } from 'lucide-react';

/**
 * Systemic Incident & Historical Pattern Analysis component.
 * Displays correlated systemic incident telemetry and historical recurrence logs.
 * Strictly 100% backend-derived — no hardcoded metrics or fake signatures.
 */
export default function HistoricalPatternPanel({ incident, pattern }) {
  const hasIncident = Boolean(incident);
  const hasPattern = Boolean(pattern && pattern.has_historical_pattern);

  if (!hasIncident && !hasPattern) {
    return null;
  }

  const formattedIncidentAmount = incident
    ? new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
      }).format(incident.affected_amount)
    : null;

  return (
    <section className="paper-section">
      <div className="incident-historical-split">
        {/* Left Column: Systemic Incident Telemetry */}
        {hasIncident ? (
          <div className="incident-box">
            <div className="incident-box-title">
              <AlertTriangle size={16} />
              <span>!! SYSTEMIC INCIDENT DETECTED</span>
              <span className="handwritten-text" style={{ fontSize: '1.05rem', color: 'var(--color-annotation)', marginLeft: 'auto' }}>
                same cluster →
              </span>
            </div>

            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--text-main)', fontWeight: 700 }}>
              {incident.bank} · {incident.gateway} · {incident.dominant_error}
            </div>

            <div className="incident-kpis">
              <div className="inc-kpi-item">
                <span className="inc-kpi-val">{incident.affected_transaction_count} TXNS</span>
                <span className="inc-kpi-lbl">AFFECTED</span>
              </div>
              <div className="inc-kpi-item">
                <span className="inc-kpi-val" style={{ color: 'var(--color-delayed)' }}>
                  {formattedIncidentAmount}
                </span>
                <span className="inc-kpi-lbl">VALUE IMPACT</span>
              </div>
              <div className="inc-kpi-item">
                <span className="inc-kpi-val" style={{ fontSize: '0.85rem' }}>
                  {incident.start_time?.slice(11, 16)}–{incident.end_time?.slice(11, 16)}
                </span>
                <span className="inc-kpi-lbl">WINDOW</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="historical-box" style={{ background: 'var(--bg-paper-subtle)' }}>
            <div className="historical-box-title">SYSTEMIC INCIDENT</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              No systemic cluster detected for this transaction.
            </div>
          </div>
        )}

        {/* Right Column: Historical Pattern Frequency */}
        {hasPattern ? (
          <div className="historical-box">
            <div className="historical-box-title">HISTORICAL PATTERN</div>

            <div className="historical-occ-list">
              {pattern.previous_occurrences?.map((occ) => (
                <div key={occ.incident_id} className="occ-item">
                  <span>{occ.date}</span>
                  <strong>{occ.affected_transaction_count} TXNS</strong>
                </div>
              ))}
              {pattern.current_occurrence && (
                <div className="occ-item current">
                  <span>{pattern.current_occurrence.date}</span>
                  <strong>{pattern.current_occurrence.affected_transaction_count} TXNS (CURRENT)</strong>
                </div>
              )}
            </div>

            {pattern.comparison_summary && (
              <div className="handwritten-text" style={{ fontSize: '1.05rem', color: 'var(--color-annotation)', marginTop: '0.25rem' }}>
                {pattern.comparison_summary}
              </div>
            )}
          </div>
        ) : (
          <div className="historical-box" style={{ background: 'var(--bg-paper-subtle)' }}>
            <div className="historical-box-title">HISTORICAL PATTERN</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {pattern?.comparison_summary || 'No previous occurrences observed in historical logs.'}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
