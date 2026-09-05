"""
Deterministic Confidence Scoring
Computes an evidence-based confidence score (0-100) for a transaction investigation.

Scoring rules (no AI or randomness):
  +35  -- Gateway record present
  +30  -- Bank record present
  +25  -- Ledger record present
  +10  -- All three amounts match

Penalties per anomaly type:
  BANK_DELAY               -> -10 (MEDIUM severity), -20 (HIGH severity)
  AMOUNT_MISMATCH          -> -30
  MISSING_BANK_RECORD      -> -25
  MISSING_LEDGER_RECORD    -> -20
  DUPLICATE_GATEWAY_RECORD -> -15
  TIMESTAMP_INCONSISTENCY  -> -25
  STATUS_CONFLICT          -> -25
  TRANSACTION_NOT_FOUND    -> -90  (net score will be 0)

Score is clamped to [0, 100].
Level:
  90-100 -> VERY_HIGH
  75-89  -> HIGH
  50-74  -> MEDIUM
  0-49   -> LOW
"""

from typing import Any, Dict, List, Optional
from backend.models.schemas import AnomalyItem, ConfidenceInfo


# Base points awarded for evidence presence
_BASE_GATEWAY = 35
_BASE_BANK = 30
_BASE_LEDGER = 25
_AMOUNT_CONSISTENCY_BONUS = 10

# Per-anomaly-type penalties (type -> penalty)
_ANOMALY_PENALTIES: Dict[str, int] = {
    "TRANSACTION_NOT_FOUND": 90,
    "AMOUNT_MISMATCH": 30,
    "MISSING_BANK_RECORD": 25,
    "TIMESTAMP_INCONSISTENCY": 25,
    "STATUS_CONFLICT": 25,
    "MISSING_LEDGER_RECORD": 20,
    "BANK_DELAY_HIGH": 20,
    "DUPLICATE_GATEWAY_RECORD": 15,
    "BANK_DELAY_MEDIUM": 10,
}


def _get_level(score: int) -> str:
    if score >= 90:
        return "VERY_HIGH"
    if score >= 75:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"


def calculate_confidence(
    gateway_records: List[Dict[str, Any]],
    bank_record: Optional[Dict[str, Any]],
    ledger_record: Optional[Dict[str, Any]],
    anomalies: List[AnomalyItem],
) -> ConfidenceInfo:
    """
    Calculates a deterministic confidence score from 0 to 100.

    Args:
        gateway_records: All gateway records for the transaction.
        bank_record: The primary bank record (or None).
        ledger_record: The primary ledger record (or None).
        anomalies: List of detected AnomalyItem objects.

    Returns:
        A ConfidenceInfo model with score, level, breakdown, and factors.
    """
    breakdown: Dict[str, int] = {}
    factors: List[str] = []
    score = 0

    # --- Positive evidence points ---
    if gateway_records:
        breakdown["gateway_present"] = _BASE_GATEWAY
        score += _BASE_GATEWAY
        factors.append("Gateway record found")
    else:
        factors.append("Gateway record missing")

    if bank_record is not None:
        breakdown["bank_present"] = _BASE_BANK
        score += _BASE_BANK
        factors.append("Bank settlement record found")
    else:
        factors.append("Bank settlement record missing")

    if ledger_record is not None:
        breakdown["ledger_present"] = _BASE_LEDGER
        score += _BASE_LEDGER
        factors.append("Ledger accounting record found")
    else:
        factors.append("Ledger accounting record missing")

    # Amount consistency bonus (all three present and matching)
    if gateway_records and bank_record is not None and ledger_record is not None:
        try:
            primary_gw = gateway_records[0]
            gw_amt = round(float(primary_gw.get("amount", 0)), 2)
            bk_amt = round(float(bank_record.get("amount", -1)), 2)
            ld_amt = round(float(ledger_record.get("amount", -1)), 2)
            if gw_amt == bk_amt == ld_amt:
                breakdown["amounts_consistent"] = _AMOUNT_CONSISTENCY_BONUS
                score += _AMOUNT_CONSISTENCY_BONUS
                factors.append("All amounts are consistent across all three systems")
        except (TypeError, ValueError):
            pass

    # --- Anomaly penalties ---
    for anomaly in anomalies:
        atype = anomaly.anomaly_type
        severity = anomaly.severity

        if atype == "BANK_DELAY":
            key = f"BANK_DELAY_{severity}"
            penalty = _ANOMALY_PENALTIES.get(key, _ANOMALY_PENALTIES["BANK_DELAY_MEDIUM"])
            breakdown[f"penalty_{atype}"] = -penalty
            score -= penalty
            factors.append(f"Settlement delay detected (-{penalty} pts)")

        elif atype in _ANOMALY_PENALTIES:
            penalty = _ANOMALY_PENALTIES[atype]
            breakdown[f"penalty_{atype}"] = -penalty
            score -= penalty
            factors.append(f"{atype.replace('_', ' ').title()} detected (-{penalty} pts)")

    # Clamp to [0, 100]
    score = max(0, min(100, score))
    level = _get_level(score)

    return ConfidenceInfo(
        score=score,
        level=level,
        breakdown=breakdown,
        factors=factors,
    )
