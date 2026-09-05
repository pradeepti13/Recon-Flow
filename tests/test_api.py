"""
Phase 4 — FastAPI Integration Tests
Tests the investigation API endpoints exposed by backend/api/investigation.py.

No mocking; uses the real investigation engine and CSV datasets.
Covers:
  - POST /api/investigate  (successful, anomaly, unknown, blank ID)
  - GET  /api/investigate/{transaction_id}  (successful, anomaly, unknown)
  - CORS headers for the configured local React origin
  - Health and root endpoints preserved from Phase 0
  - Response envelope shape (ok, result fields)
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.data_loader import clear_cache


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_loader_cache():
    """Clear the DataLoader cache between tests for isolation."""
    clear_cache()
    yield
    clear_cache()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _post_investigate(transaction_id: str):
    """POST /api/investigate with the given transaction_id."""
    return client.post("/api/investigate", json={"transaction_id": transaction_id})


def _get_investigate(transaction_id: str):
    """GET /api/investigate/{transaction_id}."""
    return client.get(f"/api/investigate/{transaction_id}")


# ---------------------------------------------------------------------------
# POST /api/investigate — successful investigation (TXN10001, normal)
# ---------------------------------------------------------------------------

class TestPostInvestigateNormal:
    """POST /api/investigate with a known normal transaction (TXN10001)."""

    def test_returns_200(self):
        resp = _post_investigate("TXN10001")
        assert resp.status_code == 200

    def test_response_envelope_ok(self):
        data = _post_investigate("TXN10001").json()
        assert data["ok"] is True
        assert "result" in data

    def test_transaction_id_in_result(self):
        result = _post_investigate("TXN10001").json()["result"]
        assert result["transaction_id"] == "TXN10001"

    def test_status_success(self):
        result = _post_investigate("TXN10001").json()["result"]
        assert result["status"] == "SUCCESS"

    def test_confidence_high(self):
        result = _post_investigate("TXN10001").json()["result"]
        assert result["confidence"]["score"] >= 75
        assert result["confidence"]["level"] in ("HIGH", "VERY_HIGH")

    def test_all_three_records_present(self):
        result = _post_investigate("TXN10001").json()["result"]
        assert result["gateway"] is not None
        assert result["bank"] is not None
        assert result["ledger"] is not None

    def test_no_anomalies(self):
        result = _post_investigate("TXN10001").json()["result"]
        assert result["anomalies"] == []

    def test_timeline_nonempty_and_chronological(self):
        result = _post_investigate("TXN10001").json()["result"]
        ts_list = [e["timestamp"] for e in result["timeline"] if e["timestamp"]]
        assert len(ts_list) > 0
        assert ts_list == sorted(ts_list)

    def test_evidence_nonempty(self):
        result = _post_investigate("TXN10001").json()["result"]
        assert len(result["evidence"]) > 0

    def test_summary_nonempty(self):
        result = _post_investigate("TXN10001").json()["result"]
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0

    def test_delays_field_present(self):
        result = _post_investigate("TXN10001").json()["result"]
        assert "delays" in result
        assert result["delays"]["is_delayed"] is False

    def test_gateway_records_list_present(self):
        result = _post_investigate("TXN10001").json()["result"]
        assert isinstance(result["gateway_records"], list)
        assert len(result["gateway_records"]) == 1


# ---------------------------------------------------------------------------
# POST /api/investigate — anomaly case (TXN10087, bank delay)
# ---------------------------------------------------------------------------

class TestPostInvestigateBankDelay:
    """POST /api/investigate with the bank-delay transaction (TXN10087)."""

    def test_returns_200(self):
        resp = _post_investigate("TXN10087")
        assert resp.status_code == 200

    def test_status_delayed(self):
        result = _post_investigate("TXN10087").json()["result"]
        assert result["status"] == "DELAYED"

    def test_bank_delay_anomaly_present(self):
        result = _post_investigate("TXN10087").json()["result"]
        anomaly_types = [a["anomaly_type"] for a in result["anomalies"]]
        assert "BANK_DELAY" in anomaly_types

    def test_bank_delay_high_severity(self):
        result = _post_investigate("TXN10087").json()["result"]
        bank_delay = next(a for a in result["anomalies"] if a["anomaly_type"] == "BANK_DELAY")
        assert bank_delay["severity"] == "HIGH"

    def test_is_delayed_true(self):
        result = _post_investigate("TXN10087").json()["result"]
        assert result["delays"]["is_delayed"] is True
        assert result["delays"]["bank_delay_minutes"] is not None
        assert result["delays"]["bank_delay_minutes"] > 60

    def test_all_records_present(self):
        result = _post_investigate("TXN10087").json()["result"]
        assert result["gateway"] is not None
        assert result["bank"] is not None
        assert result["ledger"] is not None

    def test_confidence_reduced_but_reasonable(self):
        result = _post_investigate("TXN10087").json()["result"]
        assert 0 < result["confidence"]["score"] < 100

    def test_no_systemic_anomaly(self):
        """Phase 3/4 must not produce systemic incident anomalies."""
        result = _post_investigate("TXN10087").json()["result"]
        systemic = [a for a in result["anomalies"] if "SYSTEMIC" in a["anomaly_type"].upper()]
        assert systemic == []


# ---------------------------------------------------------------------------
# POST /api/investigate — unknown transaction ID
# ---------------------------------------------------------------------------

class TestPostInvestigateUnknown:
    """POST /api/investigate with an ID that does not exist in any dataset."""

    def test_returns_404(self):
        """An unknown transaction ID must return HTTP 404."""
        resp = _post_investigate("TXN_DOES_NOT_EXIST_99999")
        assert resp.status_code == 404

    def test_error_detail_present(self):
        data = _post_investigate("TXN_DOES_NOT_EXIST_99999").json()
        # FastAPI serialises HTTPException as {"detail": "..."}
        assert "detail" in data
        assert "TXN_DOES_NOT_EXIST_99999" in data["detail"]

    def test_no_result_in_404_response(self):
        data = _post_investigate("TXN_DOES_NOT_EXIST_99999").json()
        assert "result" not in data


# ---------------------------------------------------------------------------
# POST /api/investigate — blank / empty transaction ID
# ---------------------------------------------------------------------------

class TestPostInvestigateBlankId:
    """POST /api/investigate with a blank transaction_id must return 400."""

    def test_blank_string_returns_400(self):
        """A whitespace-only transaction_id must be rejected with 400."""
        resp = client.post("/api/investigate", json={"transaction_id": "   "})
        assert resp.status_code == 400

    def test_empty_string_rejected_by_pydantic(self):
        """An empty string violates min_length=1 and is rejected with 422."""
        resp = client.post("/api/investigate", json={"transaction_id": ""})
        assert resp.status_code == 422

    def test_missing_transaction_id_rejected(self):
        """Missing transaction_id key is rejected with 422."""
        resp = client.post("/api/investigate", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/investigate/{transaction_id} — convenience variant
# ---------------------------------------------------------------------------

class TestGetInvestigate:
    """GET /api/investigate/{transaction_id} — must behave identically to POST."""

    def test_normal_returns_200(self):
        resp = _get_investigate("TXN10001")
        assert resp.status_code == 200

    def test_normal_status_success(self):
        result = _get_investigate("TXN10001").json()["result"]
        assert result["status"] == "SUCCESS"

    def test_bank_delay_status_delayed(self):
        result = _get_investigate("TXN10087").json()["result"]
        assert result["status"] == "DELAYED"

    def test_bank_delay_anomaly(self):
        result = _get_investigate("TXN10087").json()["result"]
        anomaly_types = [a["anomaly_type"] for a in result["anomalies"]]
        assert "BANK_DELAY" in anomaly_types

    def test_unknown_returns_404(self):
        resp = _get_investigate("TXN_DOES_NOT_EXIST_GET_88888")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
        assert "result" not in data

    def test_amount_mismatch_status(self):
        result = _get_investigate("TXN10142").json()["result"]
        assert result["status"] == "MISMATCH"

    def test_missing_bank_status(self):
        result = _get_investigate("TXN10211").json()["result"]
        assert result["status"] == "MISSING_DATA"

    def test_missing_ledger_status(self):
        result = _get_investigate("TXN10304").json()["result"]
        assert result["status"] == "MISSING_DATA"

    def test_duplicate_status(self):
        result = _get_investigate("TXN10482").json()["result"]
        assert result["status"] == "DUPLICATE"

    def test_timestamp_error_status(self):
        result = _get_investigate("TXN10531").json()["result"]
        assert result["status"] == "INCONSISTENT"


# ---------------------------------------------------------------------------
# Additional demo cases via POST
# ---------------------------------------------------------------------------

class TestPostInvestigateAllDemoCases:
    """POST /api/investigate against each known demo case — all must return 200."""

    DEMO_CASES = {
        "TXN10001": "SUCCESS",
        "TXN10087": "DELAYED",
        "TXN10142": "MISMATCH",
        "TXN10211": "MISSING_DATA",
        "TXN10304": "MISSING_DATA",
        "TXN10482": "DUPLICATE",
        "TXN10531": "INCONSISTENT",
    }

    @pytest.mark.parametrize("txn_id,expected_status", DEMO_CASES.items())
    def test_demo_case_status(self, txn_id, expected_status):
        resp = _post_investigate(txn_id)
        assert resp.status_code == 200, f"{txn_id}: expected 200, got {resp.status_code}"
        result = resp.json()["result"]
        assert result["status"] == expected_status, (
            f"{txn_id}: expected status={expected_status}, got={result['status']}"
        )

    @pytest.mark.parametrize("txn_id,_", DEMO_CASES.items())
    def test_demo_case_has_valid_confidence(self, txn_id, _):
        result = _post_investigate(txn_id).json()["result"]
        score = result["confidence"]["score"]
        assert 0 <= score <= 100, f"{txn_id}: confidence score out of range: {score}"
        assert result["confidence"]["level"] in ("VERY_HIGH", "HIGH", "MEDIUM", "LOW")


# ---------------------------------------------------------------------------
# CORS — configured origin must be permitted
# ---------------------------------------------------------------------------

class TestCORS:
    """Verify CORS headers are returned for the configured React dev server origin."""

    FRONTEND_ORIGIN = "http://localhost:5173"

    def test_cors_header_present_for_configured_origin(self):
        """
        A preflight OPTIONS request from the local React dev server origin
        must receive an Access-Control-Allow-Origin header.
        """
        resp = client.options(
            "/api/investigate",
            headers={
                "Origin": self.FRONTEND_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        # FastAPI + Starlette return 200 for valid preflight OPTIONS
        assert resp.status_code == 200
        acao = resp.headers.get("access-control-allow-origin", "")
        assert self.FRONTEND_ORIGIN in acao or acao == "*", (
            f"Expected CORS allow-origin to include {self.FRONTEND_ORIGIN!r}, got {acao!r}"
        )

    def test_cors_header_on_get_request(self):
        """Simple GET requests from the configured origin must also carry the CORS header."""
        resp = client.get(
            "/api/investigate/TXN10001",
            headers={"Origin": self.FRONTEND_ORIGIN},
        )
        assert resp.status_code == 200
        acao = resp.headers.get("access-control-allow-origin", "")
        assert acao != "", "Expected access-control-allow-origin header to be present"

    def test_cors_header_on_post_request(self):
        """POST requests from the configured origin must carry the CORS header."""
        resp = client.post(
            "/api/investigate",
            json={"transaction_id": "TXN10001"},
            headers={"Origin": self.FRONTEND_ORIGIN},
        )
        assert resp.status_code == 200
        acao = resp.headers.get("access-control-allow-origin", "")
        assert acao != "", "Expected access-control-allow-origin header to be present"


# ---------------------------------------------------------------------------
# Response contract — required fields always present
# ---------------------------------------------------------------------------

class TestResponseContract:
    """All required fields must be present in every successful response."""

    REQUIRED_RESULT_FIELDS = [
        "transaction_id", "status", "summary",
        "gateway", "gateway_records", "bank", "ledger",
        "timeline", "anomalies", "evidence", "exceptions",
        "delays", "confidence",
    ]

    REQUIRED_CONFIDENCE_FIELDS = ["score", "level", "breakdown", "factors"]
    REQUIRED_DELAYS_FIELDS = ["bank_delay_minutes", "gateway_capture_delay_seconds",
                               "settlement_initiation_delay_seconds", "is_delayed", "delay_reason"]

    @pytest.mark.parametrize("txn_id", ["TXN10001", "TXN10087"])
    def test_all_result_fields_present(self, txn_id):
        result = _post_investigate(txn_id).json()["result"]
        for field in self.REQUIRED_RESULT_FIELDS:
            assert field in result, f"Field '{field}' missing from result for {txn_id}"

    @pytest.mark.parametrize("txn_id", ["TXN10001", "TXN10087"])
    def test_confidence_sub_fields(self, txn_id):
        confidence = _post_investigate(txn_id).json()["result"]["confidence"]
        for field in self.REQUIRED_CONFIDENCE_FIELDS:
            assert field in confidence, f"Confidence field '{field}' missing for {txn_id}"

    @pytest.mark.parametrize("txn_id", ["TXN10001", "TXN10087"])
    def test_delays_sub_fields(self, txn_id):
        delays = _post_investigate(txn_id).json()["result"]["delays"]
        for field in self.REQUIRED_DELAYS_FIELDS:
            assert field in delays, f"Delays field '{field}' missing for {txn_id}"

    def test_status_values_from_allowed_set(self):
        """All known demo transactions must return a status from the agreed set."""
        valid_statuses = {
            "SUCCESS", "DELAYED", "MISMATCH", "MISSING_DATA",
            "DUPLICATE", "INCONSISTENT", "FAILED",
        }
        for txn_id in ["TXN10001", "TXN10087", "TXN10142",
                        "TXN10211", "TXN10304", "TXN10482",
                        "TXN10531"]:
            resp = _post_investigate(txn_id)
            assert resp.status_code == 200, f"{txn_id}: expected 200, got {resp.status_code}"
            result = resp.json()["result"]
            assert result["status"] in valid_statuses, (
                f"{txn_id} returned unexpected status: {result['status']}"
            )

    def test_unknown_transaction_returns_404_not_200(self):
        """Unknown transaction IDs must return 404, not 200 with UNKNOWN status."""
        resp = _post_investigate("TXN_DOES_NOT_EXIST_STATUS")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Health endpoints — must remain intact from Phase 0
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    """Phase 0 health endpoints must not be broken by Phase 4 changes."""

    def test_root_still_healthy(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_health_endpoint_still_works(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "docs" in data["endpoints"]

    def test_openapi_schema_still_available(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        info = resp.json()["info"]
        assert info["title"] == "Settlement Intelligence API"

    def test_swagger_ui_still_available(self):
        resp = client.get("/docs")
        assert resp.status_code == 200
