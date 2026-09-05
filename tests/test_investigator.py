"""
Phase 3 - Deterministic Investigation Engine Tests
Tests the investigate() function against all demo scenarios defined in demo_cases.json.
No mocking; uses the real CSV datasets.
"""

import pytest
from backend.services.data_loader import clear_cache
from backend.services.investigator import investigate
from backend.models.schemas import InvestigationResult


@pytest.fixture(autouse=True)
def reset_cache():
    """Ensure DataLoader cache is cleared between tests for isolation."""
    clear_cache()
    yield
    clear_cache()


# ---------------------------------------------------------------------------
# Helper predicates
# ---------------------------------------------------------------------------

def _has_anomaly(result: InvestigationResult, anomaly_type: str) -> bool:
    return any(a.anomaly_type == anomaly_type for a in result.anomalies)


def _timeline_types(result: InvestigationResult):
    return [e.event for e in result.timeline]


# ---------------------------------------------------------------------------
# Non-existent transaction
# ---------------------------------------------------------------------------

def test_nonexistent_transaction():
    """An unknown transaction ID must return status UNKNOWN with zero confidence."""
    result = investigate("TXN_DOES_NOT_EXIST")
    assert isinstance(result, InvestigationResult)
    assert result.transaction_id == "TXN_DOES_NOT_EXIST"
    assert result.status == "UNKNOWN"
    assert result.confidence.score == 0
    assert result.confidence.level == "LOW"
    assert result.gateway is None
    assert result.bank is None
    assert result.ledger is None
    assert result.timeline == []
    assert _has_anomaly(result, "TRANSACTION_NOT_FOUND")


# ---------------------------------------------------------------------------
# Normal transaction: TXN10001
# ---------------------------------------------------------------------------

def test_normal_transaction():
    """Normal transaction must settle SUCCESS with high confidence and no anomalies."""
    result = investigate("TXN10001")
    assert result.transaction_id == "TXN10001"
    assert result.status == "SUCCESS"
    assert result.confidence.score >= 75
    assert result.confidence.level in ("HIGH", "VERY_HIGH")
    assert result.anomalies == []
    # All three records should be present
    assert result.gateway is not None
    assert result.bank is not None
    assert result.ledger is not None
    # Timeline must have events from all three systems
    sources = {e.source for e in result.timeline}
    assert "GATEWAY" in sources
    assert "BANK" in sources
    assert "LEDGER" in sources
    # Timeline must be chronologically ordered
    timestamps = [e.timestamp for e in result.timeline if e.timestamp]
    assert timestamps == sorted(timestamps)
    # Evidence must be non-empty
    assert len(result.evidence) > 0


# ---------------------------------------------------------------------------
# Bank delay: TXN10087
# ---------------------------------------------------------------------------

def test_bank_delay():
    """
    TXN10087: Gateway and Ledger present, Bank delayed past expected SLA.
    Expected status: DELAYED. Bank delay anomaly must be present.
    """
    result = investigate("TXN10087")
    assert result.transaction_id == "TXN10087"
    assert result.status == "DELAYED"
    assert _has_anomaly(result, "BANK_DELAY")
    assert result.delays.is_delayed is True
    assert result.delays.bank_delay_minutes is not None
    assert result.delays.bank_delay_minutes > 0
    # All records present
    assert result.gateway is not None
    assert result.bank is not None
    assert result.ledger is not None
    # Confidence should be reduced but not catastrophically
    assert result.confidence.score >= 40


# ---------------------------------------------------------------------------
# Amount mismatch: TXN10142
# ---------------------------------------------------------------------------

def test_amount_mismatch():
    """
    TXN10142: Gateway=5000, Bank=4800, Ledger=5000.
    Expected status: MISMATCH. AMOUNT_MISMATCH anomaly must be present.
    """
    result = investigate("TXN10142")
    assert result.transaction_id == "TXN10142"
    assert result.status == "MISMATCH"
    assert _has_anomaly(result, "AMOUNT_MISMATCH")
    # Verify the raw amounts are what we expect
    assert result.gateway is not None
    assert float(result.gateway["amount"]) == 5000.0
    assert result.bank is not None
    assert float(result.bank["amount"]) == 4800.0
    assert result.ledger is not None
    assert float(result.ledger["amount"]) == 5000.0
    # Confidence should be reduced by the mismatch penalty
    assert result.confidence.score < 90


# ---------------------------------------------------------------------------
# Missing bank: TXN10211
# ---------------------------------------------------------------------------

def test_missing_bank():
    """
    TXN10211: Gateway=present, Bank=MISSING, Ledger=present.
    Expected status: MISSING_DATA. MISSING_BANK_RECORD anomaly must be detected.
    """
    result = investigate("TXN10211")
    assert result.transaction_id == "TXN10211"
    assert result.status == "MISSING_DATA"
    assert _has_anomaly(result, "MISSING_BANK_RECORD")
    assert result.gateway is not None
    assert result.bank is None
    assert result.ledger is not None
    # No ledger anomaly should be present for this case
    assert not _has_anomaly(result, "MISSING_LEDGER_RECORD")
    # Confidence is reduced due to missing bank
    assert result.confidence.score < 90


# ---------------------------------------------------------------------------
# Missing ledger: TXN10304
# ---------------------------------------------------------------------------

def test_missing_ledger():
    """
    TXN10304: Gateway=present, Bank=present, Ledger=MISSING.
    Expected status: MISSING_DATA. MISSING_LEDGER_RECORD anomaly must be detected.
    """
    result = investigate("TXN10304")
    assert result.transaction_id == "TXN10304"
    assert result.status == "MISSING_DATA"
    assert _has_anomaly(result, "MISSING_LEDGER_RECORD")
    assert result.gateway is not None
    assert result.bank is not None
    assert result.ledger is None
    # No bank anomaly should be present for this case
    assert not _has_anomaly(result, "MISSING_BANK_RECORD")


# ---------------------------------------------------------------------------
# Duplicate gateway: TXN10482
# ---------------------------------------------------------------------------

def test_duplicate_gateway():
    """
    TXN10482: Two Gateway records for same transaction ID.
    Expected status: DUPLICATE. DUPLICATE_GATEWAY_RECORD anomaly must be present.
    """
    result = investigate("TXN10482")
    assert result.transaction_id == "TXN10482"
    assert result.status == "DUPLICATE"
    assert _has_anomaly(result, "DUPLICATE_GATEWAY_RECORD")
    assert len(result.gateway_records) == 2
    # Confirm the two records have different gateway references
    refs = [r["gateway_reference"] for r in result.gateway_records]
    assert len(set(refs)) == 2, "Duplicate gateway records should have different references"


# ---------------------------------------------------------------------------
# Timestamp inconsistency: TXN10531
# ---------------------------------------------------------------------------

def test_timestamp_inconsistency():
    """
    TXN10531: Bank settled_at earlier than Gateway initiated_at.
    Expected status: INCONSISTENT. TIMESTAMP_INCONSISTENCY anomaly must be present.
    """
    result = investigate("TXN10531")
    assert result.transaction_id == "TXN10531"
    assert result.status == "INCONSISTENT"
    assert _has_anomaly(result, "TIMESTAMP_INCONSISTENCY")
    assert result.gateway is not None
    assert result.bank is not None


# ---------------------------------------------------------------------------
# Systemic incident: TXN10087 (also the bank_delay case)
# ---------------------------------------------------------------------------

def test_systemic_incident_is_bank_delay():
    """
    demo_cases.json maps systemic_incident to TXN10087, same as bank_delay.
    Confirm the same result is returned and has a BANK_DELAY anomaly.
    """
    result = investigate("TXN10087")
    assert result.status == "DELAYED"
    assert _has_anomaly(result, "BANK_DELAY")


# ---------------------------------------------------------------------------
# Structural / contract tests
# ---------------------------------------------------------------------------

def test_result_fields_always_populated():
    """InvestigationResult must always include all required fields."""
    for tid in ["TXN10001", "TXN10087", "TXN10142", "TXN10211", "TXN_DOES_NOT_EXIST"]:
        result = investigate(tid)
        assert isinstance(result.transaction_id, str)
        assert isinstance(result.status, str)
        assert isinstance(result.summary, str) and len(result.summary) > 0
        assert isinstance(result.timeline, list)
        assert isinstance(result.anomalies, list)
        assert isinstance(result.evidence, list)
        assert isinstance(result.exceptions, list)
        assert isinstance(result.confidence.score, int)
        assert 0 <= result.confidence.score <= 100
        assert result.confidence.level in ("VERY_HIGH", "HIGH", "MEDIUM", "LOW")


def test_status_values_are_valid():
    """All returned statuses must be from the agreed set."""
    valid_statuses = {
        "SUCCESS", "DELAYED", "MISMATCH", "MISSING_DATA",
        "DUPLICATE", "INCONSISTENT", "FAILED", "UNKNOWN"
    }
    demo_ids = ["TXN10001", "TXN10087", "TXN10142", "TXN10211",
                "TXN10304", "TXN10482", "TXN10531", "TXN_DOES_NOT_EXIST"]
    for tid in demo_ids:
        result = investigate(tid)
        assert result.status in valid_statuses, (
            f"{tid} returned unexpected status: {result.status}"
        )


def test_timeline_chronological_order():
    """All investigation timelines must be in non-decreasing chronological order."""
    demo_ids = ["TXN10001", "TXN10087", "TXN10142", "TXN10304", "TXN10482", "TXN10531"]
    for tid in demo_ids:
        result = investigate(tid)
        timestamps = [e.timestamp for e in result.timeline if e.timestamp]
        assert timestamps == sorted(timestamps), (
            f"Timeline for {tid} is not chronologically ordered: {timestamps}"
        )


def test_confidence_lower_for_anomalous_transactions():
    """Anomalous transactions must have lower confidence than the clean normal case."""
    normal = investigate("TXN10001")
    delayed = investigate("TXN10087")
    mismatch = investigate("TXN10142")
    missing_bank = investigate("TXN10211")
    missing_ledger = investigate("TXN10304")
    duplicate = investigate("TXN10482")
    ts_error = investigate("TXN10531")

    assert normal.confidence.score > delayed.confidence.score
    assert normal.confidence.score > mismatch.confidence.score
    assert normal.confidence.score > missing_bank.confidence.score
    assert normal.confidence.score > missing_ledger.confidence.score
    assert normal.confidence.score > duplicate.confidence.score
    assert normal.confidence.score > ts_error.confidence.score


def test_evidence_references_anomalies():
    """Evidence list must mention ANOMALY entries when anomalies are detected."""
    result = investigate("TXN10142")
    evidence_text = "\n".join(result.evidence)
    assert "ANOMALY" in evidence_text or "AMOUNT_MISMATCH" in evidence_text


def test_row_counts_unchanged():
    """Data row counts must remain unchanged after running investigations."""
    from backend.services.data_loader import load_gateway, load_bank, load_ledger
    for tid in ["TXN10001", "TXN10087", "TXN10142", "TXN10211"]:
        investigate(tid)
    assert len(load_gateway()) >= 12155
    assert len(load_bank()) >= 12000
    assert len(load_ledger()) >= 12000



# ---------------------------------------------------------------------------
# Phase 3 Refinement Tests — Threshold semantics and systemic-detection guard
# ---------------------------------------------------------------------------

def _make_bank_record(delay_seconds: int) -> dict:
    """
    Construct a minimal in-memory bank record with a configurable delay
    between expected_settlement_at and settled_at.
    Uses fixed base timestamps to avoid any dependency on external state.
    """
    import pandas as pd
    base = pd.Timestamp("2026-01-01T12:00:00")
    expected = base
    settled = base + pd.Timedelta(seconds=delay_seconds)
    return {
        "transaction_id": "TXN_TEST",
        "bank_reference": "BNK_TST_TXN_TEST",
        "bank_name": "TEST_BANK",
        "amount": 1000.0,
        "bank_status": "SETTLED",
        "received_at": base.isoformat(),
        "expected_settlement_at": expected.isoformat(),
        "settled_at": settled.isoformat(),
        "response_code": "00",
        "response_message": "OK",
    }


def test_exactly_15_minutes_is_not_delayed():
    """
    Exactly 15 minutes (900 s) late must NOT be flagged as BANK_DELAY.
    The threshold is strictly greater than 15 minutes.
    Tests the anomaly detector directly with a constructed in-memory record.
    """
    from backend.services.anomaly_detector import detect_anomalies
    bank_rec = _make_bank_record(delay_seconds=900)  # exactly 15 minutes
    anomalies = detect_anomalies(
        transaction_id="TXN_TEST",
        gateway_records=[{"transaction_id": "TXN_TEST", "gateway_reference": "GW_TEST",
                          "gateway_status": "CAPTURED", "amount": 1000.0,
                          "currency": "INR", "payment_method": "UPI",
                          "initiated_at": "2026-01-01T11:55:00",
                          "captured_at": "2026-01-01T11:56:00",
                          "settlement_initiated_at": "2026-01-01T11:57:00",
                          "response_code": "00", "response_message": "OK",
                          "merchant_id": "MERCH_001"}],
        bank_record=bank_rec,
        ledger_record=None,
    )
    bank_delay_anomalies = [a for a in anomalies if a.anomaly_type == "BANK_DELAY"]
    assert bank_delay_anomalies == [], (
        f"Exactly 15 minutes must NOT be flagged as BANK_DELAY, but got: {bank_delay_anomalies}"
    )


def test_more_than_15_minutes_is_delayed():
    """
    16 minutes (960 s) late MUST be flagged as BANK_DELAY with MEDIUM severity.
    The threshold is strictly greater than 15 minutes.
    """
    from backend.services.anomaly_detector import detect_anomalies
    bank_rec = _make_bank_record(delay_seconds=960)  # 16 minutes
    anomalies = detect_anomalies(
        transaction_id="TXN_TEST",
        gateway_records=[{"transaction_id": "TXN_TEST", "gateway_reference": "GW_TEST",
                          "gateway_status": "CAPTURED", "amount": 1000.0,
                          "currency": "INR", "payment_method": "UPI",
                          "initiated_at": "2026-01-01T11:55:00",
                          "captured_at": "2026-01-01T11:56:00",
                          "settlement_initiated_at": "2026-01-01T11:57:00",
                          "response_code": "00", "response_message": "OK",
                          "merchant_id": "MERCH_001"}],
        bank_record=bank_rec,
        ledger_record=None,
    )
    bank_delay_anomalies = [a for a in anomalies if a.anomaly_type == "BANK_DELAY"]
    assert len(bank_delay_anomalies) == 1, (
        f"16-minute delay must be flagged as BANK_DELAY; anomalies: {anomalies}"
    )
    assert bank_delay_anomalies[0].severity == "MEDIUM", (
        f"16-minute delay must be MEDIUM severity, got: {bank_delay_anomalies[0].severity}"
    )
    assert bank_delay_anomalies[0].details["delay_minutes"] == 16.0


def test_txn10087_delay_is_high_severity():
    """
    TXN10087 is delayed by ~92 minutes, which exceeds 60 minutes.
    Its BANK_DELAY anomaly must be flagged with HIGH severity.
    """
    result = investigate("TXN10087")
    bank_delay_anomalies = [a for a in result.anomalies if a.anomaly_type == "BANK_DELAY"]
    assert len(bank_delay_anomalies) == 1, (
        f"TXN10087 must have exactly one BANK_DELAY anomaly; got: {result.anomalies}"
    )
    assert bank_delay_anomalies[0].severity == "HIGH", (
        f"TXN10087 delay is >60 min — expected HIGH severity, got: {bank_delay_anomalies[0].severity}"
    )
    # Verify the actual delay is approximately 92 minutes
    delay_min = bank_delay_anomalies[0].details["delay_minutes"]
    assert delay_min > 60, f"TXN10087 delay must be >60 min, got: {delay_min}"


def test_txn10087_has_no_systemic_incident_anomaly():
    """
    Phase 3 must NOT add a SYSTEMIC_INCIDENT anomaly to any transaction.
    TXN10087 appears in demo_cases.json as a systemic_incident example,
    but Phase 3 is transaction-level only — systemic discovery belongs to Phase 5.
    """
    result = investigate("TXN10087")
    systemic_anomalies = [
        a for a in result.anomalies if "SYSTEMIC" in a.anomaly_type.upper()
    ]
    assert systemic_anomalies == [], (
        f"Phase 3 must not produce systemic anomalies; got: {systemic_anomalies}"
    )


def test_investigator_does_not_use_demo_cases_for_status():
    """
    The investigator must derive status purely from CSV evidence.
    Passing a transaction ID that exists in demo_cases.json as 'systemic_incident'
    (TXN10087) must produce DELAYED — not UNKNOWN or any systemic status —
    confirming status comes from data, not from demo_cases.json lookup.
    """
    # TXN10087 is the 'systemic_incident' demo case, yet Phase 3 must produce DELAYED
    result = investigate("TXN10087")
    assert result.status == "DELAYED", (
        f"TXN10087 status must be DELAYED (from CSV evidence), got: {result.status}"
    )
    # Ensure demo_cases.json was NOT consulted to construct anomaly list
    anomaly_types = {a.anomaly_type for a in result.anomalies}
    assert "SYSTEMIC_INCIDENT" not in anomaly_types
    assert "TRANSACTION_NOT_FOUND" not in anomaly_types


def test_below_threshold_not_delayed_via_investigate():
    """
    End-to-end guard: if bank delay is <=15 minutes the investigator
    must NOT set is_delayed=True or status=DELAYED.
    Uses a constructed in-memory record via the delay-calculation helper.
    """
    from backend.services.investigator import _calculate_delays
    bank_rec = _make_bank_record(delay_seconds=900)  # exactly 15 min — not delayed
    delays = _calculate_delays(gateway_records=[], bank_record=bank_rec)
    assert delays.is_delayed is False, (
        f"Exactly 15 min must not be is_delayed=True; got: {delays}"
    )

    bank_rec_just_over = _make_bank_record(delay_seconds=901)  # 15m 1s — delayed
    delays_over = _calculate_delays(gateway_records=[], bank_record=bank_rec_just_over)
    assert delays_over.is_delayed is True, (
        f"901 seconds must be is_delayed=True; got: {delays_over}"
    )

