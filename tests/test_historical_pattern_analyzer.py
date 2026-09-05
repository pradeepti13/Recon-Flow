"""
Tests for Phase 8 — Historical Settlement Intelligence & Historical Pattern Analyzer.
"""

import pytest
import pandas as pd
from backend.services.data_loader import DataLoader
from backend.services.systemic_analyzer import SystemicAnalyzer
from backend.services.historical_pattern_analyzer import HistoricalPatternAnalyzer


def test_dataset_invariants_12155():
    """Verify dataset size, unique transaction IDs, and date range."""
    loader = DataLoader()
    gw_df = loader.get_gateway_data()
    bank_df = loader.get_bank_data()
    ledger_df = loader.get_ledger_data()


    # Unique transactions across gateway dataset
    unique_txns = gw_df["transaction_id"].unique()
    assert len(unique_txns) == 12155, f"Expected 12,155 unique transactions, got {len(unique_txns)}"

    # Date range check
    dates = sorted(gw_df["initiated_at"].str.slice(0, 10).unique())
    assert len(dates) == 9, f"Expected 9 calendar dates, got {len(dates)}"
    assert dates[0] == "2026-08-27"
    assert dates[-1] == "2026-09-04"

    # All 7 demo transactions present
    demo_ids = [
        "TXN10001", "TXN10087", "TXN10142",
        "TXN10211", "TXN10304", "TXN10482", "TXN10531"
    ]
    for tid in demo_ids:
        assert tid in unique_txns, f"Demo transaction {tid} missing from dataset"


def test_recurring_historical_pattern_txn10087():
    """
    Verify TXN10087 triggers recurring historical pattern (HDFC_BANK + RAZORPAY + BANK_TIMEOUT).
    Observed on 3 distinct dates: 2026-08-29 (31 txns), 2026-09-02 (24 txns), 2026-09-04 (130 txns).
    Current vs previous max ratio should be 4.2x (130 / 31).
    """
    analyzer = HistoricalPatternAnalyzer()
    res = analyzer.analyze_transaction("TXN10087")

    assert res.has_historical_pattern is True
    assert res.pattern_signature["bank"] == "HDFC_BANK"
    assert res.pattern_signature["gateway"] == "RAZORPAY"
    assert res.pattern_signature["error_code"] == "BANK_TIMEOUT"

    assert res.occurrence_count == 3
    assert "2026-08-29" in res.distinct_dates
    assert "2026-09-02" in res.distinct_dates
    assert "2026-09-04" in res.distinct_dates

    assert res.previous_max_affected_transactions == 31
    assert res.current_vs_previous_ratio == 4.2
    assert "4.2x larger" in res.comparison_summary


def test_one_off_incident_pattern():
    """
    Verify one-off incident signatures (e.g. SBI + PAYU + BANK_TIMEOUT on 2026-08-28)
    return has_historical_pattern=False because occurrence_count < 2.
    """
    analyzer = HistoricalPatternAnalyzer()
    systemic_analyzer = SystemicAnalyzer()
    incidents = systemic_analyzer.detect_incidents()

    # Find the SBI incident
    sbi_inc = next((inc for inc in incidents if inc.bank == "SBI"), None)
    assert sbi_inc is not None, "SBI incident should exist in dataset"

    # Analyze an affected transaction from the SBI incident
    sample_tid = sbi_inc.affected_transactions[0]
    res = analyzer.analyze_transaction(sample_tid)

    assert res.has_historical_pattern is False
    assert res.occurrence_count == 1
    assert "No previous occurrences" in res.comparison_summary


def test_non_systemic_transaction_history():
    """Verify normal/isolated transaction returns has_historical_pattern=False."""
    analyzer = HistoricalPatternAnalyzer()
    res = analyzer.analyze_transaction("TXN10001")

    assert res.has_historical_pattern is False
    assert res.comparison_summary == "Transaction is not associated with a systemic incident."
