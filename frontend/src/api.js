/**
 * API client for Recon Flow.
 * Communicates with FastAPI backend for health, transaction investigation, and systemic incidents.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Health check endpoint ping.
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    if (!response.ok) {
      throw new Error(`Health check failed with status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API health check error:', error);
    throw error;
  }
}

/**
 * Investigates a transaction deterministically across Gateway, Bank, and Ledger.
 * Authoritative source of truth for transaction existence and verification.
 * 
 * @param {string} transactionId
 * @returns {Promise<import('./types').InvestigationResult>}
 */
export async function investigateTransaction(transactionId) {
  const tid = (transactionId || '').trim();
  if (!tid) {
    throw { status: 400, detail: 'Please enter a valid transaction ID.' };
  }

  const response = await fetch(`${API_BASE_URL}/api/investigate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transaction_id: tid }),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail || (response.status === 404
      ? `Transaction not found: '${tid}' was not found in simulated Gateway, Bank, or Ledger records.`
      : `Request failed with status ${response.status}`);
    throw { status: response.status, detail };
  }

  if (!data.ok || !data.result) {
    throw { status: 500, detail: 'Invalid response format from investigation engine.' };
  }

  return data.result;
}

/**
 * Checks if a transaction is associated with an active systemic incident.
 * Returns { is_systemic: boolean, incident: SystemicIncident | null }.
 * 
 * @param {string} transactionId
 * @returns {Promise<{ is_systemic: boolean, incident: any }>}
 */
export async function getTransactionIncident(transactionId) {
  const tid = (transactionId || '').trim();
  if (!tid) {
    return { is_systemic: false, incident: null };
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/incidents/transaction/${encodeURIComponent(tid)}`);
    if (!response.ok) {
      return { is_systemic: false, incident: null };
    }
    return await response.json();
  } catch (error) {
    console.warn('Systemic incident check non-blocking failure:', error);
    return { is_systemic: false, incident: null };
  }
}

/**
 * Fetches all currently active systemic incidents.
 * 
 * @returns {Promise<Array<any>>}
 */
export async function getActiveIncidents() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/incidents`);
    if (!response.ok) {
      return [];
    }
    return await response.json();
  } catch (error) {
    console.warn('Get active incidents failure:', error);
    return [];
  }
}

/**
 * Fetches historical pattern intelligence for a transaction.
 * Returns HistoricalPatternResult object.
 *
 * @param {string} transactionId
 * @returns {Promise<object>}
 */
export async function getHistoricalPattern(transactionId) {
  const tid = (transactionId || '').trim();
  if (!tid) {
    return { has_historical_pattern: false };
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/incidents/transaction/${encodeURIComponent(tid)}/history`);
    if (!response.ok) {
      return { has_historical_pattern: false };
    }
    return await response.json();
  } catch (error) {
    console.warn('Historical pattern check non-blocking failure:', error);
    return { has_historical_pattern: false };
  }
}

/**
 * Requests an LLM-generated plain-English explanation for a completed investigation.
 *
 * Accepts the already-computed deterministic investigation result, optional incident,
 * and optional historical pattern.
 * Always resolves (never rejects) — the backend always returns HTTP 200.
 * When the LLM is unavailable, the backend returns a deterministic fallback with
 * explanation.is_fallback === true.
 *
 * @param {object} investigation - InvestigationResult from investigateTransaction()
 * @param {object|null} incident - SystemicIncident or null
 * @param {object|null} historicalPattern - HistoricalPatternResult or null
 * @returns {Promise<{summary, root_cause, recommended_action, customer_facing_explanation, uncertainty, is_fallback, fallback_reason}>}
 */
export async function explainTransaction(investigation, incident, historicalPattern) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        investigation,
        incident: incident || null,
        historical_pattern: historicalPattern || null,
      }),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok || !data || !data.ok) {
      // Unexpected HTTP error — return a client-side fallback shape
      return {
        summary: investigation.summary || 'Investigation complete.',
        root_cause: 'AI explanation service error.',
        recommended_action: 'Review the deterministic evidence panel above.',
        customer_facing_explanation: 'Please refer to the investigation details.',
        uncertainty: 'AI explanation unavailable. Showing deterministic summary.',
        is_fallback: true,
        fallback_reason: `HTTP ${response.status} from /api/explain`,
      };
    }

    return data.explanation;
  } catch (error) {
    console.warn('AI explanation request failed (non-blocking):', error);
    // Client-side network failure — return a safe fallback
    return {
      summary: investigation.summary || 'Investigation complete.',
      root_cause: 'AI explanation service unreachable.',
      recommended_action: 'Review the deterministic evidence panel above.',
      customer_facing_explanation: 'Please refer to the investigation details.',
      uncertainty: 'AI explanation unavailable. Showing deterministic summary.',
      is_fallback: true,
      fallback_reason: error.message || 'Network error',
    };
  }
}

/**
 * Fetches a paginated, filterable list of transactions from the dataset index.
 *
 * @param {object} params - { page, pageSize, search, status, filterType, anomalyType }
 * @returns {Promise<{transactions: Array, page: number, page_size: number, total: number, total_normal: number, total_anomalies: number, total_systemic: number}>}
 */
export async function getTransactions({ page = 1, pageSize = 25, search = '', status = '', filterType = '', anomalyType = '' } = {}) {
  const query = new URLSearchParams();
  query.append('page', page);
  query.append('page_size', pageSize);
  if (search) query.append('search', search);
  if (status) query.append('status', status);
  if (filterType) query.append('filter_type', filterType);
  if (anomalyType) query.append('anomaly_type', anomalyType);

  try {
    const response = await fetch(`${API_BASE_URL}/api/transactions?${query.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch transactions index (HTTP ${response.status})`);
    }
    return await response.json();
  } catch (error) {
    console.error('getTransactions API error:', error);
    return {
      transactions: [],
      page: 1,
      page_size: pageSize,
      total: 0,
      total_normal: 0,
      total_anomalies: 0,
      total_systemic: 0,
    };
  }
}


