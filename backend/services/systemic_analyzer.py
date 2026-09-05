"""
Phase 5 - Systemic Analyzer Service
Discovers systemic settlement incidents across the complete dataset deterministically.
No machine learning, no hardcoded transaction IDs, no reliance on demo_cases.json.
Deduplicates transactions prior to clustering to ensure metrics are not inflated by duplicates.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from backend.models.schemas import SystemicIncident, IncidentAssociation
from backend.services.data_loader import load_all_data


# Deterministic mapping of gateway_reference prefix to canonical gateway provider name
GATEWAY_PREFIX_MAP: Dict[str, str] = {
    "GW_RAZ": "RAZORPAY",
    "GW_PAY": "PAYU",
    "GW_CAS": "CASHFREE",
    "GW_STR": "STRIPE",
}

# Incident qualification thresholds
MIN_INCIDENT_TRANSACTION_COUNT = 10
MAX_INTRA_CLUSTER_GAP_SECONDS = 1800  # 30 minutes inactivity gap
MAX_CLUSTER_SPAN_SECONDS = 14400      # 4 hours max duration
SLA_DELAY_THRESHOLD_SECONDS = 900     # 15 minutes


def derive_gateway_provider(gateway_reference: Optional[str]) -> str:
    """
    Deterministically extracts the gateway provider from gateway_reference prefix.
    e.g. 'GW_RAZ_TXN10001' -> 'RAZORPAY'
    """
    if not gateway_reference or not isinstance(gateway_reference, str):
        return "UNKNOWN"
    prefix = gateway_reference[:6]
    return GATEWAY_PREFIX_MAP.get(prefix, "UNKNOWN")


def _calculate_severity(count: int, amount: float) -> str:
    if count >= 100 or amount >= 1_000_000.0:
        return "CRITICAL"
    if count >= 50 or amount >= 500_000.0:
        return "HIGH"
    return "MEDIUM"


def _calculate_incident_confidence(count: int, dominant_error: str) -> int:
    score = 70
    if count >= 50:
        score += 15
    elif count >= 20:
        score += 10

    if dominant_error in ("BANK_TIMEOUT", "SYSTEM_ERROR", "SERVICE_UNAVAILABLE"):
        score += 10
    else:
        score += 5

    score += 5  # Confirmed homogeneous bank and gateway
    return min(100, max(0, score))


class SystemicAnalyzer:
    """
    Analyzes all gateway and bank settlement records to detect systemic incident clusters.
    """

    def __init__(self):
        self._cached_incidents: Optional[List[SystemicIncident]] = None
        self._incident_lookup: Dict[str, SystemicIncident] = {}

    def clear_cache(self) -> None:
        self._cached_incidents = None
        self._incident_lookup = {}

    def detect_incidents(
        self,
        gw_df: Optional[pd.DataFrame] = None,
        bnk_df: Optional[pd.DataFrame] = None,
        force_reload: bool = False,
    ) -> List[SystemicIncident]:
        """
        Discovers systemic incidents from the datasets.
        If DataFrames are not supplied, loads them through DataLoader.
        """
        if self._cached_incidents is not None and not force_reload and gw_df is None and bnk_df is None:
            return self._cached_incidents

        if gw_df is None or bnk_df is None:
            raw_gw, raw_bnk, _ = load_all_data()
            gw_df = raw_gw if gw_df is None else gw_df
            bnk_df = raw_bnk if bnk_df is None else bnk_df

        if gw_df.empty or bnk_df.empty:
            self._cached_incidents = []
            self._incident_lookup = {}
            return []

        # -------------------------------------------------------------------
        # 1. Deduplicate by transaction_id prior to merging
        # -------------------------------------------------------------------
        # Keep the first/primary gateway and bank row so duplicate capture rows (like TXN10482)
        # never inflate incident count, amount, or create Cartesian product rows.
        gw_clean = gw_df.drop_duplicates(subset=["transaction_id"], keep="first").copy()
        bnk_clean = bnk_df.drop_duplicates(subset=["transaction_id"], keep="first").copy()

        # Derive gateway provider column
        gw_clean["gateway_provider"] = gw_clean["gateway_reference"].apply(derive_gateway_provider)

        # Merge on transaction_id (inner join: transactions with both gateway and bank context)
        merged = pd.merge(
            gw_clean,
            bnk_clean,
            on="transaction_id",
            suffixes=("_gw", "_bnk"),
            how="inner",
        )

        if merged.empty:
            self._cached_incidents = []
            self._incident_lookup = {}
            return []

        # Use bank amount where available, fallback to gateway amount
        merged["amount"] = pd.to_numeric(merged["amount_bnk"].fillna(merged["amount_gw"]), errors="coerce").fillna(0.0)

        # -------------------------------------------------------------------
        # 2. Compute settlement delays and identify anomalies
        # -------------------------------------------------------------------
        merged["dt_init"] = pd.to_datetime(merged["initiated_at"], errors="coerce")
        merged["dt_exp"] = pd.to_datetime(merged["expected_settlement_at"], errors="coerce")
        merged["dt_set"] = pd.to_datetime(merged["settled_at"], errors="coerce")

        # Delay in seconds past SLA
        merged["delay_sec"] = (merged["dt_set"] - merged["dt_exp"]).dt.total_seconds().fillna(0.0)
        merged["delay_min"] = merged["delay_sec"] / 60.0

        # Anomalous criteria:
        # - Delay exceeds 15 minutes SLA (> 900s)
        # - Bank status indicates failure
        # - Gateway status indicates failure
        # - Response code indicates timeout / server error
        is_delayed = merged["delay_sec"] > SLA_DELAY_THRESHOLD_SECONDS
        is_bank_failed = merged["bank_status"].str.upper() == "FAILED"
        is_gw_failed = merged["gateway_status"].str.upper() == "FAILED"
        is_timeout = (merged["response_code_bnk"].str.upper() == "BANK_TIMEOUT") | (
            merged["response_code_gw"].str.upper() == "BANK_TIMEOUT"
        )

        anomalies = merged[is_delayed | is_bank_failed | is_gw_failed | is_timeout].copy()

        if anomalies.empty:
            self._cached_incidents = []
            self._incident_lookup = {}
            return []

        # -------------------------------------------------------------------
        # 3. Partition by (bank_name, gateway_provider, response_code)
        # -------------------------------------------------------------------
        # Normalize fields for grouping
        anomalies["group_bank"] = anomalies["bank_name"].fillna("UNKNOWN_BANK")
        anomalies["group_gateway"] = anomalies["gateway_provider"].fillna("UNKNOWN_GATEWAY")
        anomalies["group_error"] = anomalies["response_code_bnk"].fillna(anomalies["response_code_gw"]).fillna("UNKNOWN_ERROR")

        incidents: List[SystemicIncident] = []
        incident_lookup: Dict[str, SystemicIncident] = {}
        incident_counter = 1

        grouped = anomalies.groupby(["group_bank", "group_gateway", "group_error"])

        for (bank_name, gateway_name, error_code), group in grouped:
            # Sort group chronologically by initiation timestamp
            sorted_group = group.sort_values("dt_init").copy()

            # ---------------------------------------------------------------
            # 4. Temporal Rolling Max-Gap Clustering
            # ---------------------------------------------------------------
            clusters: List[List[pd.Series]] = []
            current_cluster: List[pd.Series] = []
            cluster_start_dt: Optional[pd.Timestamp] = None
            last_seen_dt: Optional[pd.Timestamp] = None

            for _, row in sorted_group.iterrows():
                row_dt = row["dt_init"]
                if pd.isna(row_dt):
                    continue

                if not current_cluster:
                    current_cluster = [row]
                    cluster_start_dt = row_dt
                    last_seen_dt = row_dt
                else:
                    gap_sec = (row_dt - last_seen_dt).total_seconds()
                    span_sec = (row_dt - cluster_start_dt).total_seconds()

                    if gap_sec <= MAX_INTRA_CLUSTER_GAP_SECONDS and span_sec <= MAX_CLUSTER_SPAN_SECONDS:
                        current_cluster.append(row)
                        last_seen_dt = row_dt
                    else:
                        clusters.append(current_cluster)
                        current_cluster = [row]
                        cluster_start_dt = row_dt
                        last_seen_dt = row_dt

            if current_cluster:
                clusters.append(current_cluster)

            # ---------------------------------------------------------------
            # 5. Evaluate and Qualify Incidents
            # ---------------------------------------------------------------
            for cluster_rows in clusters:
                # Deduplicate transaction IDs within the cluster strictly
                unique_txns: Dict[str, pd.Series] = {}
                for r in cluster_rows:
                    tid = str(r["transaction_id"]).strip()
                    if tid not in unique_txns:
                        unique_txns[tid] = r

                txn_count = len(unique_txns)
                if txn_count < MIN_INCIDENT_TRANSACTION_COUNT:
                    continue

                records = list(unique_txns.values())
                affected_ids = list(unique_txns.keys())
                total_amount = round(sum(float(r["amount"]) for r in records), 2)

                # Min/max timestamps
                init_times = [r["dt_init"] for r in records if pd.notna(r["dt_init"])]
                settle_times = [r["dt_set"] for r in records if pd.notna(r["dt_set"])]

                start_time_dt = min(init_times) if init_times else datetime.now()
                # End time covers the latest settlement or initiation
                end_time_dt = max(settle_times + init_times) if (settle_times or init_times) else start_time_dt

                start_time_iso = start_time_dt.strftime("%Y-%m-%dT%H:%M:%S")
                end_time_iso = end_time_dt.strftime("%Y-%m-%dT%H:%M:%S")

                delays = [float(r["delay_min"]) for r in records if pd.notna(r["delay_min"]) and r["delay_min"] > 0]
                min_delay = round(min(delays), 1) if delays else 0.0
                max_delay = round(max(delays), 1) if delays else 0.0

                severity = _calculate_severity(txn_count, total_amount)
                confidence_score = _calculate_incident_confidence(txn_count, error_code)

                bank_prefix = bank_name[:3].upper()
                date_str = start_time_dt.strftime("%Y%m%d")
                inc_id = f"INC-{bank_prefix}-{date_str}-{incident_counter:02d}"
                incident_counter += 1

                reasons = [
                    f"{txn_count} transactions affected at {bank_name} via {gateway_name} between {start_time_iso[11:19]} and {end_time_iso[11:19]}",
                    f"100% of transactions in this cluster share response code '{error_code}'",
                    f"Total settlement volume at risk: ₹{total_amount:,.2f}",
                ]
                if delays:
                    reasons.append(f"Settlement delays ranged from {min_delay:.1f} to {max_delay:.1f} minutes past SLA")

                incident = SystemicIncident(
                    incident_id=inc_id,
                    title=f"{bank_name} {gateway_name} Settlement Incident ({error_code})",
                    severity=severity,
                    status="ACTIVE",
                    bank=bank_name,
                    gateway=gateway_name,
                    dominant_error=error_code,
                    start_time=start_time_iso,
                    end_time=end_time_iso,
                    affected_transaction_count=txn_count,
                    affected_amount=total_amount,
                    common_delay_range_minutes=[min_delay, max_delay],
                    detection_reasons=reasons,
                    affected_transactions=affected_ids,
                    confidence=confidence_score,
                )

                incidents.append(incident)
                for tid in affected_ids:
                    incident_lookup[tid] = incident

        self._cached_incidents = incidents
        self._incident_lookup = incident_lookup
        return incidents

    def get_active_incidents(self, reload: bool = False) -> List[SystemicIncident]:
        """Returns all currently detected active systemic incidents."""
        return self.detect_incidents(force_reload=reload)

    def check_transaction_incident(
        self, transaction_id: str, reload: bool = False
    ) -> Optional[SystemicIncident]:
        """
        Determines if a transaction ID is associated with any detected systemic incident.
        Returns the SystemicIncident if associated, else None.
        """
        tid = str(transaction_id).strip()
        if self._cached_incidents is None or reload:
            self.detect_incidents(force_reload=reload)

        return self._incident_lookup.get(tid)

    def check_transaction_association(
        self, transaction_id: str, reload: bool = False
    ) -> IncidentAssociation:
        """
        Returns structured IncidentAssociation model for a transaction.
        """
        inc = self.check_transaction_incident(transaction_id, reload=reload)
        if inc is not None:
            return IncidentAssociation(is_systemic=True, incident=inc)
        return IncidentAssociation(is_systemic=False, incident=None)


# Global singleton instance
_default_analyzer = SystemicAnalyzer()


def detect_incidents(
    gw_df: Optional[pd.DataFrame] = None,
    bnk_df: Optional[pd.DataFrame] = None,
    reload: bool = False,
) -> List[SystemicIncident]:
    return _default_analyzer.detect_incidents(gw_df=gw_df, bnk_df=bnk_df, force_reload=reload)


def get_active_incidents(reload: bool = False) -> List[SystemicIncident]:
    return _default_analyzer.get_active_incidents(reload=reload)


def check_transaction_incident(transaction_id: str, reload: bool = False) -> Optional[SystemicIncident]:
    return _default_analyzer.check_transaction_incident(transaction_id, reload=reload)


def check_transaction_association(transaction_id: str, reload: bool = False) -> IncidentAssociation:
    return _default_analyzer.check_transaction_association(transaction_id, reload=reload)


def clear_incident_cache() -> None:
    _default_analyzer.clear_cache()
