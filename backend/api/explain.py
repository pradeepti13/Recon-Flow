"""
Phase 7 - FastAPI Explanation Router
Exposes POST /api/explain — the LLM explanation endpoint.

Design contract:
  - Always returns HTTP 200.
  - LLM failure is communicated via ExplanationOutput.is_fallback = True.
  - The endpoint receives a pre-computed InvestigationResult and optional incident.
  - It NEVER re-investigates a transaction or accesses CSV data itself.
  - Deterministic investigation (/api/investigate) is unchanged and unaffected.
"""

from fastapi import APIRouter
from backend.models.schemas import ExplainRequest, ExplainResponse, ExplanationOutput
from backend.services.ai_service import generate_explanation

router = APIRouter(prefix="/api", tags=["explanation"])


@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="Generate AI explanation for an investigation result",
    description=(
        "Accepts a pre-computed deterministic InvestigationResult (and optional systemic incident) "
        "and returns an LLM-generated plain-English support explanation. "
        "Always returns HTTP 200 — if the LLM is unavailable, a deterministic fallback "
        "explanation is returned with is_fallback=True. "
        "This endpoint does NOT re-investigate the transaction or access CSV data."
    ),
    responses={
        200: {
            "description": (
                "Explanation generated (is_fallback=false) or deterministic fallback returned "
                "(is_fallback=true). Always HTTP 200."
            )
        },
        422: {"description": "Request body validation error (Pydantic)."},
    },
)
def post_explain(body: ExplainRequest) -> ExplainResponse:
    """
    Generate a plain-English AI explanation for a completed investigation.

    The LLM is given only a structured context derived from the supplied
    InvestigationResult and optional SystemicIncident. It never reads CSV files
    and never overrides deterministic results.

    If the LLM fails for any reason (no key, network error, malformed output, timeout),
    a safe deterministic fallback explanation is returned with is_fallback=True.
    The HTTP status code is always 200.
    """
    explanation: ExplanationOutput = generate_explanation(
        investigation=body.investigation,
        incident=body.incident,
        historical_pattern=body.historical_pattern,
    )
    return ExplainResponse(ok=True, explanation=explanation)

