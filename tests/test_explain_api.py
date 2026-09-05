"""
Phase 7 — Tests for POST /api/explain

All LLM calls are mocked. No real API keys are required or used.

Coverage:
  1. Normal transaction → valid AI explanation
  2. Bank delay → explanation reflects delay context
  3. Amount mismatch → explanation reflects mismatch
  4. Missing bank → explanation acknowledges missing record
  5. Missing ledger → explanation acknowledges missing record
  6. Duplicate transaction → explanation reflects duplicate status
  7. Timestamp inconsistency → explanation reflects inconsistency
  8. Systemic incident → explanation includes incident context
  9. Incomplete evidence → fallback language when mock returns incomplete data
 10. Provider exception → fallback + HTTP 200
 11. Malformed/non-JSON LLM response → fallback + HTTP 200
 12. No API key configured → fallback + HTTP 200, no network call
 13. Blank/invalid request body → HTTP 422
"""

import json
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.schemas import (
    AnomalyItem,
    ConfidenceInfo,
    DelaysInfo,
    ExplanationOutput,
    InvestigationResult,
    SystemicIncident,
    TimelineEvent,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared fixtures / factory helpers
# ---------------------------------------------------------------------------

def _make_confidence(score: int = 90, level: str = "VERY_HIGH") -> ConfidenceInfo:
    return ConfidenceInfo(score=score, level=level, breakdown={}, factors=["Gateway record found"])


def _make_delays(
    bank_delay_minutes: Optional[float] = None,
    is_delayed: bool = False,
    delay_reason: Optional[str] = None,
) -> DelaysInfo:
    return DelaysInfo(
        bank_delay_minutes=bank_delay_minutes,
        is_delayed=is_delayed,
        delay_reason=delay_reason,
    )


def _make_investigation(
    transaction_id: str = "TXN10001",
    status: str = "SUCCESS",
    summary: str = "Transaction settled successfully.",
    gateway: Optional[Dict[str, Any]] = None,
    bank: Optional[Dict[str, Any]] = None,
    ledger: Optional[Dict[str, Any]] = None,
    anomalies: Optional[list] = None,
    delays: Optional[DelaysInfo] = None,
    confidence_score: int = 90,
) -> InvestigationResult:
    return InvestigationResult(
        transaction_id=transaction_id,
        status=status,
        summary=summary,
        gateway=gateway or {
            "gateway_reference": "GW_RAZ_TXN10001",
            "gateway_status": "CAPTURED",
            "amount": 5000.0,
            "currency": "INR",
            "response_code": "SUCCESS",
        },
        gateway_records=[
            gateway or {
                "gateway_reference": "GW_RAZ_TXN10001",
                "gateway_status": "CAPTURED",
                "amount": 5000.0,
                "currency": "INR",
                "response_code": "SUCCESS",
            }
        ],
        bank=bank,
        ledger=ledger,
        timeline=[],
        anomalies=anomalies or [],
        evidence=["Gateway record found."],
        exceptions=[],
        delays=delays or _make_delays(),
        confidence=_make_confidence(confidence_score),
    )


def _make_incident() -> SystemicIncident:
    return SystemicIncident(
        incident_id="INC-HDF-20260904-01",
        title="HDFC_BANK settlement degradation",
        severity="CRITICAL",
        status="ACTIVE",
        bank="HDFC_BANK",
        gateway="RAZORPAY",
        dominant_error="BANK_TIMEOUT",
        start_time="2026-09-04T14:00:00",
        end_time="2026-09-04T17:50:00",
        affected_transaction_count=130,
        affected_amount=1_377_500.0,
        common_delay_range_minutes=[46.0, 110.0],
        detection_reasons=["130 delayed transactions at HDFC_BANK via RAZORPAY"],
        affected_transactions=["TXN10087"],
        confidence=95,
    )


_VALID_AI_RESPONSE = {
    "summary": "Settlement completed successfully.",
    "root_cause": "All three systems confirmed the transaction.",
    "recommended_action": "Inform the merchant that their payment settled.",
    "customer_facing_explanation": "Your payment was successfully processed.",
    "uncertainty": "All key facts are confirmed.",
}


def _explain_request(
    investigation: InvestigationResult,
    incident: Optional[SystemicIncident] = None,
) -> dict:
    """Builds the JSON body for POST /api/explain."""
    body: Dict[str, Any] = {"investigation": investigation.model_dump()}
    body["incident"] = incident.model_dump() if incident else None
    return body


# ---------------------------------------------------------------------------
# Test 1 — Normal transaction → valid AI explanation returned
# ---------------------------------------------------------------------------

def test_normal_transaction_ai_explanation():
    inv = _make_investigation()
    with patch(
        "backend.services.ai_service._call_gemini",
        return_value=json.dumps(_VALID_AI_RESPONSE),
    ):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["explanation"]["is_fallback"] is False
    assert data["explanation"]["summary"] == _VALID_AI_RESPONSE["summary"]
    assert data["explanation"]["root_cause"] == _VALID_AI_RESPONSE["root_cause"]
    assert data["explanation"]["fallback_reason"] is None


# ---------------------------------------------------------------------------
# Test 2 — Bank delay → explanation reflects delay context
# ---------------------------------------------------------------------------

def test_bank_delay_explanation():
    inv = _make_investigation(
        transaction_id="TXN10087",
        status="DELAYED",
        summary="Transaction TXN10087 settled with a delay of 92.0 minutes.",
        bank={
            "bank_name": "HDFC_BANK",
            "bank_status": "SETTLED",
            "amount": 10500.0,
            "response_code": "BANK_TIMEOUT",
            "expected_settlement_at": "2026-09-04T14:45:00",
            "settled_at": "2026-09-04T16:17:00",
        },
        ledger={"ledger_status": "POSTED", "amount": 10500.0, "reconciliation_status": "MATCHED"},
        anomalies=[
            AnomalyItem(
                anomaly_type="BANK_DELAY",
                severity="HIGH",
                description="Settlement was delayed by 92.0 minutes.",
                details={"delay_minutes": 92.0},
            )
        ],
        delays=_make_delays(bank_delay_minutes=92.0, is_delayed=True, delay_reason="92 min late"),
        confidence_score=75,
    )

    delay_response = {
        "summary": "Settlement delayed by 92 minutes due to HDFC_BANK timeout.",
        "root_cause": "Bank timeout (BANK_TIMEOUT) at HDFC_BANK caused a 92-minute settlement delay.",
        "recommended_action": "Inform the merchant settlement was completed late.",
        "customer_facing_explanation": "Your payment was captured but settlement was delayed.",
        "uncertainty": "All key facts are confirmed.",
    }

    with patch("backend.services.ai_service._call_gemini", return_value=json.dumps(delay_response)):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["is_fallback"] is False
    assert "92" in data["explanation"]["summary"] or "delay" in data["explanation"]["summary"].lower()


# ---------------------------------------------------------------------------
# Test 3 — Amount mismatch → explanation reflects mismatch
# ---------------------------------------------------------------------------

def test_amount_mismatch_explanation():
    inv = _make_investigation(
        transaction_id="TXN10142",
        status="MISMATCH",
        summary="Amount mismatch detected.",
        bank={
            "bank_name": "ICICI_BANK",
            "bank_status": "SETTLED",
            "amount": 4800.0,
            "response_code": "SUCCESS",
        },
        ledger={"ledger_status": "POSTED", "amount": 5000.0, "reconciliation_status": "MISMATCHED"},
        anomalies=[
            AnomalyItem(
                anomaly_type="AMOUNT_MISMATCH",
                severity="HIGH",
                description="Gateway amount ₹5,000 differs from Bank amount ₹4,800.",
                details={"gateway_amount": 5000.0, "bank_amount": 4800.0},
            )
        ],
        confidence_score=35,
    )

    mismatch_response = {
        "summary": "Amount mismatch: Gateway ₹5,000 vs Bank ₹4,800.",
        "root_cause": "Gateway and bank amounts do not agree.",
        "recommended_action": "Escalate for manual reconciliation.",
        "customer_facing_explanation": "There is a discrepancy in your payment records.",
        "uncertainty": "The records contain conflicting evidence.",
    }

    with patch("backend.services.ai_service._call_gemini", return_value=json.dumps(mismatch_response)):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["is_fallback"] is False
    assert "mismatch" in data["explanation"]["summary"].lower() or "mismatch" in data["explanation"]["root_cause"].lower()


# ---------------------------------------------------------------------------
# Test 4 — Missing bank → explanation acknowledges missing record
# ---------------------------------------------------------------------------

def test_missing_bank_explanation():
    inv = _make_investigation(
        transaction_id="TXN10211",
        status="MISSING_DATA",
        summary="Missing records in Bank.",
        bank=None,
        ledger=None,
        anomalies=[
            AnomalyItem(
                anomaly_type="MISSING_BANK_RECORD",
                severity="HIGH",
                description="Gateway record exists but no Bank settlement record was found.",
                details={},
            )
        ],
        confidence_score=10,
    )

    missing_bank_response = {
        "summary": "No bank settlement record found for TXN10211.",
        "root_cause": "Bank settlement record is missing.",
        "recommended_action": "Escalate to bank for manual tracing.",
        "customer_facing_explanation": "We cannot confirm settlement status at this time.",
        "uncertainty": "The available records do not establish the exact cause.",
    }

    with patch("backend.services.ai_service._call_gemini", return_value=json.dumps(missing_bank_response)):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["is_fallback"] is False


# ---------------------------------------------------------------------------
# Test 5 — Missing ledger → explanation acknowledges missing record
# ---------------------------------------------------------------------------

def test_missing_ledger_explanation():
    inv = _make_investigation(
        transaction_id="TXN10304",
        status="MISSING_DATA",
        summary="Missing records in Ledger.",
        bank={
            "bank_name": "SBI",
            "bank_status": "SETTLED",
            "amount": 7500.0,
            "response_code": "SUCCESS",
        },
        ledger=None,
        anomalies=[
            AnomalyItem(
                anomaly_type="MISSING_LEDGER_RECORD",
                severity="HIGH",
                description="No ledger record found.",
                details={},
            )
        ],
        confidence_score=45,
    )

    missing_ledger_response = {
        "summary": "Ledger record missing for TXN10304.",
        "root_cause": "Internal ledger accounting entry not found.",
        "recommended_action": "Check internal ledger system.",
        "customer_facing_explanation": "Your payment was received but internal posting is pending.",
        "uncertainty": "The available records do not establish the exact cause.",
    }

    with patch("backend.services.ai_service._call_gemini", return_value=json.dumps(missing_ledger_response)):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["is_fallback"] is False


# ---------------------------------------------------------------------------
# Test 6 — Duplicate transaction → explanation reflects duplicate
# ---------------------------------------------------------------------------

def test_duplicate_transaction_explanation():
    inv = _make_investigation(
        transaction_id="TXN10482",
        status="DUPLICATE",
        summary="2 duplicate Gateway records detected.",
        anomalies=[
            AnomalyItem(
                anomaly_type="DUPLICATE_GATEWAY_RECORD",
                severity="CRITICAL",
                description="2 Gateway records found for TXN10482.",
                details={"count": 2},
            )
        ],
        confidence_score=20,
    )

    dup_response = {
        "summary": "Duplicate gateway submission detected for TXN10482.",
        "root_cause": "Two gateway records were submitted for the same transaction.",
        "recommended_action": "Do not process payment. Escalate for duplicate investigation.",
        "customer_facing_explanation": "A duplicate submission was detected. Our team is investigating.",
        "uncertainty": "The records contain conflicting evidence.",
    }

    with patch("backend.services.ai_service._call_gemini", return_value=json.dumps(dup_response)):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["is_fallback"] is False


# ---------------------------------------------------------------------------
# Test 7 — Timestamp inconsistency → explanation reflects inconsistency
# ---------------------------------------------------------------------------

def test_timestamp_inconsistency_explanation():
    inv = _make_investigation(
        transaction_id="TXN10531",
        status="INCONSISTENT",
        summary="Data inconsistency detected (TIMESTAMP_INCONSISTENCY).",
        bank={
            "bank_name": "AXIS_BANK",
            "bank_status": "SETTLED",
            "amount": 3200.0,
            "response_code": "SUCCESS",
            "settled_at": "2026-09-04T08:00:00",
        },
        anomalies=[
            AnomalyItem(
                anomaly_type="TIMESTAMP_INCONSISTENCY",
                severity="HIGH",
                description="Bank settlement occurred before Gateway initiation.",
                details={},
            )
        ],
        confidence_score=10,
    )

    ts_response = {
        "summary": "Chronological inconsistency detected: bank settled before gateway initiated.",
        "root_cause": "Impossible timestamp sequence — bank record predates gateway initiation.",
        "recommended_action": "Do not confirm settlement. Escalate for data integrity review.",
        "customer_facing_explanation": "There is an inconsistency in your payment records. Our team is investigating.",
        "uncertainty": "The records contain conflicting evidence, so the exact cause cannot be confirmed.",
    }

    with patch("backend.services.ai_service._call_gemini", return_value=json.dumps(ts_response)):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["is_fallback"] is False


# ---------------------------------------------------------------------------
# Test 8 — Systemic incident → explanation context includes incident data
# ---------------------------------------------------------------------------

def test_systemic_incident_explanation():
    inv = _make_investigation(
        transaction_id="TXN10087",
        status="DELAYED",
        summary="Transaction TXN10087 settled with a delay of 92.0 minutes.",
        bank={
            "bank_name": "HDFC_BANK",
            "bank_status": "SETTLED",
            "amount": 10500.0,
            "response_code": "BANK_TIMEOUT",
        },
        ledger={"ledger_status": "POSTED", "amount": 10500.0, "reconciliation_status": "MATCHED"},
        anomalies=[
            AnomalyItem(
                anomaly_type="BANK_DELAY",
                severity="HIGH",
                description="Delayed 92 minutes.",
                details={"delay_minutes": 92.0},
            )
        ],
        delays=_make_delays(bank_delay_minutes=92.0, is_delayed=True),
        confidence_score=75,
    )
    incident = _make_incident()

    systemic_response = {
        "summary": "Delayed 92 minutes. Part of a systemic HDFC_BANK outage affecting 130 transactions.",
        "root_cause": "BANK_TIMEOUT at HDFC_BANK via RAZORPAY — part of a CRITICAL incident.",
        "recommended_action": "Inform merchant of delay. Reference incident INC-HDF-20260904-01.",
        "customer_facing_explanation": "Your payment was captured but affected by a bank outage. Settlement is complete.",
        "uncertainty": "All key facts are confirmed. Incident scope: 130 transactions, ₹1,377,500.",
    }

    with patch("backend.services.ai_service._call_gemini", return_value=json.dumps(systemic_response)):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv, incident))

    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["is_fallback"] is False
    # Verify incident facts appear in explanation
    assert "130" in data["explanation"]["summary"] or "130" in data["explanation"]["uncertainty"]


# ---------------------------------------------------------------------------
# Test 9 — Incomplete evidence → deterministic fallback language
# ---------------------------------------------------------------------------

def test_incomplete_evidence_fallback_language():
    """When the mock returns a valid response with uncertainty language for incomplete evidence."""
    inv = _make_investigation(
        transaction_id="TXN10211",
        status="MISSING_DATA",
        summary="Missing records in Bank.",
        bank=None,
        ledger=None,
        anomalies=[
            AnomalyItem(
                anomaly_type="MISSING_BANK_RECORD",
                severity="HIGH",
                description="No bank record found.",
                details={},
            )
        ],
        confidence_score=10,
    )

    incomplete_response = {
        "summary": "Settlement status cannot be fully confirmed.",
        "root_cause": "Bank record is missing.",
        "recommended_action": "Investigate missing bank record.",
        "customer_facing_explanation": "We are unable to confirm settlement. Investigating.",
        "uncertainty": "The available records do not establish the exact cause.",
    }

    with patch("backend.services.ai_service._call_gemini", return_value=json.dumps(incomplete_response)):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert "available records" in data["explanation"]["uncertainty"].lower() or \
           "cannot" in data["explanation"]["uncertainty"].lower()


# ---------------------------------------------------------------------------
# Test 10 — Provider exception → fallback + HTTP 200
# ---------------------------------------------------------------------------

def test_provider_exception_returns_fallback():
    inv = _make_investigation()

    with patch(
        "backend.services.ai_service._call_gemini",
        side_effect=ConnectionError("Network unreachable"),
    ):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["explanation"]["is_fallback"] is True
    assert data["explanation"]["fallback_reason"] is not None
    assert "ConnectionError" in data["explanation"]["fallback_reason"]


# ---------------------------------------------------------------------------
# Test 11 — Malformed/non-JSON response → fallback + HTTP 200
# ---------------------------------------------------------------------------

def test_malformed_llm_response_returns_fallback():
    inv = _make_investigation()

    with patch(
        "backend.services.ai_service._call_gemini",
        return_value="This is not valid JSON at all!",
    ):
        with patch("backend.services.ai_service.GEMINI_API_KEY", "fake-key"):
            response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["explanation"]["is_fallback"] is True
    assert "non-JSON" in data["explanation"]["fallback_reason"] or \
           "invalid" in data["explanation"]["fallback_reason"].lower()


# ---------------------------------------------------------------------------
# Test 12 — No API key → fallback + HTTP 200, no network call
# ---------------------------------------------------------------------------

def test_no_api_key_returns_fallback_without_network_call():
    """With an empty API key, generate_explanation must return fallback immediately."""
    inv = _make_investigation()

    # Patch keys to empty and provider to gemini
    with patch("backend.services.ai_service.GEMINI_API_KEY", ""):
        with patch("backend.services.ai_service.LLM_PROVIDER", "gemini"):
            # _call_gemini must NOT be called — patch it to raise if invoked
            with patch(
                "backend.services.ai_service._call_gemini",
                side_effect=AssertionError("_call_gemini must not be called with no API key"),
            ):
                response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["explanation"]["is_fallback"] is True
    assert "API key not configured" in data["explanation"]["fallback_reason"]


# ---------------------------------------------------------------------------
# Test 13 — Invalid/blank request body → HTTP 422
# ---------------------------------------------------------------------------

def test_blank_request_returns_422():
    """Missing 'investigation' field should cause Pydantic validation error → 422."""
    response = client.post("/api/explain", json={})
    assert response.status_code == 422


def test_null_investigation_returns_422():
    """Explicitly null 'investigation' is not a valid InvestigationResult → 422."""
    response = client.post("/api/explain", json={"investigation": None, "incident": None})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Verify: Groq fallback path (no key → immediate fallback)
# ---------------------------------------------------------------------------

def test_groq_no_api_key_returns_fallback():
    inv = _make_investigation()

    with patch("backend.services.ai_service.GROQ_API_KEY", ""):
        with patch("backend.services.ai_service.LLM_PROVIDER", "groq"):
            with patch(
                "backend.services.ai_service._call_groq",
                side_effect=AssertionError("_call_groq must not be called with no API key"),
            ):
                response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    data = response.json()
    assert data["explanation"]["is_fallback"] is True
    assert "API key not configured" in data["explanation"]["fallback_reason"]


# ---------------------------------------------------------------------------
# Verify: Groq provider used when LLM_PROVIDER=groq
# ---------------------------------------------------------------------------

def test_groq_provider_called_when_configured():
    inv = _make_investigation()

    with patch("backend.services.ai_service.GROQ_API_KEY", "fake-groq-key"):
        with patch("backend.services.ai_service.LLM_PROVIDER", "groq"):
            with patch(
                "backend.services.ai_service._call_groq",
                return_value=json.dumps(_VALID_AI_RESPONSE),
            ) as mock_groq:
                response = client.post("/api/explain", json=_explain_request(inv))

    assert response.status_code == 200
    mock_groq.assert_called_once()
    data = response.json()
    assert data["explanation"]["is_fallback"] is False
