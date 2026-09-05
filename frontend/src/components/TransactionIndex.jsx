import React, { useState, useEffect, useCallback } from 'react';
import { getTransactions } from '../api';
import { Search, ChevronLeft, ChevronRight, Filter } from 'lucide-react';

const FILTER_MODES = [
  { id: 'ALL', label: 'ALL' },
  { id: 'NORMAL', label: 'NORMAL' },
  { id: 'ANOMALIES', label: 'ANOMALIES' },
  { id: 'SYSTEMIC', label: 'SYSTEMIC' },
];

const ANOMALY_STATUSES = [
  { id: '', label: 'ANY STATUS' },
  { id: 'DELAYED', label: 'DELAYED' },
  { id: 'MISMATCH', label: 'MISMATCH' },
  { id: 'MISSING_DATA', label: 'MISSING DATA' },
  { id: 'DUPLICATE', label: 'DUPLICATE' },
  { id: 'INCONSISTENT', label: 'INCONSISTENT' },
];

export default function TransactionIndex({ onSelectTransaction, activeTxnId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [filterMode, setFilterMode] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('');

  const fetchIndex = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTransactions({
        page,
        pageSize,
        search,
        status: statusFilter,
        filterType: filterMode,
      });
      setData(res);
    } catch (err) {
      console.error('Failed to load transaction index:', err);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, filterMode, statusFilter]);

  useEffect(() => {
    fetchIndex();
  }, [fetchIndex]);

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleFilterModeChange = (mode) => {
    setFilterMode(mode);
    setPage(1);
  };

  const handleStatusFilterChange = (e) => {
    setStatusFilter(e.target.value);
    setPage(1);
  };

  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  return (
    <section className="paper-section">
      <div className="paper-section-title-row">
        <h2 className="paper-section-title">TRANSACTION INDEX</h2>
        {data && (
          <span className="paper-section-subtitle">
            {data.total.toLocaleString()} MATCHING ({data.total_normal.toLocaleString()} NORMAL · {data.total_anomalies.toLocaleString()} ANOMALOUS)
          </span>
        )}
      </div>

      {/* Dataset KPI Summary Bar */}
      {data && (
        <div style={{
          display: 'flex',
          gap: '1rem',
          flexWrap: 'wrap',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          padding: '0.5rem 0.85rem',
          backgroundColor: 'var(--bg-paper-subtle)',
          border: '1px solid var(--border-paper)',
          borderRadius: '2px',
        }}>
          <div><strong>12,155</strong> TOTAL</div>
          <div>• <strong style={{ color: 'var(--color-success)' }}>{data.total_normal.toLocaleString()}</strong> NORMAL</div>
          <div>• <strong style={{ color: 'var(--color-delayed)' }}>{data.total_anomalies.toLocaleString()}</strong> ANOMALOUS</div>
          <div>• <strong style={{ color: 'var(--color-duplicate)' }}>{data.total_systemic.toLocaleString()}</strong> SYSTEMIC</div>
        </div>
      )}

      {/* Controls: Search + Filter Tabs */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Search Input */}
          <div style={{ flex: 1, minWidth: '200px', display: 'flex', alignItems: 'center', backgroundColor: '#fff', border: '1px solid var(--border-strong)', padding: '0.35rem 0.6rem', borderRadius: '2px' }}>
            <Search size={14} style={{ color: 'var(--text-muted)', marginRight: '0.4rem' }} />
            <input
              type="text"
              placeholder="Search transaction ID..."
              value={search}
              onChange={handleSearchChange}
              style={{
                border: 'none',
                outline: 'none',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8rem',
                width: '100%',
                backgroundColor: 'transparent',
              }}
            />
          </div>

          {/* Status Dropdown Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Filter size={14} style={{ color: 'var(--text-muted)' }} />
            <select
              value={statusFilter}
              onChange={handleStatusFilterChange}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.75rem',
                padding: '0.35rem 0.6rem',
                border: '1px solid var(--border-strong)',
                borderRadius: '2px',
                backgroundColor: '#fff',
                color: 'var(--text-main)',
              }}
            >
              {ANOMALY_STATUSES.map((s) => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Filter Tabs */}
        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
          {FILTER_MODES.map((mode) => (
            <button
              key={mode.id}
              type="button"
              className={`preset-chip ${filterMode === mode.id ? 'active' : ''}`}
              style={{
                backgroundColor: filterMode === mode.id ? 'var(--text-main)' : '#ffffff',
                color: filterMode === mode.id ? '#ffffff' : 'var(--text-body)',
                borderColor: filterMode === mode.id ? 'var(--text-main)' : 'var(--border-paper)',
              }}
              onClick={() => handleFilterModeChange(mode.id)}
            >
              [ {mode.label} ]
            </button>
          ))}
        </div>
      </div>

      {/* Transaction Register Table */}
      <div className="tri-party-table-container">
        <table className="tri-party-table">
          <thead>
            <tr>
              <th>TRANSACTION ID</th>
              <th>STATUS</th>
              <th>FINDING / ANOMALY</th>
              <th>AMOUNT</th>
              <th>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem' }}>
                  Loading transaction index...
                </td>
              </tr>
            )}

            {!loading && data && data.transactions.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem' }}>
                  No transactions match current filters.
                </td>
              </tr>
            )}

            {!loading && data && data.transactions.map((tx) => {
              const isSelected = activeTxnId === tx.transaction_id;
              const formatAmount = tx.amount != null
                ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(tx.amount)
                : 'N/A';

              let statusColor = 'var(--color-success)';
              if (tx.status === 'DELAYED' || tx.status === 'INCONSISTENT') statusColor = 'var(--color-delayed)';
              if (tx.status === 'MISMATCH') statusColor = 'var(--color-mismatch)';
              if (tx.status === 'MISSING_DATA') statusColor = 'var(--color-missing)';
              if (tx.status === 'DUPLICATE') statusColor = 'var(--color-duplicate)';

              return (
                <tr
                  key={tx.transaction_id}
                  style={{
                    backgroundColor: isSelected ? 'var(--bg-paper-subtle)' : 'transparent',
                    cursor: 'pointer',
                  }}
                  onClick={() => onSelectTransaction(tx.transaction_id)}
                >
                  <td style={{ fontWeight: 800 }}>
                    {tx.transaction_id}
                    {tx.is_systemic && (
                      <span style={{ fontSize: '0.65rem', color: 'var(--color-delayed)', marginLeft: '0.35rem', fontWeight: 800 }}>
                        [SYSTEMIC]
                      </span>
                    )}
                  </td>
                  <td>
                    <span style={{ color: statusColor, fontWeight: 700 }}>
                      {tx.status}
                    </span>
                  </td>
                  <td>
                    <span style={{ color: tx.anomaly_type ? 'var(--text-main)' : 'var(--text-muted)' }}>
                      {tx.anomaly_type || 'NORMAL_SETTLEMENT'}
                    </span>
                  </td>
                  <td style={{ fontWeight: 700 }}>{formatAmount}</td>
                  <td>
                    <button
                      type="button"
                      className="btn-copy-notice"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectTransaction(tx.transaction_id);
                      }}
                    >
                      INVESTIGATE →
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {data && data.total > 0 && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          paddingTop: '0.4rem',
        }}>
          <div>
            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, data.total)} of {data.total.toLocaleString()}
          </div>
          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
            <button
              type="button"
              className="btn-copy-notice"
              disabled={page <= 1 || loading}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft size={12} /> PREV
            </button>
            <span>Page {page} of {totalPages}</span>
            <button
              type="button"
              className="btn-copy-notice"
              disabled={page >= totalPages || loading}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              NEXT <ChevronRight size={12} />
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
