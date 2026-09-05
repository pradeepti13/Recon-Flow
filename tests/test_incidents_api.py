"""
Phase 6 - Incidents API Tests
Tests HTTP endpoints exposed by backend/api/incidents.py:
  - GET /api/incidents
  - GET /api/incidents/transaction/{transaction_id}
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.data_loader import clear_cache
from backend.services.systemic_analyzer import clear_incident_cache

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_all_caches():
    clear_cache()
    clear_incident_cache()
    yield
    clear_cache()
    clear_incident_cache()


class TestIncidentsApi:
    """Verifies the GET /api/incidents endpoint."""

    def test_get_active_incidents_returns_200(self):
        resp = client.get("/api/incidents")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        hdfc_inc = next((inc for inc in data if inc["bank"] == "HDFC_BANK" and inc["affected_transaction_count"] == 130), None)
        assert hdfc_inc is not None
        assert hdfc_inc["gateway"] == "RAZORPAY"
        assert hdfc_inc["dominant_error"] == "BANK_TIMEOUT"


class TestTransactionIncidentAssociationApi:
    """Verifies the GET /api/incidents/transaction/{transaction_id} endpoint."""

    def test_systemic_transaction_returns_associated_incident(self):
        resp = client.get("/api/incidents/transaction/TXN10087")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_systemic"] is True
        assert data["incident"] is not None
        assert data["incident"]["bank"] == "HDFC_BANK"
        assert data["incident"]["gateway"] == "RAZORPAY"
        assert data["incident"]["affected_transaction_count"] == 130


    def test_normal_transaction_returns_not_systemic(self):
        resp = client.get("/api/incidents/transaction/TXN10001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_systemic"] is False
        assert data["incident"] is None

    def test_isolated_anomaly_transaction_returns_not_systemic(self):
        resp = client.get("/api/incidents/transaction/TXN10142")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_systemic"] is False
        assert data["incident"] is None

    def test_unknown_transaction_returns_200_not_systemic(self):
        """
        Unknown IDs return 200 with is_systemic: false and incident: null.
        Transaction existence validation is authoritatively handled by /api/investigate (404).
        """
        resp = client.get("/api/incidents/transaction/TXN99999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_systemic"] is False
        assert data["incident"] is None
