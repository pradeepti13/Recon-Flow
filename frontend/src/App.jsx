import React, { useState, useEffect, useCallback, useRef } from 'react';
import './styles/dashboard.css';

import {
  checkHealth,
  investigateTransaction,
  getTransactionIncident,
  getHistoricalPattern,
  explainTransaction,
} from './api';

import Header from './components/Header';
import SearchBar from './components/SearchBar';
import InvestigationConclusion from './components/InvestigationConclusion';
import CrossSystemComparison from './components/CrossSystemComparison';
import TransactionTimeline from './components/TransactionTimeline';
import HistoricalPatternPanel from './components/HistoricalPatternPanel';
import EvidencePanel from './components/EvidencePanel';
import EmptyState from './components/EmptyState';
import AIExplanationPanel from './components/AIExplanationPanel';

import { AlertCircle, RefreshCw } from 'lucide-react';

export default function App() {
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [incident, setIncident] = useState(null);
  const [historicalPattern, setHistoricalPattern] = useState(null);
  const [error, setError] = useState(null);

  // Phase 7: AI explanation state — separate from deterministic investigation state
  const [explanation, setExplanation] = useState(null);
  const [explanationLoading, setExplanationLoading] = useState(false);

  // Guard against stale async responses during rapid sequential searches
  const searchSequenceRef = useRef(0);

  // Initial health check
  useEffect(() => {
    checkHealth()
      .then((data) => {
        setHealth(data);
        setHealthError(null);
      })
      .catch((err) => {
        console.warn('Backend offline:', err);
        setHealthError(err.message || 'API unreachable');
      });
  }, []);

  // Main investigation search handler
  const handleSearch = useCallback(async (txnId) => {
    const cleanId = (txnId || '').trim();
    if (!cleanId) return;

    // Increment search sequence token
    const currentSeq = ++searchSequenceRef.current;

    setLoading(true);
    setError(null);
    setResult(null);
    setIncident(null);
    setHistoricalPattern(null);
    setExplanation(null);
    setExplanationLoading(false);

    try {
      // 1. Concurrently call investigation, systemic association & historical pattern
      const [investigationData, incidentData, historicalData] = await Promise.all([
        investigateTransaction(cleanId),
        getTransactionIncident(cleanId).catch(() => ({ is_systemic: false, incident: null })),
        getHistoricalPattern(cleanId).catch(() => ({ has_historical_pattern: false })),
      ]);

      // Guard: If another search was initiated, ignore this response
      if (currentSeq !== searchSequenceRef.current) return;

      setResult(investigationData);

      const associatedIncident = (incidentData && incidentData.is_systemic && incidentData.incident)
        ? incidentData.incident
        : null;
      setIncident(associatedIncident);
      setHistoricalPattern(historicalData);

      // 2. Fetch AI explanation asynchronously without blocking primary deterministic UI
      setExplanationLoading(true);
      explainTransaction(investigationData, associatedIncident, historicalData)
        .then((aiExp) => {
          if (currentSeq === searchSequenceRef.current) {
            setExplanation(aiExp);
          }
        })
        .catch((aiErr) => {
          console.warn('Explain failed:', aiErr);
        })
        .finally(() => {
          if (currentSeq === searchSequenceRef.current) {
            setExplanationLoading(false);
          }
        });
    } catch (err) {
      if (currentSeq !== searchSequenceRef.current) return;
      console.error('Investigation error:', err);
      setError({
        status: err.status || 500,
        detail: err.detail || 'An unexpected error occurred while investigating.',
      });
      setResult(null);
      setIncident(null);
      setHistoricalPattern(null);
      setExplanation(null);
      setExplanationLoading(false);
    } finally {
      if (currentSeq === searchSequenceRef.current) {
        setLoading(false);
      }
    }
  }, []);

  return (
    <div className="dashboard-container">
      {/* Single Continuous Financial Working Paper Sheet */}
      <main className="working-paper-sheet">
        {/* Header with simulated data badge & health status */}
        <Header health={health} healthError={healthError} />

        {/* Query Docket Input & Presets */}
        <SearchBar
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          onSearch={handleSearch}
          loading={loading}
        />

        {/* Loading Skeleton State */}
        {loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div className="skeleton-line" style={{ height: '140px' }} />
            <div className="skeleton-line" style={{ height: '220px' }} />
            <div className="skeleton-line" style={{ height: '180px' }} />
          </div>
        )}

        {/* Error & 404 States */}
        {!loading && error && (
          <div className="error-paper-state">
            <AlertCircle
              size={36}
              style={{ color: error.status === 404 ? '#64748b' : '#dc2626', marginBottom: '0.75rem' }}
            />
            <h3 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', margin: '0 0 0.5rem', color: 'var(--text-main)' }}>
              {error.status === 404 ? 'Transaction Not Found (HTTP 404)' : 'Investigation Error'}
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', margin: '0 0 1.25rem' }}>
              {error.detail}
            </p>
            <button
              type="button"
              className="btn-docket-investigate"
              style={{ margin: '0 auto', backgroundColor: '#334155' }}
              onClick={() => {
                setSearchTerm('TXN10001');
                handleSearch('TXN10001');
              }}
            >
              <RefreshCw size={14} />
              Reset with Sample Docket (TXN10001)
            </button>
          </div>
        )}

        {/* Empty State when no search has occurred */}
        {!loading && !error && !result && (
          <EmptyState />
        )}

        {/* Active Investigation Document */}
        {!loading && !error && result && (
          <>
            {/* 01 / PRIMARY DOCKET FINDING */}
            <InvestigationConclusion result={result} incident={incident} />

            {/* 02 / LEDGER ACCOUNTING (Tri-Party Reconciliation) */}
            <CrossSystemComparison
              gateway={result.gateway}
              gatewayRecords={result.gateway_records}
              bank={result.bank}
              ledger={result.ledger}
              status={result.status}
            />

            {/* 03 / EVENT SEQUENCE (Chronological Audit Trail) */}
            <TransactionTimeline timeline={result.timeline} />

            {/* 04 / INCIDENT CORRELATION & TELEMETRY */}
            <HistoricalPatternPanel incident={incident} pattern={historicalPattern} />

            {/* 05 / EVIDENTIARY CHECKLIST & VARIANCE SUMMARY */}
            <EvidencePanel
              evidence={result.evidence}
              exceptions={result.exceptions}
              delays={result.delays}
              status={result.status}
              result={result}
            />

            {/* 06 / SUBORDINATE INVESTIGATION NARRATIVE (AI Explanation) */}
            <AIExplanationPanel
              explanation={explanation}
              loading={explanationLoading}
            />
          </>
        )}
      </main>
    </div>
  );
}
