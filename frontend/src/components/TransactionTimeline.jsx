import React from 'react';

/**
 * Section 03: Event Sequence / Chronological Audit Trail.
 * Compact horizontal timeline matching screenshot 1.
 * Dynamically rendered from backend timeline items.
 */
export default function TransactionTimeline({ timeline }) {
  if (!timeline || timeline.length === 0) {
    return (
      <section className="paper-section">
        <div className="paper-section-title-row">
          <div>
            <span className="paper-section-tag">03 / EVENT SEQUENCE</span>
            <h2 className="paper-section-title" style={{ marginTop: '0.15rem' }}>Chronological Audit Trail</h2>
          </div>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          No event sequence records available for this transaction.
        </div>
      </section>
    );
  }

  // Base Reference timestamp from first event
  const baseTime = timeline[0]?.timestamp ? timeline[0].timestamp.slice(11, 19) + ' IST' : 'N/A';

  // Identify any failure point node
  let failureIdx = -1;
  let failureAnnoText = '';

  timeline.forEach((item, idx) => {
    const ev = item.event || '';
    const desc = (item.description || '').toLowerCase();
    if (ev.includes('DELAY') || desc.includes('delay')) {
      failureIdx = idx;
      failureAnnoText = '↑ delay starts here';
    } else if (ev.includes('MISMATCH') || desc.includes('mismatch') || desc.includes('differs')) {
      failureIdx = idx;
      failureAnnoText = '← amount diverges here';
    } else if (ev.includes('MISSING_BANK') || desc.includes('no bank')) {
      failureIdx = idx;
      failureAnnoText = '← bank record missing';
    } else if (ev.includes('MISSING_LEDGER') || desc.includes('no internal ledger')) {
      failureIdx = idx;
      failureAnnoText = '← ledger entry missing';
    } else if (ev.includes('DUPLICATE') || desc.includes('duplicate')) {
      failureIdx = idx;
      failureAnnoText = '← duplicate capture';
    } else if (ev.includes('TIMESTAMP') || desc.includes('violation') || desc.includes('before')) {
      failureIdx = idx;
      failureAnnoText = '← chronology breaks here';
    }
  });

  return (
    <section className="paper-section">
      <div className="paper-section-title-row" style={{ alignItems: 'flex-start' }}>
        <div>
          <span className="paper-section-tag">03 / EVENT SEQUENCE</span>
          <h2 className="paper-section-title" style={{ marginTop: '0.15rem' }}>Chronological Audit Trail</h2>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          Base Reference: T0 = {baseTime}
        </div>
      </div>

      {/* Compact Horizontal Event Timeline */}
      <div className="horizontal-timeline-container">
        <div className="horizontal-timeline-grid">
          {timeline.map((item, idx) => {
            const isFailure = idx === failureIdx;
            const timeStr = item.timestamp ? item.timestamp.slice(11, 19) : 'Pending';

            let eventTitle = item.event.replace(/_/g, ' ');
            if (eventTitle === 'PAYMENT INITIATED') eventTitle = 'Initiation';
            if (eventTitle === 'PAYMENT CAPTURED') eventTitle = 'Capture';
            if (eventTitle === 'BANK RECEIVED') eventTitle = 'Bank Receipt';
            if (eventTitle === 'BANK SETTLED') eventTitle = 'Bank Settled';
            if (eventTitle === 'LEDGER POSTED') eventTitle = 'GL Posting';
            if (eventTitle === 'SETTLEMENT EXPECTED') eventTitle = 'SLA Deadline';

            return (
              <div key={idx} className={`timeline-col ${isFailure ? 'failure-col' : ''}`}>
                <div className={`col-time ${isFailure ? 'fail-text' : ''}`}>{timeStr}</div>
                <div className={`col-title ${isFailure ? 'fail-text' : ''}`}>{eventTitle}</div>
                <div className="col-sub">{item.source}</div>

                {isFailure && failureAnnoText && (
                  <div className="timeline-col-anno">
                    <span className="handwritten-text">{failureAnnoText}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
