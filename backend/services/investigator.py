"""
Deterministic Investigation Engine - Recon Flow
Takes a transaction_id, fetches records from all three systems via DataLoader,
builds a timeline, runs anomaly detection, computes confidence, and returns a
structured InvestigationResult.

No LLM or AI logic is used. All outputs are derived purely from the CSV data.
"""

from typing import Any, Dict, List, Optional
import pandas as pd

from backend.models.schemas import (
    AnomalyItem,
    ConfidenceInfo,
    DelaysInfo,
    InvestigationResult,
    TimelineEvent,
)
from backend.services.data_loader import (
    find_gateway_records,
    find_bank_transaction,
    find_ledger_transaction,
)
from backend.services.anomaly_detector import detect_anomalies
from backend.services.confidence import calculate_confidence


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_ts(value: Any) -> Optional[pd.Timestamp]:
    """Safely parses a timestamp value into a pandas Timestamp, or returns None."""
    if value is None:
        return None
    try:
        ts = pd.to_datetime(value)
        return ts if not pd.isnull(ts) else None
    except Exception:
        return None


def _fmt(ts: Optional[pd.Timestamp]) -> Optional[str]:
    """Formats a Timestamp to ISO 8601 string or None."""
    if ts is None:
        return None
    return ts.strftime("%Y-%m-%dT%H:%M:%S")


def _build_timeline(
    gateway_records: List[Dict[str, Any]],
    bank_record: Optional[Dict[str, Any]],
    ledger_record: Optional[Dict[str, Any]],
) -> List[TimelineEvent]:
    """
    Constructs a chronologically ordered timeline of events from all available records.
    Events without valid timestamps are placed at the end in data order.
    """
    raw_events: List[tuple] = []  # (timestamp_or_None, TimelineEvent)

    # Gateway events
    for i, gw in enumerate(gateway_records):
        suffix = f" (record {i + 1})" if len(gateway_records) > 1 else ""

        ts_init = _parse_ts(gw.get("initiated_at"))
        raw_events.append((
            ts_init,
            TimelineEvent(
                timestamp=_fmt(ts_init),
                event="PAYMENT_INITIATED",
                source="GATEWAY",
                description=f"Payment initiated via {gw.get('payment_method', 'unknown')} "
                            f"for {gw.get('currency', '')} {gw.get('amount', '')}{suffix}. "
                            f"Reference: {gw.get('gateway_reference', 'N/A')}.",
            ),
        ))

        ts_cap = _parse_ts(gw.get("captured_at"))
        if ts_cap:
            raw_events.append((
                ts_cap,
                TimelineEvent(
                    timestamp=_fmt(ts_cap),
                    event="PAYMENT_CAPTURED",
                    source="GATEWAY",
                    description=f"Payment captured by gateway{suffix}. Status: {gw.get('gateway_status', 'N/A')}.",
                ),
            ))

        ts_si = _parse_ts(gw.get("settlement_initiated_at"))
        if ts_si:
            raw_events.append((
                ts_si,
                TimelineEvent(
                    timestamp=_fmt(ts_si),
                    event="SETTLEMENT_INITIATED",
                    source="GATEWAY",
                    description=f"Settlement instruction dispatched to bank{suffix}.",
                ),
            ))

    # Bank events
    if bank_record:
        ts_recv = _parse_ts(bank_record.get("received_at"))
        if ts_recv:
            raw_events.append((
                ts_recv,
                TimelineEvent(
                    timestamp=_fmt(ts_recv),
                    event="BANK_RECEIVED",
                    source="BANK",
                    description=f"Settlement instruction received by {bank_record.get('bank_name', 'bank')}. "
                                f"Reference: {bank_record.get('bank_reference', 'N/A')}.",
                ),
            ))

        ts_exp = _parse_ts(bank_record.get("expected_settlement_at"))
        if ts_exp:
            raw_events.append((
                ts_exp,
                TimelineEvent(
                    timestamp=_fmt(ts_exp),
                    event="SETTLEMENT_EXPECTED",
                    source="BANK",
                    description=f"Settlement expected by {bank_record.get('bank_name', 'bank')} "
                                f"at this time (SLA deadline).",
                ),
            ))

        ts_set = _parse_ts(bank_record.get("settled_at"))
        if ts_set:
            raw_events.append((
                ts_set,
                TimelineEvent(
                    timestamp=_fmt(ts_set),
                    event="BANK_SETTLED",
                    source="BANK",
                    description=f"Settlement processed by {bank_record.get('bank_name', 'bank')}. "
                                f"Status: {bank_record.get('bank_status', 'N/A')}.",
                ),
            ))

    # Ledger events
    if ledger_record:
        ts_led = _parse_ts(ledger_record.get("created_at"))
        if ts_led:
            raw_events.append((
                ts_led,
                TimelineEvent(
                    timestamp=_fmt(ts_led),
                    event="LEDGER_POSTED",
                    source="LEDGER",
                    description=f"Internal ledger entry {ledger_record.get('ledger_entry_id', 'N/A')} posted. "
                                f"Reconciliation status: {ledger_record.get('reconciliation_status', 'N/A')}.",
                ),
            ))

    # Sort events chronologically; events without timestamps are placed at end
    def sort_key(item: tuple):
        ts = item[0]
        if ts is None:
            return pd.Timestamp.max
        return ts

    raw_events.sort(key=sort_key)
    return [event for _, event in raw_events]


def _build_evidence(
    transaction_id: str,
    gateway_records: List[Dict[str, Any]],
    bank_record: Optional[Dict[str, Any]],
    ledger_record: Optional[Dict[str, Any]],
    anomalies: List[AnomalyItem],
    delays: DelaysInfo,
) -> List[str]:
    """
    Builds a list of factual, deterministic evidence statements.
    """
    ev: List[str] = []

    # Gateway evidence
    if gateway_records:
        primary_gw = gateway_records[0]
        ev.append(
            f"Gateway record found (reference: {primary_gw.get('gateway_reference', 'N/A')}); "
            f"status: {primary_gw.get('gateway_status', 'N/A')}; "
            f"amount: {primary_gw.get('currency', '')} {primary_gw.get('amount', '')}."
        )
        if len(gateway_records) > 1:
            refs = [r.get("gateway_reference", "") for r in gateway_records]
            ev.append(f"Multiple gateway records found ({len(gateway_records)}): {', '.join(refs)}.")
    else:
        ev.append(f"No gateway record found for {transaction_id}.")

    # Bank evidence
    if bank_record:
        ev.append(
            f"Bank record found at {bank_record.get('bank_name', 'N/A')} "
            f"(reference: {bank_record.get('bank_reference', 'N/A')}); "
            f"status: {bank_record.get('bank_status', 'N/A')}; "
            f"amount: {bank_record.get('amount', '')}."
        )
        if delays.bank_delay_minutes is not None and delays.is_delayed:
            ev.append(
                f"Settlement delayed by {delays.bank_delay_minutes:.1f} minutes past SLA "
                f"(expected: {bank_record.get('expected_settlement_at', 'N/A')}, "
                f"actual: {bank_record.get('settled_at', 'N/A')})."
            )
        elif bank_record.get("settled_at"):
            ev.append(
                f"Settlement completed at {bank_record.get('settled_at')} "
                f"(expected: {bank_record.get('expected_settlement_at', 'N/A')})."
            )
    else:
        ev.append(f"No bank settlement record found for {transaction_id}.")

    # Ledger evidence
    if ledger_record:
        ev.append(
            f"Ledger entry {ledger_record.get('ledger_entry_id', 'N/A')} posted; "
            f"status: {ledger_record.get('ledger_status', 'N/A')}; "
            f"reconciliation: {ledger_record.get('reconciliation_status', 'N/A')}."
        )
    else:
        ev.append(f"No internal ledger record found for {transaction_id}.")

    # Anomaly-driven evidence
    for anomaly in anomalies:
        ev.append(f"ANOMALY [{anomaly.anomaly_type}]: {anomaly.description}")

    return ev


def _build_exceptions(anomalies: List[AnomalyItem]) -> List[str]:
    """Returns a plain-text list of exceptions from anomalies."""
    return [
        f"[{anomaly.severity}] {anomaly.anomaly_type}: {anomaly.description}"
        for anomaly in anomalies
    ]


def _calculate_delays(
    gateway_records: List[Dict[str, Any]],
    bank_record: Optional[Dict[str, Any]],
) -> DelaysInfo:
    """Computes all delay metrics deterministically from timestamps."""
    primary_gw = gateway_records[0] if gateway_records else None
    bank_delay_minutes: Optional[float] = None
    gateway_capture_delay_seconds: Optional[float] = None
    settlement_initiation_delay_seconds: Optional[float] = None
    is_delayed = False
    delay_reason: Optional[str] = None

    # Gateway capture delay
    if primary_gw:
        ts_init = _parse_ts(primary_gw.get("initiated_at"))
        ts_cap = _parse_ts(primary_gw.get("captured_at"))
        if ts_init and ts_cap and ts_cap >= ts_init:
            gateway_capture_delay_seconds = (ts_cap - ts_init).total_seconds()

        ts_si = _parse_ts(primary_gw.get("settlement_initiated_at"))
        if ts_cap and ts_si and ts_si >= ts_cap:
            settlement_initiation_delay_seconds = (ts_si - ts_cap).total_seconds()

    # Bank settlement delay vs expected SLA
    # is_delayed is True only when settled_at exceeds expected_settlement_at by more than 15 minutes.
    if bank_record:
        ts_exp = _parse_ts(bank_record.get("expected_settlement_at"))
        ts_set = _parse_ts(bank_record.get("settled_at"))
        if ts_exp and ts_set:
            diff_sec = (ts_set - ts_exp).total_seconds()
            bank_delay_minutes = round(diff_sec / 60.0, 1)
            if diff_sec > 900:  # 900 seconds = 15 minutes
                is_delayed = True
                delay_reason = (
                    f"Settlement was {bank_delay_minutes:.1f} minutes late "
                    f"(expected: {bank_record.get('expected_settlement_at')}, "
                    f"actual: {bank_record.get('settled_at')})."
                )

    return DelaysInfo(
        bank_delay_minutes=bank_delay_minutes,
        gateway_capture_delay_seconds=gateway_capture_delay_seconds,
        settlement_initiation_delay_seconds=settlement_initiation_delay_seconds,
        is_delayed=is_delayed,
        delay_reason=delay_reason,
    )


def _determine_status(
    gateway_records: List[Dict[str, Any]],
    bank_record: Optional[Dict[str, Any]],
    ledger_record: Optional[Dict[str, Any]],
    anomalies: List[AnomalyItem],
) -> str:
    """
    Derives the overall investigation status from anomaly types.
    Priority order: UNKNOWN > MISSING_DATA > DUPLICATE > INCONSISTENT > MISMATCH > DELAYED > SUCCESS
    """
    anomaly_types = {a.anomaly_type for a in anomalies}

    # No records at all
    if not gateway_records and bank_record is None and ledger_record is None:
        return "UNKNOWN"

    if "TRANSACTION_NOT_FOUND" in anomaly_types:
        return "UNKNOWN"

    if "STATUS_CONFLICT" in anomaly_types or "TIMESTAMP_INCONSISTENCY" in anomaly_types:
        return "INCONSISTENT"

    if "DUPLICATE_GATEWAY_RECORD" in anomaly_types:
        return "DUPLICATE"

    if "MISSING_BANK_RECORD" in anomaly_types or "MISSING_LEDGER_RECORD" in anomaly_types:
        return "MISSING_DATA"

    if "AMOUNT_MISMATCH" in anomaly_types:
        return "MISMATCH"

    if "BANK_DELAY" in anomaly_types:
        return "DELAYED"

    return "SUCCESS"


def _build_summary(
    transaction_id: str,
    status: str,
    gateway_records: List[Dict[str, Any]],
    bank_record: Optional[Dict[str, Any]],
    ledger_record: Optional[Dict[str, Any]],
    anomalies: List[AnomalyItem],
    delays: DelaysInfo,
) -> str:
    """
    Generates a deterministic, factual one-sentence summary of the investigation.
    """
    gw_present = len(gateway_records) > 0
    bnk_present = bank_record is not None
    led_present = ledger_record is not None

    presence_parts = []
    if gw_present:
        presence_parts.append("Gateway ✓")
    else:
        presence_parts.append("Gateway ✗")
    if bnk_present:
        presence_parts.append("Bank ✓")
    else:
        presence_parts.append("Bank ✗")
    if led_present:
        presence_parts.append("Ledger ✓")
    else:
        presence_parts.append("Ledger ✗")

    presence_str = " | ".join(presence_parts)

    if status == "UNKNOWN":
        return f"Transaction {transaction_id} was not found in any system. ({presence_str})"

    if status == "SUCCESS":
        return (
            f"Transaction {transaction_id} settled successfully across all three systems. "
            f"({presence_str})"
        )

    if status == "DELAYED":
        delay_min = delays.bank_delay_minutes
        return (
            f"Transaction {transaction_id} settled with a delay of "
            f"{delay_min:.1f} minutes past the expected SLA. ({presence_str})"
        )

    if status == "MISMATCH":
        anomaly = next((a for a in anomalies if a.anomaly_type == "AMOUNT_MISMATCH"), None)
        detail = anomaly.description if anomaly else "Amount mismatch detected."
        return f"Transaction {transaction_id}: {detail} ({presence_str})"

    if status == "MISSING_DATA":
        missing = []
        if not bnk_present:
            missing.append("Bank")
        if not led_present:
            missing.append("Ledger")
        return (
            f"Transaction {transaction_id}: Missing records in {', '.join(missing)}. "
            f"({presence_str})"
        )

    if status == "DUPLICATE":
        return (
            f"Transaction {transaction_id}: {len(gateway_records)} duplicate Gateway records detected. "
            f"({presence_str})"
        )

    if status == "INCONSISTENT":
        types = [a.anomaly_type for a in anomalies]
        return (
            f"Transaction {transaction_id}: Data inconsistency detected "
            f"({', '.join(types)}). ({presence_str})"
        )

    return f"Transaction {transaction_id} investigation status: {status}. ({presence_str})"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def investigate(transaction_id: str) -> InvestigationResult:
    """
    Entry point for the deterministic investigation engine.

    Args:
        transaction_id: The transaction ID string to investigate.

    Returns:
        InvestigationResult with all evidence, timeline, anomalies, and confidence.
    """
    tid = str(transaction_id).strip()

    # Fetch all records via DataLoader
    gateway_records = find_gateway_records(tid)
    bank_record = find_bank_transaction(tid)
    ledger_record = find_ledger_transaction(tid)

    primary_gateway = gateway_records[0] if gateway_records else None

    # Detect anomalies deterministically
    anomalies = detect_anomalies(
        transaction_id=tid,
        gateway_records=gateway_records,
        bank_record=bank_record,
        ledger_record=ledger_record,
    )

    # Calculate delays
    delays = _calculate_delays(gateway_records, bank_record)

    # Build timeline
    timeline = _build_timeline(gateway_records, bank_record, ledger_record)

    # Build evidence list and exceptions
    evidence = _build_evidence(tid, gateway_records, bank_record, ledger_record, anomalies, delays)
    exceptions = _build_exceptions(anomalies)

    # Calculate confidence
    confidence = calculate_confidence(
        gateway_records=gateway_records,
        bank_record=bank_record,
        ledger_record=ledger_record,
        anomalies=anomalies,
    )

    # Determine overall status
    status = _determine_status(gateway_records, bank_record, ledger_record, anomalies)

    # Build summary
    summary = _build_summary(
        transaction_id=tid,
        status=status,
        gateway_records=gateway_records,
        bank_record=bank_record,
        ledger_record=ledger_record,
        anomalies=anomalies,
        delays=delays,
    )

    return InvestigationResult(
        transaction_id=tid,
        status=status,
        summary=summary,
        gateway=primary_gateway,
        gateway_records=gateway_records,
        bank=bank_record,
        ledger=ledger_record,
        timeline=timeline,
        anomalies=anomalies,
        evidence=evidence,
        exceptions=exceptions,
        delays=delays,
        confidence=confidence,
    )
