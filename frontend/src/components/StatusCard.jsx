import React from 'react';
import {
  CheckCircle2,
  Clock,
  AlertOctagon,
  FileQuestion,
  Copy,
  Shuffle,
  HelpCircle,
  Check,
  X,
} from 'lucide-react';

const STATUS_CONFIG = {
  SUCCESS: {
    icon: CheckCircle2,
    label: 'SETTLEMENT SUCCESSFUL',
    badgeClass: 'status-SUCCESS',
  },
  DELAYED: {
    icon: Clock,
    label: 'SETTLEMENT DELAYED',
    badgeClass: 'status-DELAYED',
  },
  MISMATCH: {
    icon: AlertOctagon,
    label: 'AMOUNT MISMATCH DETECTED',
    badgeClass: 'status-MISMATCH',
  },
  MISSING_DATA: {
    icon: FileQuestion,
    label: 'MISSING SYSTEM RECORD',
    badgeClass: 'status-MISSING_DATA',
  },
  DUPLICATE: {
    icon: Copy,
    label: 'DUPLICATE SUBMISSION DETECTED',
    badgeClass: 'status-DUPLICATE',
  },
  INCONSISTENT: {
    icon: Shuffle,
    label: 'TIMESTAMP INCONSISTENCY',
    badgeClass: 'status-INCONSISTENT',
  },
  UNKNOWN: {
    icon: HelpCircle,
    label: 'TRANSACTION UNKNOWN',
    badgeClass: 'status-UNKNOWN',
  },
};

export default function StatusCard({ result }) {
  if (!result) return null;

  const config = STATUS_CONFIG[result.status] || STATUS_CONFIG.UNKNOWN;
  const StatusIcon = config.icon;

  const hasGateway = Boolean(result.gateway);
  const hasBank = Boolean(result.bank);
  const hasLedger = Boolean(result.ledger);

  return (
    <div className="status-card">
      <div className="status-card-header">
        <div className={`status-badge-hero ${config.badgeClass}`}>
          <StatusIcon size={22} />
          <span>{config.label}</span>
        </div>
        <div style={{ fontFamily: 'monospace', color: '#94a3b8', fontSize: '0.85rem' }}>
          ID: {result.transaction_id}
        </div>
      </div>

      <p className="status-summary-text">{result.summary}</p>

      <div className="status-presence-triad">
        <div className={`presence-pill ${hasGateway ? 'present' : 'missing'}`}>
          {hasGateway ? <Check size={14} /> : <X size={14} />}
          <span>Gateway: {hasGateway ? 'Captured' : 'Missing'}</span>
        </div>
        <div className={`presence-pill ${hasBank ? 'present' : 'missing'}`}>
          {hasBank ? <Check size={14} /> : <X size={14} />}
          <span>Bank: {hasBank ? 'Settled' : 'Missing'}</span>
        </div>
        <div className={`presence-pill ${hasLedger ? 'present' : 'missing'}`}>
          {hasLedger ? <Check size={14} /> : <X size={14} />}
          <span>Ledger: {hasLedger ? 'Posted' : 'Missing'}</span>
        </div>
      </div>
    </div>
  );
}
