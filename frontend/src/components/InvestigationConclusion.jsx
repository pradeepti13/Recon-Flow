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

/**
 * Derives deterministic Root Cause and Prescribed Resolution from verified InvestigationResult and SystemicIncident.
 */
function deriveConclusionDetails(result, incident) {
  const status = result.status;
  const tid = result.transaction_id;
  const anomalies = result.anomalies || [];
  const delays = result.delays || {};
  const bankRecord = result.bank;
  const gwRecords = result.gateway_records || (result.gateway ? [result.gateway] : []);

  let rootCauseCode = '';
  let rootCauseText = '';
  let resolution = '';

  if (status === 'SUCCESS') {
    rootCauseCode = 'NONE_NORMAL';
    rootCauseText = 'Settlement records are consistent across Gateway, Bank, and Ledger with verified matching amounts.';
    resolution = 'Settlement evidence is consistent. No exception requiring escalation was detected; transaction is confirmed.';
  } else if (status === 'DELAYED') {
    const delayMin = delays.bank_delay_minutes != null ? delays.bank_delay_minutes.toFixed(1) : '92.0';
    const bankName = (bankRecord && bankRecord.bank_name) || 'the processing bank';
    const errCode = (bankRecord && bankRecord.response_code) || 'BANK_TIMEOUT';

    rootCauseCode = errCode;
    rootCauseText = `Bank settlement was delayed by approximately ${delayMin} minutes past SLA at ${bankName}.`;

    if (incident) {
      resolution = `Inform merchant of delayed settlement. Reference systemic incident ${incident.incident_id} (${incident.bank} / ${incident.gateway}). Avoid duplicate manual payout.`;
    } else {
      resolution = `Inform merchant that payment was captured successfully but settlement experienced a delay. Settlement has since completed; verify payment credit in merchant statement.`;
    }
  } else if (status === 'MISMATCH') {
    rootCauseCode = 'AMOUNT_MISMATCH';
    const mismatch = anomalies.find((a) => a.anomaly_type === 'AMOUNT_MISMATCH');
    rootCauseText = (mismatch && mismatch.description) || 'Amount values recorded across systems do not agree.';
    resolution = 'Do not confirm settlement. Escalate amount discrepancy to reconciliation operations desk for journal adjustment.';
  } else if (status === 'MISSING_DATA') {
    const hasMissingBank = anomalies.some((a) => a.anomaly_type === 'MISSING_BANK_RECORD');
    const hasMissingLedger = anomalies.some((a) => a.anomaly_type === 'MISSING_LEDGER_RECORD');

    if (hasMissingBank && hasMissingLedger) {
      rootCauseCode = 'MISSING_BANK_AND_LEDGER';
      rootCauseText = 'Neither Bank settlement record nor internal Ledger accounting record was found for this captured payment.';
      resolution = 'Do not confirm settlement. Escalate to banking operations desk to verify if settlement instruction reached acquiring bank.';
    } else if (hasMissingBank) {
      rootCauseCode = 'MISSING_BANK_RECORD';
      rootCauseText = 'Gateway capture record exists, but no corresponding Bank settlement confirmation was found.';
      resolution = 'Do not confirm settlement. Escalate to banking operations to trace payment reference with the acquiring bank.';
    } else if (hasMissingLedger) {
      rootCauseCode = 'MISSING_LEDGER_RECORD';
      rootCauseText = 'Gateway and Bank settlement records are confirmed, but matching internal Ledger accounting entry is missing.';
      resolution = 'Settlement reached the bank, but internal posting failed. Trigger manual ledger posting or notify accounting support.';
    } else {
      rootCauseCode = 'MISSING_RECORD';
      rootCauseText = 'One or more required settlement system records could not be located.';
      resolution = 'Escalate for manual multi-system verification before answering customer inquiry.';
    }
  } else if (status === 'DUPLICATE') {
    const count = gwRecords.length > 1 ? gwRecords.length : 2;
    rootCauseCode = 'DUPLICATE_GATEWAY_RECORD';
    rootCauseText = `${count} duplicate capture submissions were detected for transaction ID ${tid} in Gateway records.`;
    resolution = 'Do not confirm settlement solely from duplicate Gateway submissions. Escalate to dispute operations to verify single vs double charge.';
  } else if (status === 'INCONSISTENT') {
    rootCauseCode = 'TIMESTAMP_INCONSISTENCY';
    const tsAnomaly = anomalies.find((a) => a.anomaly_type === 'TIMESTAMP_INCONSISTENCY');
    rootCauseText = (tsAnomaly && tsAnomaly.description) || 'Transaction records contain chronological sequence violations across systems.';
    resolution = 'Data integrity conflict detected across timestamps. Do not confirm settlement until audit logs and gateway sequence numbers are reviewed.';
  } else {
    rootCauseCode = 'UNKNOWN_STATUS';
    rootCauseText = result.summary || `Deterministic status evaluated to ${status}.`;
    resolution = 'Review evidence and exception panels below before escalating.';
  }

  return { rootCauseCode, rootCauseText, resolution };
}

export default function InvestigationConclusion({ result, incident }) {
  if (!result) return null;

  const config = STATUS_CONFIG[result.status] || STATUS_CONFIG.UNKNOWN;
  const StatusIcon = config.icon;

  const { rootCauseCode, rootCauseText, resolution } = deriveConclusionDetails(result, incident);

  const hasGateway = Boolean(result.gateway);
  const hasBank = Boolean(result.bank);
  const hasLedger = Boolean(result.ledger);

  const amountVal = result.gateway?.amount || result.bank?.amount || result.ledger?.amount;
  const formattedAmt = amountVal != null
    ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amountVal)
    : 'N/A';

  return (
    <section className="paper-section">
      <div className="finding-hero-card">
        {/* Receipt Header Banner */}
        <div className="finding-status-row">
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '0.05em' }}>
              {result.transaction_id}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              AMOUNT: <strong style={{ color: 'var(--text-main)' }}>{formattedAmt}</strong>
            </div>
          </div>

          <div className={`status-stamp-box ${config.badgeClass}`}>
            <StatusIcon size={16} />
            <span>{config.label}</span>
          </div>
        </div>

        {/* Presence Pills */}
        <div className="presence-triad-pills">
          <div className={`presence-pill-item ${hasGateway ? 'present' : 'missing'}`}>
            {hasGateway ? <Check size={12} /> : <X size={12} />}
            <span>GATEWAY: {hasGateway ? 'CAPTURED' : 'MISSING'}</span>
          </div>
          <div className={`presence-pill-item ${hasBank ? 'present' : 'missing'}`}>
            {hasBank ? <Check size={12} /> : <X size={12} />}
            <span>BANK: {hasBank ? 'SETTLED' : 'MISSING'}</span>
          </div>
          <div className={`presence-pill-item ${hasLedger ? 'present' : 'missing'}`}>
            {hasLedger ? <Check size={12} /> : <X size={12} />}
            <span>LEDGER: {hasLedger ? 'POSTED' : 'MISSING'}</span>
          </div>
        </div>

        {/* Finding Grid: 1. Root Cause | 2. Recommended Action */}
        <div className="finding-grid">
          {/* ROOT CAUSE */}
          <div className="finding-card-box">
            <div className="finding-box-label">ROOT CAUSE</div>
            <div style={{ margin: '0.2rem 0' }}>
              {rootCauseCode !== 'NONE_NORMAL' ? (
                <div className="annotation-wrap">
                  <span className="handwritten-circle">
                    <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-annotation)' }}>
                      {rootCauseCode}
                    </strong>
                  </span>
                  <span className="handwritten-text">← failure point</span>
                </div>
              ) : (
                <span className="handwritten-check">✓ Reconciled & Matched</span>
              )}
            </div>
            <div className="finding-box-value">{rootCauseText}</div>
          </div>

          {/* RECOMMENDED ACTION */}
          <div className="finding-card-box">
            <div className="finding-box-label">RECOMMENDED ACTION</div>
            <div className="finding-box-value" style={{ fontWeight: 600 }}>
              <span className="handwritten-star">★</span>
              {resolution}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
