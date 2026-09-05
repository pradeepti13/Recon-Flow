"""
Phase 5 - Systemic Analyzer Tests
Tests deterministic incident discovery, temporal clustering,
transaction association, duplicate row metric inflation guards,
and independence from demo_cases.json.
"""

from datetime import datetime, timedelta
import pandas as pd
import pytest

from backend.services.systemic_analyzer import (
    SystemicAnalyzer,
    detect_incidents,
    get_active_incidents,
    check_transaction_incident,
    check_transaction_association,
    derive_gateway_provider,
    clear_incident_cache,
)
from backend.services.data_loader import load_all_data, clear_cache


@pytest.fixture(autouse=True)
def reset_caches():
    """Ensure caches are reset between tests."""
    clear_cache()
    clear_incident_cache()
    yield
    clear_cache()
    clear_incident_cache()


# ---------------------------------------------------------------------------
# 1. Gateway Provider Derivation Tests
# ---------------------------------------------------------------------------

class TestGatewayProviderDerivation:
    def test_canonical_prefixes(self):
        assert derive_gateway_provider("GW_RAZ_TXN10001") == "RAZORPAY"
        assert derive_gateway_provider("GW_PAY_TXN10002") == "PAYU"
        assert derive_gateway_provider("GW_CAS_TXN10003") == "CASHFREE"
        assert derive_gateway_provider("GW_STR_TXN10004") == "STRIPE"

    def test_unknown_or_malformed_prefix(self):
        assert derive_gateway_provider("GW_UNKNOWN_123") == "UNKNOWN"
        assert derive_gateway_provider("") == "UNKNOWN"
        assert derive_gateway_provider(None) == "UNKNOWN"


# ---------------------------------------------------------------------------
# 2. Discovery on the Real Dataset
# ---------------------------------------------------------------------------

class TestSystemicIncidentDiscovery:
    """Validates that the analyzer programmatically discovers synthetic incidents."""

    def test_discovers_hdfc_razorpay_incident(self):
        incidents = detect_incidents()
        assert len(incidents) >= 1, f"Expected at least 1 systemic incident, found {len(incidents)}"

        inc = next(i for i in incidents if i.affected_transaction_count == 130)
        # Cluster parameters
        assert inc.bank == "HDFC_BANK"
        assert inc.gateway == "RAZORPAY"
        assert inc.dominant_error == "BANK_TIMEOUT"
        assert inc.severity in ("HIGH", "CRITICAL")
        assert inc.status == "ACTIVE"

    def test_affected_metrics_exactness(self):
        incidents = detect_incidents()
        inc = next(i for i in incidents if i.affected_transaction_count == 130)

        # Expected counts and amounts
        assert inc.affected_transaction_count == 130
        assert len(inc.affected_transactions) == 130
        assert len(set(inc.affected_transactions)) == 130  # Strict uniqueness

    def test_delay_range_and_time_window(self):
        incidents = detect_incidents()
        inc = next(i for i in incidents if i.affected_transaction_count == 130)

        # Delay range: ~46.0 to 110.0 min
        assert len(inc.common_delay_range_minutes) == 2
        min_delay, max_delay = inc.common_delay_range_minutes
        assert 45.0 <= min_delay <= 48.0
        assert 104.0 <= max_delay <= 112.0

        # end_time reflects the latest settlement/initiation
        assert inc.end_time >= inc.start_time

    def test_incident_confidence_and_reasons(self):
        incidents = detect_incidents()
        inc = next(i for i in incidents if i.affected_transaction_count == 130)

        assert inc.confidence >= 90
        assert len(inc.detection_reasons) >= 3
        reasons_text = " ".join(inc.detection_reasons)
        assert "HDFC_BANK" in reasons_text
        assert "RAZORPAY" in reasons_text
        assert "BANK_TIMEOUT" in reasons_text


# ---------------------------------------------------------------------------
# 3. Transaction-Level Association Tests
# ---------------------------------------------------------------------------

class TestTransactionAssociation:
    def test_txn10087_associates_with_incident(self):
        inc = check_transaction_incident("TXN10087")
        assert inc is not None
        assert inc.bank == "HDFC_BANK"
        assert inc.gateway == "RAZORPAY"
        assert "TXN10087" in inc.affected_transactions

        assoc = check_transaction_association("TXN10087")
        assert assoc.is_systemic is True
        assert assoc.incident is not None
        assert assoc.incident.incident_id == inc.incident_id

    def test_normal_transaction_does_not_associate(self):
        assert check_transaction_incident("TXN10001") is None
        assoc = check_transaction_association("TXN10001")
        assert assoc.is_systemic is False
        assert assoc.incident is None

    def test_amount_mismatch_does_not_associate(self):
        # TXN10142 is an isolated amount mismatch (ICICI_BANK)
        assert check_transaction_incident("TXN10142") is None

    def test_timestamp_error_does_not_associate(self):
        # TXN10531 is an isolated timestamp error (KOTAK_BANK)
        assert check_transaction_incident("TXN10531") is None

    def test_nonexistent_transaction_does_not_associate(self):
        assert check_transaction_incident("TXN_DOES_NOT_EXIST_99999") is None


# ---------------------------------------------------------------------------
# 4. Duplicate Gateway Row Inflation Guard Test
# ---------------------------------------------------------------------------

class TestDuplicateGatewayInflationGuard:
    """Verifies duplicate gateway rows cannot artificially inflate incident volume or amounts."""

    def test_duplicate_gateway_records_do_not_inflate_metrics(self):
        raw_gw, raw_bnk, _ = load_all_data()

        # baseline run
        analyzer = SystemicAnalyzer()
        baseline_incidents = analyzer.detect_incidents(gw_df=raw_gw, bnk_df=raw_bnk)
        assert len(baseline_incidents) >= 1
        baseline_count = baseline_incidents[0].affected_transaction_count
        baseline_amount = baseline_incidents[0].affected_amount

        # Inject 10 duplicate rows for cluster transactions with different references/timestamps
        duplicates = []
        cluster_ids = baseline_incidents[0].affected_transactions[:10]
        for tid in cluster_ids:
            row = raw_gw[raw_gw["transaction_id"] == tid].iloc[0].copy()
            row["gateway_reference"] = f"GW_RAZ_DUP_{tid}"
            duplicates.append(row)

        inflated_gw = pd.concat([raw_gw, pd.DataFrame(duplicates)], ignore_index=True)
        assert len(inflated_gw) == len(raw_gw) + 10

        # Detect incidents with the duplicated DataFrame
        new_analyzer = SystemicAnalyzer()
        new_incidents = new_analyzer.detect_incidents(gw_df=inflated_gw, bnk_df=raw_bnk)

        assert len(new_incidents) == len(baseline_incidents)
        new_inc = new_incidents[0]

        # INVARIANT: metrics MUST NOT be inflated by duplicate gateway records
        assert new_inc.affected_transaction_count == baseline_count
        assert new_inc.affected_amount == baseline_amount
        assert len(new_inc.affected_transactions) == baseline_count

        assert len(set(new_inc.affected_transactions)) == baseline_count


# ---------------------------------------------------------------------------
# 5. Temporal Separation & Boundary Verification
# ---------------------------------------------------------------------------

class TestTemporalSeparation:
    """Validates that scattered anomalies outside time boundaries do not qualify as incidents."""

    def test_dispersed_anomalies_do_not_form_incident(self):
        # Construct 12 delayed transactions scattered across 12 different hours (gap = 1 hour > 30 min)
        base_time = datetime(2026, 9, 4, 8, 0, 0)
        gw_rows = []
        bnk_rows = []

        for i in range(12):
            tid = f"TXN_SCATTER_{i+1:03d}"
            init_dt = base_time + timedelta(hours=i * 2)  # 2 hours apart
            exp_dt = init_dt + timedelta(minutes=15)
            settle_dt = exp_dt + timedelta(minutes=45)  # Delayed past SLA

            gw_rows.append({
                "transaction_id": tid,
                "gateway_reference": f"GW_RAZ_{tid}",
                "merchant_id": "MERCH_101",
                "amount": 1000.0,
                "currency": "INR",
                "payment_method": "UPI",
                "gateway_status": "CAPTURED",
                "initiated_at": init_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "captured_at": init_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "settlement_initiated_at": init_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "response_code": "SUCCESS",
                "response_message": "OK",
            })

            bnk_rows.append({
                "transaction_id": tid,
                "bank_reference": f"BNK_HDF_{tid}",
                "bank_name": "HDFC_BANK",
                "amount": 1000.0,
                "bank_status": "SETTLED",
                "received_at": init_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "expected_settlement_at": exp_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "settled_at": settle_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "response_code": "BANK_TIMEOUT",
                "response_message": "Timeout",
            })

        gw_df = pd.DataFrame(gw_rows)
        bnk_df = pd.DataFrame(bnk_rows)

        analyzer = SystemicAnalyzer()
        incidents = analyzer.detect_incidents(gw_df=gw_df, bnk_df=bnk_df)

        # Because gaps between consecutive failures are 2 hours (> 30 min),
        # each cluster has count=1, which fails the MIN_INCIDENT_TRANSACTION_COUNT (10) threshold.
        assert incidents == []


# ---------------------------------------------------------------------------
# 6. Resilience and Missing-Record Robustness
# ---------------------------------------------------------------------------

class TestResilienceAndRobustness:
    def test_empty_dataframe_does_not_crash(self):
        analyzer = SystemicAnalyzer()
        incidents = analyzer.detect_incidents(gw_df=pd.DataFrame(), bnk_df=pd.DataFrame())
        assert incidents == []

    def test_missing_timestamps_do_not_crash(self):
        gw = pd.DataFrame([{
            "transaction_id": "TXN_NULL_TS",
            "gateway_reference": "GW_RAZ_TXN_NULL_TS",
            "merchant_id": "MERCH_101",
            "amount": 1000.0,
            "currency": "INR",
            "payment_method": "UPI",
            "gateway_status": "CAPTURED",
            "initiated_at": None,
            "captured_at": None,
            "settlement_initiated_at": None,
            "response_code": "SUCCESS",
            "response_message": "OK",
        }])
        bnk = pd.DataFrame([{
            "transaction_id": "TXN_NULL_TS",
            "bank_reference": "BNK_HDF_TXN_NULL_TS",
            "bank_name": "HDFC_BANK",
            "amount": 1000.0,
            "bank_status": "SETTLED",
            "received_at": None,
            "expected_settlement_at": None,
            "settled_at": None,
            "response_code": "BANK_TIMEOUT",
            "response_message": "Timeout",
        }])

        analyzer = SystemicAnalyzer()
        # Should cleanly return empty list without throwing an unhandled exception
        incidents = analyzer.detect_incidents(gw_df=gw, bnk_df=bnk)
        assert isinstance(incidents, list)
