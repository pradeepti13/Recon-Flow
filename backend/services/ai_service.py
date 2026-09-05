"""
Phase 7 - AI Explanation Service
Provides LLM-generated plain-English explanations of deterministic investigation results.

Architecture rules:
  - The LLM is NOT the source of truth.
  - The LLM receives only structured, pre-verified context derived from InvestigationResult.
  - It never accesses CSV files, never recalculates delays, never determines anomalies.
  - If the LLM is unavailable for any reason, a deterministic fallback is always returned.
  - HTTP 200 is always returned by the caller; is_fallback signals the degraded state.
"""

import json
import logging
from typing import Any, Dict, Optional

from backend.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_PROVIDER,
)
from backend.models.schemas import (
    ExplanationOutput,
    HistoricalPatternResult,
    InvestigationResult,
    SystemicIncident,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TIMEOUT_SECONDS = 10

_SYSTEM_PROMPT = """\
You are a fintech settlement support explanation assistant for an operations platform.

Your task is to transform the provided verified settlement investigation evidence into a clear, professional, and factual explanation suitable for a support or operations specialist.

STRICT OPERATIONAL & SAFETY RULES — violation of any rule invalidates your response:
1. Grounding: Rely EXCLUSIVELY on the verified fields in the supplied JSON context. Never invent or extrapolate:
   - Transaction IDs or merchant references
   - Currency or amounts (gateway, bank, ledger, or incident)
   - Timestamps, dates, or chronological durations
   - Bank names or gateway names
   - Settlement delays (quote only the exact delay_minutes provided)
   - Response codes, error codes, or systemic incident metrics
   - Historical dates or comparative ratios (use only those provided in historical_pattern)
2. Record Integrity:
   - If gateway_present, bank_present, or ledger_present is false, you must explicitly state that the corresponding record is missing. Never imply that an unrecorded action occurred.
   - Never claim settlement succeeded unless the verified status is SUCCESS or bank_status is SETTLED.
3. Status Fidelity: Never contradict the deterministic "status" field in the context.
4. Confidence Preservation: Never invent, adjust, or calculate a confidence score.
5. Historical Recurrence: If historical_pattern is present and has_historical_pattern is true, you may reference verified historical recurrence facts (such as the distinct dates or volume ratio). Never invent non-existent dates or false ratios.
6. Incomplete Evidence: If records are missing or evidence is incomplete, state clearly:
   "The available records do not establish the exact cause."
7. Conflicting Evidence: If the status is INCONSISTENT or records contradict each other, state clearly:
   "The records contain conflicting evidence, so the exact cause cannot be confirmed."
8. Tone & Style: Be concise, objective, and professional. One to three sentences per field.
9. Privacy: Do NOT expose internal reasoning or chain-of-thought.
10. Format: Return strictly VALID JSON matching the required schema. No markdown formatting, code blocks, or extra text.

OUTPUT SCHEMA (respond with exactly this JSON structure, nothing else):
{
  "summary": "<1-2 sentence factual summary of what occurred in the settlement trail>",
  "root_cause": "<the specific operational cause identified from verified evidence, or 'Settlement completed successfully' for SUCCESS>",
  "recommended_action": "<practical operational next step for the support team or merchant communication>",
  "customer_facing_explanation": "<concise, professional plain-English explanation suitable for communicating with the merchant>",
  "uncertainty": "<honest statement of any evidence gaps or 'All key facts are confirmed' if evidence is complete>"
}
"""


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def _build_context(
    investigation: InvestigationResult,
    incident: Optional[SystemicIncident],
    historical_pattern: Optional[HistoricalPatternResult] = None,
) -> Dict[str, Any]:
    """
    Constructs a flat, serialisable context dict from verified deterministic data.
    Only fields that actually exist in the schemas are included.
    The LLM sees this dict — nothing else.
    """
    ctx: Dict[str, Any] = {
        "transaction_id": investigation.transaction_id,
        "status": investigation.status,
        "deterministic_summary": investigation.summary,
        # Delay information
        "delay_minutes": investigation.delays.bank_delay_minutes,
        "is_delayed": investigation.delays.is_delayed,
        "delay_reason": investigation.delays.delay_reason,
        # Anomalies
        "anomaly_types": [a.anomaly_type for a in investigation.anomalies],
        "anomaly_descriptions": [a.description for a in investigation.anomalies],
        # Evidence and exceptions (already human-readable factual strings)
        "evidence": investigation.evidence,
        "exceptions": investigation.exceptions,
        # Gateway
        "gateway_present": investigation.gateway is not None,
        "gateway_status": investigation.gateway.get("gateway_status") if investigation.gateway else None,
        "gateway_amount": investigation.gateway.get("amount") if investigation.gateway else None,
        "gateway_currency": investigation.gateway.get("currency") if investigation.gateway else None,
        "gateway_reference": investigation.gateway.get("gateway_reference") if investigation.gateway else None,
        "gateway_response_code": investigation.gateway.get("response_code") if investigation.gateway else None,
        # Bank
        "bank_present": investigation.bank is not None,
        "bank_name": investigation.bank.get("bank_name") if investigation.bank else None,
        "bank_status": investigation.bank.get("bank_status") if investigation.bank else None,
        "bank_amount": investigation.bank.get("amount") if investigation.bank else None,
        "bank_response_code": investigation.bank.get("response_code") if investigation.bank else None,
        "bank_expected_settlement_at": investigation.bank.get("expected_settlement_at") if investigation.bank else None,
        "bank_settled_at": investigation.bank.get("settled_at") if investigation.bank else None,
        # Ledger
        "ledger_present": investigation.ledger is not None,
        "ledger_status": investigation.ledger.get("ledger_status") if investigation.ledger else None,
        "ledger_amount": investigation.ledger.get("amount") if investigation.ledger else None,
        "ledger_reconciliation_status": investigation.ledger.get("reconciliation_status") if investigation.ledger else None,
        # Confidence (deterministic — LLM must not alter these values)
        "confidence_score": investigation.confidence.score,
        "confidence_level": investigation.confidence.level,
    }

    # Systemic incident (only when associated)
    if incident is not None:
        ctx["systemic_incident"] = {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "bank": incident.bank,
            "gateway": incident.gateway,
            "dominant_error": incident.dominant_error,
            "severity": incident.severity,
            "affected_transaction_count": incident.affected_transaction_count,
            "affected_amount": incident.affected_amount,
            "delay_range_minutes": incident.common_delay_range_minutes,
            "start_time": incident.start_time,
            "end_time": incident.end_time,
        }
    else:
        ctx["systemic_incident"] = None

    # Historical pattern (only when available & recurring)
    if historical_pattern is not None and historical_pattern.has_historical_pattern:
        ctx["historical_pattern"] = {
            "has_historical_pattern": True,
            "occurrence_count": historical_pattern.occurrence_count,
            "distinct_dates": historical_pattern.distinct_dates,
            "previous_max_affected_transactions": historical_pattern.previous_max_affected_transactions,
            "current_vs_previous_ratio": historical_pattern.current_vs_previous_ratio,
            "comparison_summary": historical_pattern.comparison_summary,
        }
    else:
        ctx["historical_pattern"] = None

    return ctx


# ---------------------------------------------------------------------------
# Fallback builder
# ---------------------------------------------------------------------------

def _build_fallback(
    investigation: InvestigationResult,
    reason: str,
) -> ExplanationOutput:
    """
    Constructs a deterministic ExplanationOutput from the InvestigationResult.
    Used whenever the LLM is unavailable or returns invalid output.
    No invented information — only what the deterministic engine already provided.
    """
    tid = investigation.transaction_id
    status = investigation.status
    summary = investigation.summary

    # Root cause from anomalies
    if investigation.anomalies:
        root_cause = "; ".join(a.description for a in investigation.anomalies[:2])
    elif status == "SUCCESS":
        root_cause = "Settlement completed successfully across all three systems."
    else:
        root_cause = f"Deterministic status: {status}. Review the evidence panel for details."

    # Recommended action
    if status == "SUCCESS":
        recommended_action = (
            "Settlement confirmed. Inform the merchant that their payment settled successfully."
        )
    elif status == "DELAYED":
        delay = investigation.delays.bank_delay_minutes
        delay_str = f" ({delay:.1f} minutes)" if delay is not None else ""
        recommended_action = (
            f"Inform the merchant that settlement was completed late{delay_str}. "
            "Review the timeline and evidence panels for details."
        )
    elif status == "MISSING_DATA":
        recommended_action = (
            "One or more settlement records are missing. Escalate for manual investigation "
            "to locate the missing record in the affected system."
        )
    elif status == "MISMATCH":
        recommended_action = (
            "An amount discrepancy was detected across systems. Escalate for manual "
            "reconciliation before informing the merchant."
        )
    elif status in ("DUPLICATE", "INCONSISTENT"):
        recommended_action = (
            "A data integrity issue was detected. Do not confirm settlement to the merchant. "
            "Escalate for manual investigation."
        )
    else:
        recommended_action = (
            "Review the deterministic evidence panel for transaction details "
            "before communicating with the merchant."
        )

    # Customer-facing explanation
    if status == "SUCCESS":
        customer_facing = (
            f"Your payment ({tid}) was successfully processed and settled. "
            "All systems confirm the transaction."
        )
    elif status == "DELAYED":
        customer_facing = (
            f"Your payment ({tid}) was captured successfully, but settlement experienced a delay. "
            "The settlement has since been processed. We apologise for any inconvenience."
        )
    elif status == "MISSING_DATA":
        customer_facing = (
            f"Your payment ({tid}) was received, but we are unable to confirm the complete "
            "settlement status at this time. Our team is investigating."
        )
    else:
        customer_facing = (
            f"Your payment ({tid}) is under investigation. "
            "Our support team will provide an update shortly."
        )

    uncertainty = (
        "AI explanation unavailable. "
        "The deterministic investigation evidence is shown above and reflects the factual record."
    )

    return ExplanationOutput(
        summary=summary,
        root_cause=root_cause,
        recommended_action=recommended_action,
        customer_facing_explanation=customer_facing,
        uncertainty=uncertainty,
        is_fallback=True,
        fallback_reason=reason,
    )


# ---------------------------------------------------------------------------
# LLM callers
# ---------------------------------------------------------------------------

def _call_gemini(context: Dict[str, Any]) -> str:
    """Calls Gemini and returns the raw text response."""
    from google import genai  # type: ignore[import]
    from google.genai import types as genai_types  # type: ignore[import]

    client = genai.Client(api_key=GEMINI_API_KEY)
    user_message = (
        "Here is the structured settlement investigation context. "
        "Produce the explanation JSON:\n\n"
        + json.dumps(context, indent=2, default=str)
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_message,
        config=genai_types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    return response.text


def _call_groq(context: Dict[str, Any]) -> str:
    """Calls Groq and returns the raw text response."""
    from groq import Groq  # type: ignore[import]

    client = Groq(api_key=GROQ_API_KEY)
    user_message = (
        "Here is the structured settlement investigation context. "
        "Produce the explanation JSON:\n\n"
        + json.dumps(context, indent=2, default=str)
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        timeout=_TIMEOUT_SECONDS,
    )
    return response.choices[0].message.content or ""


def _parse_and_validate(raw_text: str) -> ExplanationOutput:
    """
    Parses the raw LLM response string into a validated ExplanationOutput.
    Raises ValueError or ValidationError on any parse/schema failure.
    """
    # Strip markdown code fences if present (defensive)
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    data = json.loads(text)  # raises json.JSONDecodeError if not valid JSON

    # Validate against schema — raises pydantic.ValidationError if invalid
    return ExplanationOutput(
        summary=data["summary"],
        root_cause=data["root_cause"],
        recommended_action=data["recommended_action"],
        customer_facing_explanation=data["customer_facing_explanation"],
        uncertainty=data["uncertainty"],
        is_fallback=False,
        fallback_reason=None,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_explanation(
    investigation: InvestigationResult,
    incident: Optional[SystemicIncident] = None,
    historical_pattern: Optional[HistoricalPatternResult] = None,
) -> ExplanationOutput:
    """
    Generates a structured plain-English explanation of the investigation result.

    The LLM receives only a structured context dict built from the already-computed
    InvestigationResult. It never accesses CSV files or performs independent analysis.

    Returns ExplanationOutput with is_fallback=False when the LLM succeeds.
    Returns a deterministic ExplanationOutput with is_fallback=True in all failure cases.
    Always returns — never raises.
    """
    # --- Guard: no API key → immediate fallback, no network call ---
    provider = (LLM_PROVIDER or "gemini").lower()
    if provider == "gemini" and not GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not configured — using deterministic fallback.")
        return _build_fallback(investigation, "API key not configured.")
    if provider == "groq" and not GROQ_API_KEY:
        logger.info("GROQ_API_KEY not configured — using deterministic fallback.")
        return _build_fallback(investigation, "API key not configured.")

    # --- Build structured context (no CSV access) ---
    context = _build_context(investigation, incident, historical_pattern)

    # --- Call LLM ---
    try:
        if provider == "groq":
            raw = _call_groq(context)
        else:
            raw = _call_gemini(context)

        result = _parse_and_validate(raw)
        logger.info(
            "LLM explanation generated for %s via %s.",
            investigation.transaction_id,
            provider,
        )
        return result

    except json.JSONDecodeError as exc:
        reason = f"LLM returned non-JSON output: {exc}"
        logger.warning("Explanation fallback (%s): %s", investigation.transaction_id, reason)
        return _build_fallback(investigation, reason)

    except Exception as exc:  # noqa: BLE001 — intentional broad catch for fallback
        reason = f"LLM unavailable or returned invalid output: {type(exc).__name__}: {exc}"
        logger.warning("Explanation fallback (%s): %s", investigation.transaction_id, reason)
        return _build_fallback(investigation, reason)

