"""
Phase 6 - Incidents API Router
Exposes systemic incident discovery and transaction-level association.
Lightweight router connecting Phase 5 Systemic Analyzer to the frontend.
Does NOT modify or duplicate transaction-level investigation.
"""

from typing import List
from fastapi import APIRouter
from backend.models.schemas import SystemicIncident, IncidentAssociation, HistoricalPatternResult
from backend.services.systemic_analyzer import (
    get_active_incidents,
    check_transaction_association,
)
from backend.services.historical_pattern_analyzer import HistoricalPatternAnalyzer

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

_historical_analyzer = HistoricalPatternAnalyzer()


@router.get(
    "",
    response_model=List[SystemicIncident],
    summary="Get active systemic incidents",
    description="Returns a list of all currently detected active systemic incidents.",
)
def get_incidents() -> List[SystemicIncident]:
    """Returns active incidents discovered deterministically from data."""
    return get_active_incidents()


@router.get(
    "/transaction/{transaction_id}",
    response_model=IncidentAssociation,
    summary="Check transaction incident association",
    description=(
        "Determines if a transaction is associated with any active systemic incident. "
        "Returns { is_systemic: bool, incident: SystemicIncident | null }. "
        "Returns 200 with is_systemic: false for non-associated or unknown IDs."
    ),
)
def get_transaction_incident(transaction_id: str) -> IncidentAssociation:
    """
    Checks if transaction_id is associated with any detected systemic incident.
    Always returns HTTP 200 with IncidentAssociation payload.
    Does not perform transaction existence validation (authoritatively handled by /api/investigate).
    """
    tid = str(transaction_id).strip()
    return check_transaction_association(tid)


@router.get(
    "/transaction/{transaction_id}/history",
    response_model=HistoricalPatternResult,
    summary="Check transaction historical pattern recurrence",
    description=(
        "Analyzes whether the transaction's systemic pattern signature has recurred across distinct calendar dates. "
        "Returns HistoricalPatternResult with has_historical_pattern=True if observed on >= 2 distinct dates."
    ),
)
def get_transaction_historical_pattern(transaction_id: str) -> HistoricalPatternResult:
    """
    Evaluates historical recurrence for the operational signature of a transaction.
    Always returns HTTP 200 with HistoricalPatternResult payload.
    """
    tid = str(transaction_id).strip()
    return _historical_analyzer.analyze_transaction(tid)

