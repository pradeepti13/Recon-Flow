import React, { useState } from 'react';
import { Bot, Check, Copy } from 'lucide-react';

/**
 * Section 06: AI Support Explanation component.
 * Displays plain-English explanation generated strictly from verified deterministic context.
 * Secondary to deterministic evidence. Includes copyable merchant notice.
 */
export default function AIExplanationPanel({ explanation, loading }) {
  const [copied, setCopied] = useState(false);

  if (!loading && !explanation) return null;

  const handleCopy = () => {
    if (explanation?.customer_facing_explanation) {
      navigator.clipboard.writeText(explanation.customer_facing_explanation);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <section className="paper-section">
      <div className="paper-section-title-row">
        <h2 className="paper-section-title">AI EXPLANATION</h2>
        <span className="paper-section-subtitle">Generated from verified investigation evidence</span>
      </div>

      <div className="ai-narrative-panel">
        {loading && (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Generating AI explanation from verified investigation evidence...
          </div>
        )}

        {!loading && explanation && (
          <>
            {/* Fallback vs Live Notice */}
            {explanation.is_fallback ? (
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', borderBottom: '1px dotted var(--border-paper)', paddingBottom: '0.5rem' }}>
                AI PROVIDER NOT CONFIGURED · Displaying verified deterministic summary.
              </div>
            ) : (
              <div style={{ fontSize: '0.78rem', color: 'var(--color-success)', fontFamily: 'var(--font-mono)', borderBottom: '1px dotted var(--border-paper)', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Bot size={14} />
                <span>Generated from verified evidence. No facts invented by AI.</span>
              </div>
            )}

            {/* Factual Narrative Paragraph */}
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', lineHeight: '1.55', color: 'var(--text-body)' }}>
              {explanation.summary} {explanation.root_cause && `Root Cause: ${explanation.root_cause}`}
            </div>

            {/* Ready to Copy Merchant Notice */}
            <div className="merchant-notice-box">
              <div className="notice-header">
                <span className="notice-title">MERCHANT NOTICE</span>
                <button type="button" className="btn-copy-notice" onClick={handleCopy}>
                  {copied ? (
                    <>
                      <Check size={12} style={{ display: 'inline', marginRight: '4px' }} />
                      COPIED
                    </>
                  ) : (
                    <>
                      <Copy size={12} style={{ display: 'inline', marginRight: '4px' }} />
                      COPY TEXT
                    </>
                  )}
                </button>
              </div>
              <p className="notice-text">"{explanation.customer_facing_explanation}"</p>
            </div>

            {/* Receipt Footer Line */}
            <div className="paper-footer-line">
              <span>RECON FLOW SETTLEMENT INVESTIGATION RECEIPT</span>
              <span>SIMULATED ENVIRONMENT</span>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
