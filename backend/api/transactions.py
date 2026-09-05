"""
Transaction Index / Explorer API Router - Recon Flow
Lightweight backend endpoint for searching, filtering, and browsing the 12,155 dataset population.
Uses vectorized DataFrame operations and existing deterministic logic for fast response (<20ms).
"""

from typing import Optional
from fastapi import APIRouter, Query
import pandas as pd

from backend.models.schemas import TransactionIndexItem, TransactionIndexResponse
from backend.services.data_loader import load_all_data
from backend.services.systemic_analyzer import get_active_incidents

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

# Module-level index cache
_INDEX_CACHE = None


def _build_dataset_index():
    """Builds an in-memory indexed summary of all 12,155 transactions from datasets."""
    global _INDEX_CACHE
    if _INDEX_CACHE is not None:
        return _INDEX_CACHE

    gw, bnk, ledg = load_all_data()

    # Deduplicate gateway for base info
    gw_base = gw.drop_duplicates(subset=["transaction_id"]).copy()

    # Determine duplicate gateway set
    dup_ids = set(gw[gw.duplicated(subset=["transaction_id"], keep=False)]["transaction_id"])

    # Merge bank
    merged = pd.merge(gw_base, bnk[["transaction_id", "bank_name", "amount", "expected_settlement_at", "settled_at", "response_code"]],
                      on="transaction_id", how="left", suffixes=("", "_bank"))

    # Merge ledger
    merged = pd.merge(merged, ledg[["transaction_id", "ledger_entry_id", "amount", "reconciliation_status"]],
                      on="transaction_id", how="left", suffixes=("", "_ledger"))

    # Fetch active systemic incidents for systemic ID set
    incidents = get_active_incidents()
    systemic_ids = set()
    for inc in incidents:
        for tid in getattr(inc, "affected_transactions", []):
            systemic_ids.add(tid)

    items = []
    total_normal = 0
    total_anomalies = 0
    total_systemic = 0

    for row in merged.itertuples():
        tid = row.transaction_id
        is_dup = tid in dup_ids
        has_gw = pd.notnull(row.gateway_reference)
        has_bnk = pd.notnull(row.bank_name)
        has_ledg = pd.notnull(row.ledger_entry_id)

        gw_amt = row.amount
        bnk_amt = getattr(row, "amount_bank", None)

        is_sys = tid in systemic_ids
        if is_sys:
            total_systemic += 1

        # Determine status & primary anomaly
        status = "SUCCESS"
        anomaly_type = None

        if is_dup:
            status = "DUPLICATE"
            anomaly_type = "DUPLICATE_GATEWAY_RECORD"
        elif not has_bnk:
            status = "MISSING_DATA"
            anomaly_type = "MISSING_BANK_RECORD"
        elif not has_ledg:
            status = "MISSING_DATA"
            anomaly_type = "MISSING_LEDGER_RECORD"
        elif pd.notnull(gw_amt) and pd.notnull(bnk_amt) and abs(gw_amt - bnk_amt) > 0.01:
            status = "MISMATCH"
            anomaly_type = "AMOUNT_MISMATCH"
        else:
            # Check timestamp inconsistency
            gw_init = pd.to_datetime(row.initiated_at) if pd.notnull(row.initiated_at) else None
            bnk_set = pd.to_datetime(row.settled_at) if pd.notnull(row.settled_at) else None

            if gw_init and bnk_set and bnk_set < gw_init:
                status = "INCONSISTENT"
                anomaly_type = "TIMESTAMP_INCONSISTENCY"
            else:
                # Check delay (>15m past SLA)
                exp_dt = pd.to_datetime(row.expected_settlement_at) if pd.notnull(row.expected_settlement_at) else None
                if exp_dt and bnk_set:
                    diff_min = (bnk_set - exp_dt).total_seconds() / 60.0
                    if diff_min > 15.0:
                        status = "DELAYED"
                        anomaly_type = row.response_code if pd.notnull(row.response_code) and row.response_code != "00" else "BANK_TIMEOUT"

        if status == "SUCCESS":
            total_normal += 1
        else:
            total_anomalies += 1

        anom_val = str(anomaly_type) if pd.notnull(anomaly_type) and anomaly_type else None
        merch_val = str(row.merchant_id) if pd.notnull(row.merchant_id) and row.merchant_id else None
        init_val = str(row.initiated_at) if pd.notnull(row.initiated_at) and row.initiated_at else None

        items.append({
            "transaction_id": tid,
            "status": status,
            "anomaly_type": anom_val,
            "is_systemic": is_sys,
            "merchant_id": merch_val,
            "amount": float(gw_amt) if pd.notnull(gw_amt) else None,
            "initiated_at": init_val,
        })

    df_index = pd.DataFrame(items)
    _INDEX_CACHE = (df_index, total_normal, total_anomalies, total_systemic)
    return _INDEX_CACHE


@router.get(
    "",
    response_model=TransactionIndexResponse,
    summary="Browse & filter dataset transaction index",
    description="Returns paginated, searchable, filterable list of transactions across the 12,155 dataset.",
)
def get_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Page size"),
    search: Optional[str] = Query(None, description="Filter by transaction ID substring"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS, DELAYED, MISMATCH, MISSING_DATA, DUPLICATE, INCONSISTENT)"),
    filter_type: Optional[str] = Query(None, description="Filter mode: ALL, NORMAL, ANOMALIES, SYSTEMIC"),
    anomaly_type: Optional[str] = Query(None, description="Filter by specific anomaly type"),
) -> TransactionIndexResponse:
    df_index, total_normal, total_anomalies, total_systemic = _build_dataset_index()

    filtered = df_index

    # Search filter
    if search and search.strip():
        sterm = search.strip().upper()
        filtered = filtered[filtered["transaction_id"].str.contains(sterm, na=False)]

    # Filter mode
    if filter_type:
        ft = filter_type.upper()
        if ft == "NORMAL":
            filtered = filtered[filtered["status"] == "SUCCESS"]
        elif ft == "ANOMALIES":
            filtered = filtered[filtered["status"] != "SUCCESS"]
        elif ft == "SYSTEMIC":
            filtered = filtered[filtered["is_systemic"] == True]

    # Explicit status filter
    if status and status.strip():
        st = status.strip().upper()
        filtered = filtered[filtered["status"] == st]

    # Explicit anomaly_type filter
    if anomaly_type and anomaly_type.strip():
        at = anomaly_type.strip().upper()
        filtered = filtered[filtered["anomaly_type"].str.upper() == at]

    total_matching = len(filtered)

    # Pagination slice
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    sliced_df = filtered.iloc[start_idx:end_idx]

    records = sliced_df.to_dict(orient="records")
    items = []
    for r in records:
        cleaned_r = {}
        for k, v in r.items():
            if pd.isna(v) or v is None or v == "None":
                cleaned_r[k] = None
            else:
                cleaned_r[k] = str(v) if k in ["transaction_id", "status", "anomaly_type", "merchant_id", "initiated_at"] and not isinstance(v, bool) else v
        items.append(TransactionIndexItem(**cleaned_r))

    return TransactionIndexResponse(
        transactions=items,
        page=page,
        page_size=page_size,
        total=total_matching,
        total_normal=total_normal,
        total_anomalies=total_anomalies,
        total_systemic=total_systemic,
    )
