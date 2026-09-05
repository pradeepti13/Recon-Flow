import React from 'react';
import { CheckCircle2, AlertTriangle } from 'lucide-react';

/**
 * Section 05: Verified Evidence & Exceptions working paper component.
 * Displays audit checklist verification and concise variance metrics.
 */
export default function EvidencePanel({ evidence, exceptions, delays, status, result }) {
  const evList = evidence || [];
  const excList = exceptions || [];

  // Compute variance metrics dynamically from investigation props
  const delayMin = delays?.bank_delay_minutes != null ? delays.bank_delay_minutes : result?.delays?.bank_delay_minutes;
  const slaVarianceText = delayMin != null && delayMin > 0 ? `+${delayMin.toFixed(1)} minutes breach` : 'Within SLA (0m)';

  const gwAmt = result?.gateway?.amount;
  const bnkAmt = result?.bank?.amount;
  const mismatchDiff = (status === 'MISMATCH' && gwAmt != null && bnkAmt != null) ? Math.abs(gwAmt - bnkAmt) : 0;
  const mismatchText = mismatchDiff > 0 ? `₹${mismatchDiff.toLocaleString('en-IN')}` : 'Nil (0.00)';

  const gwRecords = result?.gateway_records || (result?.gateway ? [result.gateway] : []);
  const dupText = gwRecords.length > 1 ? `${gwRecords.length} submissions` : 'Zero detected';

  return (
    <section className="paper-section">
      <div className="evidence-split">
        {/* Left Column: Audit Checklist Verification */}
        <div className="evidence-card">
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
            VERIFICATION CHECKLIST
          </div>

          <ul className="evidence-list-items">
            {evList.map((item, idx) => (
              <li key={idx} className="evidence-item-row">
                <CheckCircle2 size={15} style={{ color: 'var(--color-success)', flexShrink: 0, marginTop: '2px' }} />
                <span>{item}</span>
              </li>
            ))}
            {excList.map((item, idx) => (
              <li key={`exc-${idx}`} className="evidence-item-row">
                <AlertTriangle size={15} style={{ color: 'var(--color-delayed)', flexShrink: 0, marginTop: '2px' }} />
                <span style={{ color: 'var(--color-delayed)', fontWeight: 600 }}>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Right Column: Concise Variance Summary */}
        <div className="evidence-card">
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
            VARIANCE SUMMARY
          </div>

          <div className="variance-summary-grid">
            <div className="variance-row">
              <span style={{ color: 'var(--text-muted)' }}>SLA Variance:</span>
              <span className="leg-val-mono" style={{ color: delayMin > 0 ? 'var(--color-delayed)' : 'var(--color-success)', fontWeight: 700 }}>
                {slaVarianceText}
              </span>
            </div>

            <div className="variance-row">
              <span style={{ color: 'var(--text-muted)' }}>Amount Discrepancy:</span>
              <span className="leg-val-mono" style={{ color: mismatchDiff > 0 ? 'var(--color-mismatch)' : 'var(--color-success)', fontWeight: 700 }}>
                {mismatchText}
              </span>
            </div>

            <div className="variance-row">
              <span style={{ color: 'var(--text-muted)' }}>Duplicate Submissions:</span>
              <span className="leg-val-mono" style={{ color: gwRecords.length > 1 ? 'var(--color-duplicate)' : 'var(--color-success)', fontWeight: 700 }}>
                {dupText}
              </span>
            </div>

            <div className="variance-row">
              <span style={{ color: 'var(--text-muted)' }}>Confidence Score:</span>
              <span className="leg-val-mono" style={{ fontWeight: 800 }}>
                {result?.confidence?.score || 100}/100 ({result?.confidence?.level || 'HIGH'})
              </span>
            </div>
          </div>

          <div className="handwritten-text" style={{ fontSize: '1rem', color: 'var(--text-muted)', marginTop: 'auto', textAlign: 'right' }}>
            Verified from System Records
          </div>
        </div>
      </div>
    </section>
  );
}
