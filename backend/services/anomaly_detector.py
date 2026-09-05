"""
Deterministic Anomaly Detector Service
Detects anomalies such as bank settlement delays, amount mismatches,
missing records, duplicate transactions, and timestamp chronological inconsistencies.
No AI or heuristics used; purely rule-based and deterministic.
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from backend.models.schemas import AnomalyItem


def detect_anomalies(
    transaction_id: str,
    gateway_records: List[Dict[str, Any]],
    bank_record: Optional[Dict[str, Any]],
    ledger_record: Optional[Dict[str, Any]],
) -> List[AnomalyItem]:
    anomalies: List[AnomalyItem] = []

    # 1. Nonexistent transaction in all systems
    if not gateway_records and bank_record is None and ledger_record is None:
        anomalies.append(
            AnomalyItem(
                anomaly_type="TRANSACTION_NOT_FOUND",
                severity="LOW",
                description=f"Transaction {transaction_id} was not found in Gateway, Bank, or Ledger datasets.",
                details={"transaction_id": transaction_id},
            )
        )
        return anomalies

    primary_gw = gateway_records[0] if gateway_records else None

    # 2. Duplicate Gateway records
    if len(gateway_records) > 1:
        refs = [r.get("gateway_reference") for r in gateway_records if r.get("gateway_reference")]
        anomalies.append(
            AnomalyItem(
                anomaly_type="DUPLICATE_GATEWAY_RECORD",
                severity="CRITICAL",
                description=f"Duplicate capture submissions detected: {len(gateway_records)} Gateway records found for {transaction_id}.",
                details={"count": len(gateway_records), "references": refs},
            )
        )

    # 3. Missing Bank record
    if primary_gw and bank_record is None:
        anomalies.append(
            AnomalyItem(
                anomaly_type="MISSING_BANK_RECORD",
                severity="HIGH",
                description=f"Gateway record exists (status: {primary_gw.get('gateway_status')}), but no corresponding Bank settlement record was found.",
                details={"gateway_reference": primary_gw.get("gateway_reference")},
            )
        )

    # 4. Missing Ledger record
    if (primary_gw or bank_record) and ledger_record is None:
        anomalies.append(
            AnomalyItem(
                anomaly_type="MISSING_LEDGER_RECORD",
                severity="HIGH",
                description="Transaction exists in upstream systems, but matching internal Ledger accounting record is missing.",
                details={
                    "gateway_status": primary_gw.get("gateway_status") if primary_gw else None,
                    "bank_status": bank_record.get("bank_status") if bank_record else None,
                },
            )
        )

    # 5. Amount Mismatches
    amounts = {}
    if primary_gw and primary_gw.get("amount") is not None:
        amounts["Gateway"] = float(primary_gw["amount"])
    if bank_record and bank_record.get("amount") is not None:
        amounts["Bank"] = float(bank_record["amount"])
    if ledger_record and ledger_record.get("amount") is not None:
        amounts["Ledger"] = float(ledger_record["amount"])

    # Compare Gateway vs Bank
    if "Gateway" in amounts and "Bank" in amounts:
        diff_gb = abs(amounts["Gateway"] - amounts["Bank"])
        if diff_gb > 0.009:
            anomalies.append(
                AnomalyItem(
                    anomaly_type="AMOUNT_MISMATCH",
                    severity="HIGH",
                    description=f"Amount mismatch: Gateway amount ₹{amounts['Gateway']:,.2f} differs from Bank amount ₹{amounts['Bank']:,.2f} by ₹{diff_gb:,.2f}.",
                    details={
                        "gateway_amount": amounts["Gateway"],
                        "bank_amount": amounts["Bank"],
                        "difference": round(diff_gb, 2),
                    },
                )
            )

    # Compare Bank vs Ledger
    if "Bank" in amounts and "Ledger" in amounts:
        diff_bl = abs(amounts["Bank"] - amounts["Ledger"])
        if diff_bl > 0.009 and not any(a.anomaly_type == "AMOUNT_MISMATCH" for a in anomalies):
            anomalies.append(
                AnomalyItem(
                    anomaly_type="AMOUNT_MISMATCH",
                    severity="HIGH",
                    description=f"Amount mismatch: Bank amount ₹{amounts['Bank']:,.2f} differs from Ledger amount ₹{amounts['Ledger']:,.2f} by ₹{diff_bl:,.2f}.",
                    details={
                        "bank_amount": amounts["Bank"],
                        "ledger_amount": amounts["Ledger"],
                        "difference": round(diff_bl, 2),
                    },
                )
            )

    # 6. Timestamp Inconsistencies & Sequencing
    if primary_gw and bank_record:
        gw_init = primary_gw.get("initiated_at")
        bnk_settled = bank_record.get("settled_at")
        bnk_recv = bank_record.get("received_at")

        if gw_init and bnk_settled:
            try:
                dt_gw_init = pd.to_datetime(gw_init)
                dt_bnk_settled = pd.to_datetime(bnk_settled)
                if dt_bnk_settled < dt_gw_init:
                    anomalies.append(
                        AnomalyItem(
                            anomaly_type="TIMESTAMP_INCONSISTENCY",
                            severity="HIGH",
                            description=f"Chronological sequence violation: Bank settlement ({bnk_settled}) occurred before Gateway initiation ({gw_init}).",
                            details={
                                "gateway_initiated_at": gw_init,
                                "bank_settled_at": bnk_settled,
                            },
                        )
                    )
            except Exception:
                pass

        if gw_init and bnk_recv:
            try:
                dt_gw_init = pd.to_datetime(gw_init)
                dt_bnk_recv = pd.to_datetime(bnk_recv)
                if dt_bnk_recv < dt_gw_init and not any(
                    a.anomaly_type == "TIMESTAMP_INCONSISTENCY" for a in anomalies
                ):
                    anomalies.append(
                        AnomalyItem(
                            anomaly_type="TIMESTAMP_INCONSISTENCY",
                            severity="HIGH",
                            description=f"Chronological sequence violation: Bank received ({bnk_recv}) before Gateway initiation ({gw_init}).",
                            details={
                                "gateway_initiated_at": gw_init,
                                "bank_received_at": bnk_recv,
                            },
                        )
                    )
            except Exception:
                pass

    # 7. Bank Settlement Delay
    # A settlement is considered delayed when settled_at - expected_settlement_at > 15 minutes.
    # Severity: >60 minutes = HIGH, >15 minutes and <=60 minutes = MEDIUM.
    if bank_record and bank_record.get("expected_settlement_at") and bank_record.get("settled_at"):
        try:
            exp_dt = pd.to_datetime(bank_record["expected_settlement_at"])
            act_dt = pd.to_datetime(bank_record["settled_at"])
            delay_sec = (act_dt - exp_dt).total_seconds()

            # Suppress delay detection when a timestamp chronological error is already detected
            has_timestamp_err = any(a.anomaly_type == "TIMESTAMP_INCONSISTENCY" for a in anomalies)
            if delay_sec > 900 and not has_timestamp_err:  # 900 seconds = 15 minutes
                delay_min = round(delay_sec / 60.0, 1)
                anomalies.append(
                    AnomalyItem(
                        anomaly_type="BANK_DELAY",
                        severity="HIGH" if delay_min > 60 else "MEDIUM",
                        description=f"Settlement was delayed by {delay_min} minutes past the expected SLA time ({bank_record['expected_settlement_at']}).",
                        details={
                            "delay_minutes": delay_min,
                            "expected_settlement_at": bank_record["expected_settlement_at"],
                            "actual_settled_at": bank_record["settled_at"],
                            "bank_name": bank_record.get("bank_name"),
                            "response_code": bank_record.get("response_code"),
                        },
                    )
                )
        except Exception:
            pass

    # 8. Status Conflicts
    if primary_gw and bank_record:
        gw_st = primary_gw.get("gateway_status")
        bnk_st = bank_record.get("bank_status")
        if gw_st == "FAILED" and bnk_st == "SETTLED":
            anomalies.append(
                AnomalyItem(
                    anomaly_type="STATUS_CONFLICT",
                    severity="CRITICAL",
                    description=f"Status conflict: Gateway marked transaction as FAILED, but Bank marked settlement as SETTLED.",
                    details={"gateway_status": gw_st, "bank_status": bnk_st},
                )
            )

    return anomalies
