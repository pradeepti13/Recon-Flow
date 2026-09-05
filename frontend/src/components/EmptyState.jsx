import React from 'react';
import { FileSearch, Zap } from 'lucide-react';

const FEATURED_DEMOS = [
  { id: 'TXN10001', label: 'Normal Success', desc: 'Verified 3-leg matching settlement' },
  { id: 'TXN10087', label: 'Bank SLA Delay', desc: 'HDFC Bank timeout & systemic incident' },
  { id: 'TXN10142', label: 'Amount Mismatch', desc: 'Discrepancy between Gateway & Bank' },
  { id: 'TXN10211', label: 'Missing Bank Record', desc: 'Gateway captured but missing at Bank' },
  { id: 'TXN10304', label: 'Missing Ledger Record', desc: 'Bank settled but missing internal GL' },
  { id: 'TXN10482', label: 'Duplicate Gateway', desc: 'Multiple capture submissions detected' },
  { id: 'TXN10531', label: 'Timestamp Error', desc: 'Chronological sequence discrepancy' },
  { id: 'TXN09135', label: 'Dataset Transaction', desc: 'Sample from 12,155 master population' },
];

export default function EmptyState({ onSelectPreset }) {
  return (
    <section className="paper-section" style={{ borderTop: 'none', paddingTop: 0 }}>
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-paper)',
          padding: '2rem 1.5rem',
          borderRadius: '2px',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '1rem',
        }}
      >
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8rem',
            fontWeight: 800,
            letterSpacing: '0.12em',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
          }}
        >
          RECON FLOW · SETTLEMENT INVESTIGATION
        </div>

        <p
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.9rem',
            color: 'var(--text-body)',
            maxWidth: '520px',
            margin: '0 auto',
            lineHeight: 1.5,
          }}
        >
          Enter a transaction ID above to generate its reconciliation receipt.
        </p>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            letterSpacing: '0.08em',
            paddingTop: '0.5rem',
            borderTop: '1px dotted var(--border-paper)',
            width: '100%',
            maxWidth: '480px',
          }}
        >
          <span>GATEWAY</span>
          <span>→</span>
          <span>BANK</span>
          <span>→</span>
          <span>LEDGER</span>
        </div>

        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.68rem',
            fontWeight: 700,
            letterSpacing: '0.15em',
            color: 'var(--text-light)',
          }}
        >
          TRACE · RECONCILE · EXPLAIN
        </div>
      </div>
    </section>
  );
}
