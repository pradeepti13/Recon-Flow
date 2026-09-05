import React from 'react';
import { AlertTriangle, TrendingDown, Users, Clock, DollarSign } from 'lucide-react';

export default function IncidentBanner({ incident }) {
  if (!incident) return null;

  const formattedAmount = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(incident.affected_amount);

  return (
    <div className="incident-banner">
      <div className="incident-banner-header">
        <div className="incident-title-group">
          <AlertTriangle className="incident-icon" />
          <div>
            <h3 className="incident-title">
              SYSTEMIC INCIDENT DETECTED: {incident.bank} Outage
            </h3>
            <span style={{ fontSize: '0.8rem', color: '#fca5a5' }}>
              Individual delay is part of a broader infrastructure failure
            </span>
          </div>
        </div>
        <span className="incident-badge-severity">
          {incident.severity} SEVERITY
        </span>
      </div>

      <div className="incident-kpis">
        <div className="incident-kpi-card">
          <div className="incident-kpi-label">Affected Transactions</div>
          <div className="incident-kpi-value">{incident.affected_transaction_count} txns</div>
        </div>
        <div className="incident-kpi-card">
          <div className="incident-kpi-label">Settlement Volume at Risk</div>
          <div className="incident-kpi-value" style={{ color: '#f87171' }}>
            {formattedAmount}
          </div>
        </div>
        <div className="incident-kpi-card">
          <div className="incident-kpi-label">Outage Window</div>
          <div className="incident-kpi-value">
            {incident.start_time?.slice(11, 16)} – {incident.end_time?.slice(11, 16)}
          </div>
        </div>
        <div className="incident-kpi-card">
          <div className="incident-kpi-label">Common Delay Range</div>
          <div className="incident-kpi-value" style={{ color: '#fbbf24' }}>
            {incident.common_delay_range_minutes?.[0]}m – {incident.common_delay_range_minutes?.[1]}m
          </div>
        </div>
      </div>

      {incident.detection_reasons && incident.detection_reasons.length > 0 && (
        <div>
          <span style={{ fontSize: '0.78rem', color: '#fca5a5', fontWeight: 600 }}>
            Incident Evidence & Pattern Reasons:
          </span>
          <ul className="incident-reasons-list">
            {incident.detection_reasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
