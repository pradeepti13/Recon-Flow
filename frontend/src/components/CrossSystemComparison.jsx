import React from 'react';

/**
 * Tri-Party Reconciliation Ledger working-paper comparison.
 * Aligned 3-leg comparison: Gateway Leg, Banking Rail, Internal Ledger.
 * All values derived dynamically from investigation props.
 */
export default function CrossSystemComparison({
  gateway,
  gatewayRecords,
  bank,
  ledger,
  status,
}) {
  const gwRecords = gatewayRecords || (gateway ? [gateway] : []);

  // Format currency helper
  const formatAmt = (val) =>
    val != null
      ? new Intl.NumberFormat('en-IN', {
          style: 'currency',
          currency: 'INR',
        }).format(val)
      : 'N/A (Missing)';

  // Dynamic reconciliation summary statement
  let reconSummary = '';
  let summaryClass = 'reconciliation-success';

  if (status === 'SUCCESS') {
    reconSummary = '✓ Mathematical Parity: 100% matched across 3 system records (No disparity)';
    summaryClass = 'reconciliation-success';
  } else if (status === 'MISMATCH') {
    const gwAmt = gateway?.amount;
    const bnkAmt = bank?.amount;
    const diff = gwAmt != null && bnkAmt != null ? Math.abs(gwAmt - bnkAmt) : 0;
    reconSummary = `⚠ Amount Discrepancy: Gateway (${formatAmt(gwAmt)}) vs Bank (${formatAmt(bnkAmt)}) — Variance: ${formatAmt(diff)}`;
    summaryClass = 'reconciliation-alert';
  } else if (status === 'MISSING_DATA') {
    if (!bank && !ledger) {
      reconSummary = '⚠ Record Disparity: Neither Bank nor Ledger records were located for this captured payment.';
    } else if (!bank) {
      reconSummary = '⚠ Record Disparity: Gateway capture confirmed, but Bank settlement record is MISSING.';
    } else {
      reconSummary = '⚠ Record Disparity: Bank settlement confirmed, but internal Ledger entry is MISSING.';
    }
    summaryClass = 'reconciliation-alert';
  } else if (status === 'DUPLICATE') {
    reconSummary = `⚠ Data Integrity Issue: ${gwRecords.length} duplicate Gateway capture records detected for ID.`;
    summaryClass = 'reconciliation-alert';
  } else if (status === 'INCONSISTENT') {
    reconSummary = '⚠ Sequence Exception: Bank settlement timestamp precedes Gateway initiation time.';
    summaryClass = 'reconciliation-alert';
  } else {
    reconSummary = `Audit Status: Evaluated to ${status}. Review leg details below.`;
    summaryClass = 'reconciliation-alert';
  }

  return (
    <section className="paper-section">
      <div className="paper-section-title-row">
        <h2 className="paper-section-title">PAYMENT RECORD</h2>
        <span className="paper-section-subtitle">Tri-Party Reconciliation</span>
      </div>

      <div className="tri-party-table-container">
        <table className="tri-party-table">
          <thead>
            <tr>
              <th>GATEWAY</th>
              <th>BANK</th>
              <th>LEDGER</th>
            </tr>
          </thead>
          <tbody>
            {/* Row 1: System / Provider */}
            <tr>
              <td>
                <span className="leg-source-tag">PROVIDER: </span>
                <span className="leg-val-mono">{gateway?.merchant_id ? `${gateway.merchant_id}` : 'GATEWAY'}</span>
              </td>
              <td>
                <span className="leg-source-tag">BANK: </span>
                <span className="leg-val-mono">{bank?.bank_name || 'MISSING'}</span>
              </td>
              <td>
                <span className="leg-source-tag">ENTRY: </span>
                <span className="leg-val-mono">{ledger?.ledger_entry_id ? `#${ledger.ledger_entry_id}` : 'GENERAL LEDGER'}</span>
              </td>
            </tr>

            {/* Row 2: Status */}
            <tr>
              <td>
                <span className="leg-source-tag">STATUS: </span>
                <span className="leg-val-mono" style={{ color: gateway ? 'var(--color-success)' : 'var(--color-missing)' }}>
                  {gateway?.gateway_status || 'MISSING'}
                </span>
              </td>
              <td>
                <span className="leg-source-tag">STATUS: </span>
                <span
                  className="leg-val-mono"
                  style={{
                    color: bank
                      ? bank.bank_status === 'SETTLED' && status === 'DELAYED'
                        ? 'var(--color-delayed)'
                        : 'var(--color-success)'
                      : 'var(--color-missing)',
                  }}
                >
                  {bank ? (status === 'DELAYED' ? 'DELAYED' : bank.bank_status) : 'MISSING'}
                </span>
              </td>
              <td>
                <span className="leg-source-tag">STATUS: </span>
                <span className="leg-val-mono" style={{ color: ledger ? 'var(--color-success)' : 'var(--color-missing)' }}>
                  {ledger?.ledger_status || 'MISSING'}
                </span>
              </td>
            </tr>

            {/* Row 3: Amount */}
            <tr>
              <td>
                <span className="leg-source-tag">AMOUNT: </span>
                <span className="leg-val-amount">{formatAmt(gateway?.amount)}</span>
              </td>
              <td>
                <span className="leg-source-tag">AMOUNT: </span>
                <span
                  className="leg-val-amount"
                  style={{ color: status === 'MISMATCH' ? 'var(--color-mismatch)' : 'inherit' }}
                >
                  {formatAmt(bank?.amount)}
                </span>
              </td>
              <td>
                <span className="leg-source-tag">AMOUNT: </span>
                <span className="leg-val-amount">{formatAmt(ledger?.amount)}</span>
              </td>
            </tr>

            {/* Row 4: Timestamp / Code */}
            <tr>
              <td>
                <span className="leg-source-tag">TIME: </span>
                <span className="leg-val-mono">{gateway?.initiated_at ? gateway.initiated_at.slice(11, 19) : 'N/A'}</span>
              </td>
              <td>
                <span className="leg-source-tag">CODE: </span>
                <span className="leg-val-mono" style={{ color: bank?.response_code !== '00' && bank?.response_code !== 'SETTLED_OK' ? 'var(--color-delayed)' : 'inherit' }}>
                  {bank?.response_code || 'N/A'}
                </span>
              </td>
              <td>
                <span className="leg-source-tag">TIME: </span>
                <span className="leg-val-mono">{ledger?.created_at ? ledger.created_at.slice(11, 19) : 'N/A'}</span>
              </td>
            </tr>
          </tbody>
        </table>

        {/* Bottom Reconciliation Parity Summary */}
        <div className="reconciliation-summary-bar">
          <span
            className="handwritten-text"
            style={{
              fontSize: '1.1rem',
              color: summaryClass === 'reconciliation-success' ? 'var(--color-annotation-green)' : 'var(--color-annotation)',
            }}
          >
            {reconSummary}
          </span>
        </div>
      </div>
    </section>
  );
}
