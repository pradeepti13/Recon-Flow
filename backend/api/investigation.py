"""
Phase 4 - FastAPI Investigation Router
Exposes the deterministic investigation engine through a REST API.
No LLM, no systemic analysis, no authentication — pure deterministic results.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.models.schemas import InvestigationResult
from backend.services.investigator import investigate


router = APIRouter(prefix="/api", tags=["investigation"])


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------

class InvestigateRequest(BaseModel):
    """Request body for the investigation endpoint."""

    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Transaction ID to investigate (e.g. TXN10087).",
        examples=["TXN10087"],
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class InvestigateResponse(BaseModel):
    """
    Wraps InvestigationResult in a stable API envelope.
    Adds a top-level 'ok' flag for easy frontend branching.
    """

    ok: bool = Field(True, description="True when the investigation completed without error.")
    result: InvestigationResult


class ErrorResponse(BaseModel):
    """Returned when the request cannot be fulfilled."""

    ok: bool = Field(False)
    error: str
    detail: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/investigate",
    response_model=InvestigateResponse,
    summary="Investigate a transaction",
    description=(
        "Accepts a transaction_id and returns a deterministic investigation result "
        "including gateway, bank, and ledger evidence, a chronological timeline, "
        "detected anomalies, and a confidence score. "
        "No LLM or AI logic is involved."
    ),
    responses={
        200: {"description": "Investigation completed successfully."},
        400: {"model": ErrorResponse, "description": "Malformed or empty transaction ID."},
        404: {"model": ErrorResponse, "description": "Transaction not found in any system."},
        422: {"description": "Request body validation error (Pydantic)."},
    },
)
def post_investigate(body: InvestigateRequest) -> InvestigateResponse:
    """
    Investigate a single transaction by ID.

    Returns a structured result with:
    - status: SUCCESS | DELAYED | MISMATCH | MISSING_DATA | DUPLICATE | INCONSISTENT
    - gateway, bank, ledger records
    - chronological timeline
    - detected anomalies (deterministic, rule-based)
    - confidence score (0-100)
    - evidence and exception lists

    Returns HTTP 404 if the transaction ID does not exist in Gateway, Bank, or Ledger.
    """
    tid = body.transaction_id.strip()
    if not tid:
        raise HTTPException(status_code=400, detail="transaction_id must not be blank.")

    result = investigate(tid)

    if result.status == "UNKNOWN":
        raise HTTPException(
            status_code=404,
            detail=f"Transaction not found: '{tid}' does not exist in Gateway, Bank, or Ledger.",
        )

    return InvestigateResponse(ok=True, result=result)


@router.get(
    "/investigate/{transaction_id}",
    response_model=InvestigateResponse,
    summary="Investigate a transaction (GET convenience)",
    description=(
        "GET variant of the investigation endpoint for easy browser / curl testing. "
        "Behaviour is identical to POST /api/investigate."
    ),
    responses={
        200: {"description": "Investigation completed successfully."},
        400: {"model": ErrorResponse, "description": "Blank or invalid transaction_id path segment."},
        404: {"model": ErrorResponse, "description": "Transaction not found in any system."},
    },
)
def get_investigate(transaction_id: str) -> InvestigateResponse:
    """GET variant — same logic as POST, accepts transaction_id in the URL path.

    Returns HTTP 404 if the transaction ID does not exist in Gateway, Bank, or Ledger.
    """
    tid = transaction_id.strip()
    if not tid:
        raise HTTPException(status_code=400, detail="transaction_id path segment must not be blank.")

    result = investigate(tid)

    if result.status == "UNKNOWN":
        raise HTTPException(
            status_code=404,
            detail=f"Transaction not found: '{tid}' does not exist in Gateway, Bank, or Ledger.",
        )

    return InvestigateResponse(ok=True, result=result)
