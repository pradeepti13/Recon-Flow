"""
Pydantic schemas for Settlement Intelligence / Recon Flow.
Defines data structures for transaction investigation results, timeline events,
anomalies, delays, and confidence scoring.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp of the event")
    event: str = Field(..., description="Machine-readable event name (e.g. PAYMENT_CAPTURED)")
    source: str = Field(..., description="Originating system: GATEWAY, BANK, or LEDGER")
    description: str = Field(..., description="Human-readable event description")


class AnomalyItem(BaseModel):
    anomaly_type: str = Field(..., description="Machine-readable anomaly code (e.g. BANK_DELAY)")
    severity: str = Field(..., description="Severity level: LOW, MEDIUM, HIGH, CRITICAL")
    description: str = Field(..., description="Detailed description of the anomaly")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured anomaly parameters")


class DelaysInfo(BaseModel):
    bank_delay_minutes: Optional[float] = Field(
        None, description="Settlement delay past expected time in minutes"
    )
    gateway_capture_delay_seconds: Optional[float] = Field(
        None, description="Delay between initiation and capture in seconds"
    )
    settlement_initiation_delay_seconds: Optional[float] = Field(
        None, description="Delay between capture and settlement initiation in seconds"
    )
    is_delayed: bool = Field(False, description="True if bank settlement exceeded expected SLA")
    delay_reason: Optional[str] = Field(None, description="Description of delay if applicable")


class ConfidenceInfo(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Evidence confidence score (0-100)")
    level: str = Field(..., description="VERY_HIGH, HIGH, MEDIUM, or LOW")
    breakdown: Dict[str, int] = Field(
        default_factory=dict, description="Points attributed per evidence factor"
    )
    factors: List[str] = Field(
        default_factory=list, description="List of positive/negative confidence factors"
    )


class InvestigationResult(BaseModel):
    transaction_id: str = Field(..., description="Investigated transaction ID")
    status: str = Field(
        ...,
        description="Overall status: SUCCESS, DELAYED, MISMATCH, MISSING_DATA, DUPLICATE, INCONSISTENT, FAILED, UNKNOWN",
    )
    summary: str = Field(..., description="Deterministic factual summary of the investigation")
    gateway: Optional[Dict[str, Any]] = Field(None, description="Primary Gateway record")
    gateway_records: List[Dict[str, Any]] = Field(
        default_factory=list, description="All matching Gateway records (for duplicate inspection)"
    )
    bank: Optional[Dict[str, Any]] = Field(None, description="Bank settlement record")
    ledger: Optional[Dict[str, Any]] = Field(None, description="Internal ledger accounting record")
    timeline: List[TimelineEvent] = Field(
        default_factory=list, description="Chronological timeline of events across systems"
    )
    anomalies: List[AnomalyItem] = Field(
        default_factory=list, description="Deterministic anomalies identified"
    )
    evidence: List[str] = Field(
        default_factory=list, description="Factual evidence statements derived from data"
    )
    exceptions: List[str] = Field(
        default_factory=list, description="Exceptions, discrepancies, or missing data alerts"
    )
    delays: DelaysInfo = Field(
        default_factory=DelaysInfo, description="Detailed delay calculations"
    )
    confidence: ConfidenceInfo = Field(
        ..., description="Deterministic confidence calculation and score"
    )


class SystemicIncident(BaseModel):
    incident_id: str = Field(..., description="Deterministic incident ID, e.g. INC-HDF-20260904-01")
    title: str = Field(..., description="Descriptive title of the incident")
    severity: str = Field(..., description="CRITICAL, HIGH, or MEDIUM")
    status: str = Field("ACTIVE", description="Incident state")
    bank: str = Field(..., description="Affected bank name")
    gateway: str = Field(..., description="Affected gateway name")
    dominant_error: str = Field(..., description="Dominant response code or reason")
    start_time: str = Field(..., description="Incident start timestamp (ISO 8601)")
    end_time: str = Field(..., description="Incident end timestamp (ISO 8601)")
    affected_transaction_count: int = Field(..., description="Number of unique transactions in incident")
    affected_amount: float = Field(..., description="Total settlement amount affected")
    common_delay_range_minutes: List[float] = Field(..., description="[min_delay, max_delay]")
    detection_reasons: List[str] = Field(..., description="Factual evidence reasons")
    affected_transactions: List[str] = Field(default_factory=list, description="Internal list of affected IDs")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score")


class IncidentAssociation(BaseModel):
    is_systemic: bool = Field(False, description="True if transaction is part of a systemic incident")
    incident: Optional[SystemicIncident] = Field(None, description="The associated incident object, if any")


# ---------------------------------------------------------------------------
# Phase 8 — Historical Pattern Intelligence schemas
# ---------------------------------------------------------------------------


class HistoricalOccurrence(BaseModel):
    """Details of a single past or current occurrence of a systemic pattern."""

    incident_id: str = Field(..., description="Incident ID of the occurrence")
    date: str = Field(..., description="Calendar date (YYYY-MM-DD)")
    start_time: str = Field(..., description="Incident start timestamp (ISO 8601)")
    end_time: str = Field(..., description="Incident end timestamp (ISO 8601)")
    affected_transaction_count: int = Field(..., description="Number of affected transactions")
    affected_amount: float = Field(..., description="Total settlement amount affected")
    delay_range_minutes: List[float] = Field(..., description="[min_delay, max_delay]")
    severity: str = Field(..., description="Severity level of the occurrence")


class HistoricalPatternResult(BaseModel):
    """Structured deterministic historical pattern analysis result."""

    has_historical_pattern: bool = Field(
        False, description="True if signature occurred on >= 2 distinct calendar dates"
    )
    pattern_signature: Dict[str, str] = Field(
        default_factory=dict, description="Signature keys: bank, gateway, error_code"
    )
    occurrence_count: int = Field(
        0, description="Total distinct calendar dates signature was observed"
    )
    distinct_dates: List[str] = Field(
        default_factory=list, description="List of calendar dates (YYYY-MM-DD)"
    )
    previous_occurrences: List[HistoricalOccurrence] = Field(
        default_factory=list, description="Historical occurrences prior to current date"
    )
    current_occurrence: Optional[HistoricalOccurrence] = Field(
        None, description="Details of the current incident occurrence"
    )
    previous_max_affected_transactions: int = Field(
        0, description="Max affected txns among previous occurrences"
    )
    previous_max_affected_amount: float = Field(
        0.0, description="Max affected amount among previous occurrences"
    )
    current_vs_previous_ratio: Optional[float] = Field(
        None, description="Current transaction count divided by previous max count (if previous max > 0)"
    )
    comparison_summary: str = Field(
        "", description="Factual plain-English comparative statement derived purely from data"
    )


# ---------------------------------------------------------------------------
# Phase 7 — LLM Explanation Layer schemas
# ---------------------------------------------------------------------------


class ExplanationOutput(BaseModel):
    """
    Structured output produced by the AI explanation service.
    When is_fallback is True, all fields are filled from deterministic data —
    no LLM was involved.
    """

    summary: str = Field(
        ..., description="1-2 sentence factual summary of the settlement outcome"
    )
    root_cause: str = Field(
        ..., description="Identified root cause of the settlement issue (or confirmation of success)"
    )
    recommended_action: str = Field(
        ..., description="Recommended action for the support agent"
    )
    customer_facing_explanation: str = Field(
        ..., description="Plain-English explanation suitable for the merchant or customer"
    )
    uncertainty: str = Field(
        ..., description="Honest statement of any uncertainty or gaps in the available evidence"
    )
    is_fallback: bool = Field(
        False,
        description="True when the LLM was not used and deterministic fallback was returned instead",
    )
    fallback_reason: Optional[str] = Field(
        None, description="Why the fallback was used (e.g. 'API key not configured')"
    )


class ExplainRequest(BaseModel):
    """
    Request body for POST /api/explain.
    Accepts the already-computed deterministic investigation result, optional
    systemic incident, and optional historical pattern result.
    The endpoint never re-investigates the transaction.
    """

    investigation: InvestigationResult = Field(
        ..., description="Completed deterministic investigation result"
    )
    incident: Optional[SystemicIncident] = Field(
        None, description="Associated systemic incident, if any (may be null)"
    )
    historical_pattern: Optional[HistoricalPatternResult] = Field(
        None, description="Associated historical pattern result, if any (may be null)"
    )


class ExplainResponse(BaseModel):
    """Envelope returned by POST /api/explain."""

    ok: bool = Field(True, description="Always True; LLM failure is expressed via is_fallback")
    explanation: ExplanationOutput


# ---------------------------------------------------------------------------
# Transaction Index / Explorer schemas
# ---------------------------------------------------------------------------


class TransactionIndexItem(BaseModel):
    transaction_id: str = Field(..., description="Transaction ID")
    status: str = Field(..., description="SUCCESS, DELAYED, MISMATCH, MISSING_DATA, DUPLICATE, INCONSISTENT")
    anomaly_type: Optional[str] = Field(None, description="Primary anomaly type, e.g. BANK_TIMEOUT")
    is_systemic: bool = Field(False, description="True if associated with a systemic incident")
    merchant_id: Optional[str] = Field(None, description="Merchant ID")
    amount: Optional[float] = Field(None, description="Transaction amount")
    initiated_at: Optional[str] = Field(None, description="Initiation timestamp ISO string")


class TransactionIndexResponse(BaseModel):
    transactions: List[TransactionIndexItem] = Field(default_factory=list)
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)
    total: int = Field(..., description="Total matching query")
    total_normal: int = Field(..., description="Total normal transactions in dataset")
    total_anomalies: int = Field(..., description="Total anomalous transactions in dataset")
    total_systemic: int = Field(..., description="Total systemic incident transactions in dataset")


