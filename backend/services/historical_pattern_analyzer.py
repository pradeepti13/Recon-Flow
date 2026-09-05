"""
Phase 8 - Historical Pattern Analyzer Service
Analyzes all systemic incidents discovered across the complete 9-day dataset to detect
recurring operational signatures (bank + gateway + error code) on distinct calendar dates.

Architecture rules:
  - 100% deterministic logic. No ML, no RAG, no vector database.
  - Pattern recurrence requires the same signature to occur on >= 2 distinct calendar dates.
  - Computes historical comparisons (e.g. current incident volume/count vs previous occurrences).
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from pydantic import BaseModel, Field

from backend.models.schemas import (
    HistoricalOccurrence,
    HistoricalPatternResult,
    SystemicIncident,
)
from backend.services.systemic_analyzer import SystemicAnalyzer


class HistoricalPatternAnalyzer:
    """
    Evaluates systemic incidents across the historical dataset to discover recurring operational signatures.
    """

    def __init__(self, systemic_analyzer: Optional[SystemicAnalyzer] = None):
        self.systemic_analyzer = systemic_analyzer or SystemicAnalyzer()

    def analyze_incident(
        self,
        current_incident: SystemicIncident,
        all_incidents: Optional[List[SystemicIncident]] = None,
    ) -> HistoricalPatternResult:
        """
        Analyzes whether the operational signature (bank, gateway, dominant_error) of
        current_incident has appeared on distinct previous calendar dates in the dataset.
        """
        if all_incidents is None:
            all_incidents = self.systemic_analyzer.detect_incidents()

        sig_bank = current_incident.bank
        sig_gateway = current_incident.gateway
        sig_error = current_incident.dominant_error
        curr_date = current_incident.start_time[:10]

        # Match all incidents sharing the exact signature
        matching_incidents = [
            inc for inc in all_incidents
            if inc.bank == sig_bank and inc.gateway == sig_gateway and inc.dominant_error == sig_error
        ]

        # Group by distinct calendar date to prevent intra-day multiple clusters from inflating count
        date_groups: Dict[str, SystemicIncident] = {}
        for inc in matching_incidents:
            d_str = inc.start_time[:10]
            # If multiple clusters exist on same date, pick the larger one for the date summary
            if d_str not in date_groups or inc.affected_transaction_count > date_groups[d_str].affected_transaction_count:
                date_groups[d_str] = inc

        distinct_dates = sorted(list(date_groups.keys()))
        occurrence_count = len(distinct_dates)

        pattern_signature = {
            "bank": sig_bank,
            "gateway": sig_gateway,
            "error_code": sig_error,
        }

        # A pattern is classified as recurring ONLY if it appears on >= 2 distinct calendar dates
        if occurrence_count < 2:
            return HistoricalPatternResult(
                has_historical_pattern=False,
                pattern_signature=pattern_signature,
                occurrence_count=occurrence_count,
                distinct_dates=distinct_dates,
                previous_occurrences=[],
                current_occurrence=self._to_occurrence(current_incident),
                previous_max_affected_transactions=0,
                previous_max_affected_amount=0.0,
                current_vs_previous_ratio=None,
                comparison_summary=f"No previous occurrences of signature {sig_bank}·{sig_gateway}·{sig_error} observed in dataset.",
            )

        # Separate previous calendar dates from current date
        prev_dates = [d for d in distinct_dates if d < curr_date]
        prev_occurrences = [
            self._to_occurrence(date_groups[d]) for d in prev_dates
        ]

        curr_occ = self._to_occurrence(current_incident)

        prev_max_txns = max([occ.affected_transaction_count for occ in prev_occurrences], default=0)
        prev_max_amt = max([occ.affected_amount for occ in prev_occurrences], default=0.0)

        ratio = None
        if prev_max_txns > 0:
            ratio = round(current_incident.affected_transaction_count / prev_max_txns, 1)

        # Construct factual summary string
        if prev_occurrences:
            if ratio and ratio > 1.0:
                comp_summary = (
                    f"Signature observed on {len(prev_dates)} previous date(s) ({', '.join(prev_dates)}). "
                    f"Current occurrence ({current_incident.affected_transaction_count} txns) is {ratio:.1f}x larger "
                    f"than the largest previous occurrence ({prev_max_txns} txns)."
                )
            else:
                comp_summary = (
                    f"Signature observed on {len(prev_dates)} previous date(s) ({', '.join(prev_dates)}). "
                    f"Current impact ({current_incident.affected_transaction_count} txns) is within historical norms."
                )
        else:
            comp_summary = f"Signature observed on {occurrence_count} distinct dates in available dataset."

        return HistoricalPatternResult(
            has_historical_pattern=True,
            pattern_signature=pattern_signature,
            occurrence_count=occurrence_count,
            distinct_dates=distinct_dates,
            previous_occurrences=prev_occurrences,
            current_occurrence=curr_occ,
            previous_max_affected_transactions=prev_max_txns,
            previous_max_affected_amount=prev_max_amt,
            current_vs_previous_ratio=ratio,
            comparison_summary=comp_summary,
        )

    def analyze_transaction(
        self,
        transaction_id: str,
        all_incidents: Optional[List[SystemicIncident]] = None,
    ) -> HistoricalPatternResult:
        """
        Analyzes historical pattern for a given transaction by checking if it is associated with a systemic incident.
        """
        if all_incidents is None:
            all_incidents = self.systemic_analyzer.detect_incidents()

        assoc = self.systemic_analyzer.check_transaction_association(transaction_id, all_incidents)
        if not assoc.is_systemic or not assoc.incident:
            return HistoricalPatternResult(
                has_historical_pattern=False,
                comparison_summary="Transaction is not associated with a systemic incident."
            )

        return self.analyze_incident(assoc.incident, all_incidents)

    @staticmethod
    def _to_occurrence(inc: SystemicIncident) -> HistoricalOccurrence:
        return HistoricalOccurrence(
            incident_id=inc.incident_id,
            date=inc.start_time[:10],
            start_time=inc.start_time,
            end_time=inc.end_time,
            affected_transaction_count=inc.affected_transaction_count,
            affected_amount=inc.affected_amount,
            delay_range_minutes=inc.common_delay_range_minutes,
            severity=inc.severity,
        )
