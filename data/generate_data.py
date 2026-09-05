"""
Phase 8 — Synthetic Settlement Data Generator
Generates exactly 12,155 unique transactions across 9 calendar days (2026-08-27 to 2026-09-04).
Fully deterministic with seed=42.
Preserves all 7 existing demo transactions (TXN10001 to TXN10531) and anomaly rules.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

RANDOM_SEED = 42

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DEMO_CASES = {
    "normal": "TXN10001",
    "bank_delay": "TXN10087",
    "amount_mismatch": "TXN10142",
    "missing_bank": "TXN10211",
    "missing_ledger": "TXN10304",
    "duplicate": "TXN10482",
    "timestamp_error": "TXN10531",
    "systemic_incident": "TXN10087"
}

BANKS = ["HDFC_BANK", "ICICI_BANK", "SBI", "AXIS_BANK", "KOTAK_BANK"]
GATEWAYS = ["RAZORPAY", "PAYU", "CASHFREE", "STRIPE"]
PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING"]
MERCHANTS = [f"MERCH_{i:03d}" for i in range(101, 126)]

# 9 Calendar Days: 2026-08-27 through 2026-09-04
DATES = [
    datetime(2026, 8, 27),
    datetime(2026, 8, 28),
    datetime(2026, 8, 29),
    datetime(2026, 8, 30),
    datetime(2026, 8, 31),
    datetime(2026, 9, 1),
    datetime(2026, 9, 2),
    datetime(2026, 9, 3),
    datetime(2026, 9, 4),
]


def format_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def generate_dataset(num_transactions: int = 12155):
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    gateway_records = []
    bank_records = []
    ledger_records = []

    # Master Transaction Universe: TXN00001 to TXN12155 (exactly 12,155 unique IDs)
    txn_ids = [f"TXN{i:05d}" for i in range(1, num_transactions + 1)]

    # Map dates to transaction ID slices with randomized, unequal daily volumes totaling 12,155
    daily_counts = [1310, 1375, 1420, 1265, 1390, 1415, 1340, 1280, 1360]
    assert sum(daily_counts) == num_transactions

    # Randomly shuffle transaction IDs so they are not assigned chronologically by ID number
    shuffled_ids = txn_ids.copy()
    random.shuffle(shuffled_ids)

    date_txn_map = {}
    current_idx = 0
    for idx, dt in enumerate(DATES):
        cnt = daily_counts[idx]
        date_txn_map[dt.strftime("%Y-%m-%d")] = (dt, shuffled_ids[current_idx : current_idx + cnt])
        current_idx += cnt

    # Ensure demo cases fall into Sep 4 date slot so standard demo workflows work consistently
    sep4_ids = date_txn_map["2026-09-04"][1]
    for d_name, d_id in DEMO_CASES.items():
        if d_id not in txn_ids:
            continue
        if d_id not in sep4_ids:
            for d_str, (dt_obj, t_list) in date_txn_map.items():
                if d_id in t_list:
                    pos_old = t_list.index(d_id)
                    # find non-demo target in sep4 to swap
                    for s_idx, s_id in enumerate(sep4_ids):
                        if s_id not in DEMO_CASES.values():
                            t_list[pos_old] = sep4_ids[s_idx]
                            sep4_ids[s_idx] = d_id
                            break
                    break


    # Define Systemic Incident Configs across the 9 days
    # RECURRING SIGNATURE: HDFC_BANK + RAZORPAY + BANK_TIMEOUT
    # Occurrences:
    # 1. 2026-08-29 (Aug 29): 31 affected txns, 11:00-12:30
    # 2. 2026-09-02 (Sep 2): 24 affected txns, 15:00-16:15
    # 3. 2026-09-04 (Sep 4): 130 affected txns (including TXN10087), 14:00-15:55 (Hero incident)
    # ONE-OFF SIGNATURE 1: SBI + PAYU + BANK_TIMEOUT on 2026-08-28: 22 affected txns, 10:00-11:30
    # ONE-OFF SIGNATURE 2: ICICI_BANK + CASHFREE + SYSTEM_ERROR on 2026-09-01: 18 affected txns, 16:00-17:15

    systemic_assignments = {}  # txn_id -> {bank, gateway, error, delay_min, txn_time}

    # Helper to assign cluster
    def assign_cluster(date_key, count, bank, gateway, error, start_hour, duration_minutes, target_id_override=None):
        dt_obj, ids_in_day = date_txn_map[date_key]
        candidates = [t for t in ids_in_day if t not in DEMO_CASES.values() and t not in systemic_assignments]
        if target_id_override and target_id_override in ids_in_day:
            candidates = [t for t in candidates if t != target_id_override]
            chosen = [target_id_override] + random.sample(candidates, count - 1)
        else:
            chosen = random.sample(candidates, count)

        for c_id in chosen:
            off_sec = random.randint(0, duration_minutes * 60)
            t_time = dt_obj.replace(hour=start_hour, minute=0, second=0) + timedelta(seconds=off_sec)
            d_min = random.uniform(45.0, 110.0)
            systemic_assignments[c_id] = {
                "bank": bank,
                "gateway": gateway,
                "error": error,
                "delay_min": d_min,
                "txn_time": t_time,
            }

    # Assign recurring occurrences
    assign_cluster("2026-08-29", 31, "HDFC_BANK", "RAZORPAY", "BANK_TIMEOUT", 11, 90)
    assign_cluster("2026-09-02", 24, "HDFC_BANK", "RAZORPAY", "BANK_TIMEOUT", 15, 75)
    assign_cluster("2026-09-04", 130, "HDFC_BANK", "RAZORPAY", "BANK_TIMEOUT", 14, 110, target_id_override="TXN10087")

    # Assign one-off occurrences
    assign_cluster("2026-08-28", 22, "SBI", "PAYU", "BANK_TIMEOUT", 10, 90)
    assign_cluster("2026-09-01", 18, "ICICI_BANK", "CASHFREE", "SYSTEM_ERROR", 16, 75)

    # Isolated anomaly assignment across all days (approx 10% of total txns = ~1200 txns)
    # Exclude HDFC_BANK Sep 4 candidates so hero cluster stays exactly 130 txns with Bank records
    all_non_systemic = [t for t in txn_ids if t not in systemic_assignments and t not in DEMO_CASES.values()]
    random.shuffle(all_non_systemic)

    isolated_delays = set(all_non_systemic[:200])
    isolated_mismatches = set(all_non_systemic[200:350])
    isolated_missing_banks = set(all_non_systemic[350:500])
    isolated_missing_ledgers = set(all_non_systemic[500:650])
    isolated_duplicates = set(all_non_systemic[650:750])
    isolated_inconsistencies = set(all_non_systemic[750:850])

    # Reverse lookup for date of each transaction ID
    txn_date_lookup = {}
    for d_str, (dt_obj, t_list) in date_txn_map.items():
        for t_id in t_list:
            txn_date_lookup[t_id] = dt_obj

    # Main Generation Loop for 12,155 transactions
    for txn_id in txn_ids:
        base_dt = txn_date_lookup[txn_id]
        date_str = base_dt.strftime("%Y-%m-%d")

        # -------------------------------------------------------------
        # DEMO CASES OVERRIDES (Sep 4)
        # -------------------------------------------------------------
        if txn_id == "TXN10087":
            init_at = base_dt.replace(hour=14, minute=32, second=0)
            capt_at = base_dt.replace(hour=14, minute=32, second=30)
            settle_init_at = base_dt.replace(hour=14, minute=33, second=0)
            bank_recv_at = base_dt.replace(hour=14, minute=33, second=15)
            exp_settle_at = base_dt.replace(hour=14, minute=45, second=0)
            act_settle_at = base_dt.replace(hour=16, minute=17, second=0)  # 92 min delay
            ledg_created_at = base_dt.replace(hour=16, minute=18, second=0)
            demo_amt = 5000.00

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_RAZ_{txn_id}",
                "merchant_id": "MERCH_101",
                "amount": demo_amt,
                "currency": "INR",
                "payment_method": "UPI",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": f"BNK_HDF_{txn_id}",
                "bank_name": "HDFC_BANK",
                "amount": demo_amt,
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "BANK_TIMEOUT",
                "response_message": "Batch settlement delayed by core banking timeout"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": f"LEDG_{txn_id}",
                "amount": demo_amt,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": date_str,
                "reconciliation_status": "MATCHED"
            })
            continue

        if txn_id == "TXN10142":
            init_at = base_dt.replace(hour=11, minute=15, second=0)
            capt_at = init_at + timedelta(seconds=20)
            settle_init_at = capt_at + timedelta(seconds=30)
            bank_recv_at = settle_init_at + timedelta(seconds=15)
            exp_settle_at = bank_recv_at + timedelta(minutes=15)
            act_settle_at = exp_settle_at - timedelta(minutes=2)
            ledg_created_at = act_settle_at + timedelta(minutes=1)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_ICIC_{txn_id}",
                "merchant_id": "MERCH_102",
                "amount": 5000.00,
                "currency": "INR",
                "payment_method": "CARD",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": f"BNK_ICI_{txn_id}",
                "bank_name": "ICICI_BANK",
                "amount": 4800.00,  # Mismatch
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "SETTLED_OK",
                "response_message": "Settlement completed"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": f"LEDG_{txn_id}",
                "amount": 5000.00,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": date_str,
                "reconciliation_status": "DISCREPANCY"
            })
            continue

        if txn_id == "TXN10211":
            init_at = base_dt.replace(hour=10, minute=10, second=0)
            capt_at = init_at + timedelta(seconds=25)
            settle_init_at = capt_at + timedelta(seconds=35)
            ledg_created_at = settle_init_at + timedelta(minutes=5)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_PAY_{txn_id}",
                "merchant_id": "MERCH_103",
                "amount": 3200.00,
                "currency": "INR",
                "payment_method": "UPI",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": f"LEDG_{txn_id}",
                "amount": 3200.00,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": date_str,
                "reconciliation_status": "UNRECONCILED"
            })
            continue

        if txn_id == "TXN10304":
            init_at = base_dt.replace(hour=12, minute=40, second=0)
            capt_at = init_at + timedelta(seconds=15)
            settle_init_at = capt_at + timedelta(seconds=30)
            bank_recv_at = settle_init_at + timedelta(seconds=20)
            exp_settle_at = bank_recv_at + timedelta(minutes=15)
            act_settle_at = exp_settle_at + timedelta(minutes=2)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_CAS_{txn_id}",
                "merchant_id": "MERCH_104",
                "amount": 7500.00,
                "currency": "INR",
                "payment_method": "NETBANKING",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": f"BNK_SBI_{txn_id}",
                "bank_name": "SBI",
                "amount": 7500.00,
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "SETTLED_OK",
                "response_message": "Settlement completed"
            })
            continue

        if txn_id == "TXN10482":
            init_at = base_dt.replace(hour=15, minute=20, second=0)
            capt_at1 = init_at + timedelta(seconds=10)
            capt_at2 = init_at + timedelta(seconds=12)
            settle_init_at = capt_at1 + timedelta(seconds=40)
            bank_recv_at = settle_init_at + timedelta(seconds=15)
            exp_settle_at = bank_recv_at + timedelta(minutes=15)
            act_settle_at = exp_settle_at + timedelta(minutes=3)
            ledg_created_at = act_settle_at + timedelta(minutes=1)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_STR_{txn_id}_A",
                "merchant_id": "MERCH_105",
                "amount": 12000.00,
                "currency": "INR",
                "payment_method": "CARD",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at1),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_STR_{txn_id}_B",
                "merchant_id": "MERCH_105",
                "amount": 12000.00,
                "currency": "INR",
                "payment_method": "CARD",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at2),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Duplicate capture API callback received"
            })

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": f"BNK_AXI_{txn_id}",
                "bank_name": "AXIS_BANK",
                "amount": 12000.00,
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "SETTLED_OK",
                "response_message": "Single settlement batch processed"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": f"LEDG_{txn_id}",
                "amount": 12000.00,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": date_str,
                "reconciliation_status": "MATCHED"
            })
            continue

        if txn_id == "TXN10531":
            init_at = base_dt.replace(hour=15, minute=30, second=0)
            capt_at = init_at + timedelta(seconds=15)
            settle_init_at = capt_at + timedelta(seconds=20)
            bank_recv_at = settle_init_at + timedelta(seconds=10)
            exp_settle_at = bank_recv_at + timedelta(minutes=15)
            act_settle_at = base_dt.replace(hour=13, minute=10, second=0)
            ledg_created_at = act_settle_at + timedelta(minutes=5)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_RAZ_{txn_id}",
                "merchant_id": "MERCH_106",
                "amount": 8900.00,
                "currency": "INR",
                "payment_method": "UPI",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": f"BNK_KOT_{txn_id}",
                "bank_name": "KOTAK_BANK",
                "amount": 8900.00,
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "SETTLED_OK",
                "response_message": "Settlement date mismatch"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": f"LEDG_{txn_id}",
                "amount": 8900.00,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": date_str,
                "reconciliation_status": "TIMESTAMP_MISMATCH"
            })
            continue

        if txn_id == "TXN10001":
            init_at = base_dt.replace(hour=10, minute=14, second=0)
            capt_at = init_at + timedelta(seconds=12)
            settle_init_at = capt_at + timedelta(seconds=45)
            bank_recv_at = settle_init_at + timedelta(seconds=30)
            exp_settle_at = bank_recv_at + timedelta(minutes=15)
            act_settle_at = exp_settle_at - timedelta(minutes=5)
            ledg_created_at = act_settle_at + timedelta(minutes=1)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_RAZ_{txn_id}",
                "merchant_id": "MERCH_101",
                "amount": 5000.00,
                "currency": "INR",
                "payment_method": "UPI",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": f"BNK_HDF_{txn_id}",
                "bank_name": "HDFC_BANK",
                "amount": 5000.00,
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "SETTLED_OK",
                "response_message": "Settlement completed successfully"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": f"LEDG_{txn_id}",
                "amount": 5000.00,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": date_str,
                "reconciliation_status": "MATCHED"
            })
            continue

        # -------------------------------------------------------------
        # GENERAL TRANSACTIONS (Systemic or Ordinary)
        # -------------------------------------------------------------
        merchant_id = random.choice(MERCHANTS)
        currency = "INR"
        payment_method = random.choice(PAYMENT_METHODS)

        if txn_id in systemic_assignments:
            sys_info = systemic_assignments[txn_id]
            bank_name = sys_info["bank"]
            gateway_provider = sys_info["gateway"]
            err_code = sys_info["error"]
            delay_m = sys_info["delay_min"]
            txn_time = sys_info["txn_time"]
            amount = round(random.choice([1500.0, 2500.0, 3500.0, 5000.0, 7500.0, 10000.0, 15000.0, 22000.0]), 2)

            init_at = txn_time
            capt_at = init_at + timedelta(seconds=random.randint(10, 45))
            settle_init_at = capt_at + timedelta(seconds=random.randint(20, 60))
            bank_recv_at = settle_init_at + timedelta(seconds=random.randint(10, 30))
            exp_settle_at = bank_recv_at + timedelta(minutes=15)
            act_settle_at = exp_settle_at + timedelta(minutes=delay_m)
            ledg_created_at = act_settle_at + timedelta(minutes=1)

            gw_ref = f"GW_{gateway_provider[:3]}_{txn_id}"
            bnk_ref = f"BNK_{bank_name[:3]}_{txn_id}"
            ledg_id = f"LEDG_{txn_id}"

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": gw_ref,
                "merchant_id": merchant_id,
                "amount": amount,
                "currency": currency,
                "payment_method": payment_method,
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": bnk_ref,
                "bank_name": bank_name,
                "amount": amount,
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": err_code,
                "response_message": f"Settlement delayed by {err_code}"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": ledg_id,
                "amount": amount,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": date_str,
                "reconciliation_status": "MATCHED"
            })
            continue

        # Non-systemic Ordinary Transactions (Normal or Isolated Anomaly)
        bank_name = random.choice(BANKS)
        gateway_provider = random.choice(GATEWAYS)
        hour = random.randint(8, 20)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        txn_time = base_dt.replace(hour=hour, minute=minute, second=second)
        amount = round(float(random.choice([250, 499, 999, 1200, 1500, 2499, 3500, 4999, 6500, 8900, 12000, 15000])), 2)

        gw_ref = f"GW_{gateway_provider[:3]}_{txn_id}"
        bnk_ref = f"BNK_{bank_name[:3]}_{txn_id}"
        ledg_id = f"LEDG_{txn_id}"

        init_at = txn_time
        capt_at = init_at + timedelta(seconds=random.randint(10, 45))
        settle_init_at = capt_at + timedelta(seconds=random.randint(20, 60))
        bank_recv_at = settle_init_at + timedelta(seconds=random.randint(10, 30))
        exp_settle_at = bank_recv_at + timedelta(minutes=15)

        # Isolated anomaly logic
        if txn_id in isolated_delays:
            delay_m = random.uniform(20.0, 60.0)
            act_settle_at = exp_settle_at + timedelta(minutes=delay_m)
            ledg_created_at = act_settle_at + timedelta(minutes=1)
            b_status = "SETTLED"
            resp_code = "BANK_TIMEOUT"
        elif txn_id in isolated_inconsistencies:
            act_settle_at = init_at - timedelta(minutes=random.randint(15, 60))
            ledg_created_at = act_settle_at + timedelta(minutes=1)
            b_status = "SETTLED"
            resp_code = "SETTLED_OK"
        else:
            # On-time or early
            act_settle_at = exp_settle_at - timedelta(minutes=random.randint(1, 8))
            ledg_created_at = act_settle_at + timedelta(minutes=1)
            b_status = "SETTLED"
            resp_code = "SETTLED_OK"

        # Gateway record
        gateway_records.append({
            "transaction_id": txn_id,
            "gateway_reference": gw_ref,
            "merchant_id": merchant_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "gateway_status": "CAPTURED",
            "initiated_at": format_iso(init_at),
            "captured_at": format_iso(capt_at),
            "settlement_initiated_at": format_iso(settle_init_at),
            "response_code": "SUCCESS",
            "response_message": "Transaction captured successfully"
        })

        if txn_id in isolated_duplicates:
            # Add second gateway record
            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"{gw_ref}_DUP",
                "merchant_id": merchant_id,
                "amount": amount,
                "currency": currency,
                "payment_method": payment_method,
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at + timedelta(seconds=2)),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Duplicate capture API callback"
            })

        # Bank record
        if txn_id not in isolated_missing_banks:
            b_amt = amount
            if txn_id in isolated_mismatches:
                b_amt = round(amount * 0.9, 2)
            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": bnk_ref,
                "bank_name": bank_name,
                "amount": b_amt,
                "bank_status": b_status,
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": resp_code,
                "response_message": "Bank response"
            })

        # Ledger record
        if txn_id not in isolated_missing_ledgers:
            rec_stat = "MATCHED"
            if txn_id in isolated_mismatches:
                rec_stat = "DISCREPANCY"
            elif txn_id in isolated_inconsistencies:
                rec_stat = "TIMESTAMP_MISMATCH"
            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": ledg_id,
                "amount": amount,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": date_str,
                "reconciliation_status": rec_stat
            })

    # Convert to DataFrames
    gw_df = pd.DataFrame(gateway_records)
    bnk_df = pd.DataFrame(bank_records)
    ledg_df = pd.DataFrame(ledger_records)

    save_datasets(gw_df, bnk_df, ledg_df, DEMO_CASES, DATA_DIR)

    return gw_df, bnk_df, ledg_df, DEMO_CASES, None


def save_datasets(gw_df: pd.DataFrame, bnk_df: pd.DataFrame, ledg_df: pd.DataFrame, demo_cases: dict, output_dir: Path):
    """Saves generated DataFrames and demo cases to CSV/JSON files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    gw_df.to_csv(output_dir / "gateway.csv", index=False)
    bnk_df.to_csv(output_dir / "bank.csv", index=False)
    ledg_df.to_csv(output_dir / "ledger.csv", index=False)

    with open(output_dir / "demo_cases.json", "w") as f:
        json.dump(demo_cases, f, indent=2)


def validate_dataset(data_dir: Path):
    """Validates the synthetic dataset files for existence and schema integrity."""
    data_dir = Path(data_dir)
    for fname in ["gateway.csv", "bank.csv", "ledger.csv", "demo_cases.json"]:
        p = data_dir / fname
        assert p.exists(), f"Missing dataset file: {fname}"

    gw_df = pd.read_csv(data_dir / "gateway.csv")
    bnk_df = pd.read_csv(data_dir / "bank.csv")
    ledg_df = pd.read_csv(data_dir / "ledger.csv")

    assert len(gw_df) >= 12155, "Gateway CSV should contain at least 12,155 rows"
    assert len(bnk_df) > 10000, "Bank CSV should contain > 10,000 rows"
    assert len(ledg_df) > 10000, "Ledger CSV should contain > 10,000 rows"


if __name__ == "__main__":
    gw_df, bnk_df, ledg_df, _, _ = generate_dataset()
    print("Dataset generation complete!")
    print(f"Gateway rows: {len(gw_df)}, unique txns: {gw_df['transaction_id'].nunique()}")
    print(f"Bank rows: {len(bnk_df)}, unique txns: {bnk_df['transaction_id'].nunique()}")
    print(f"Ledger rows: {len(ledg_df)}, unique txns: {ledg_df['transaction_id'].nunique()}")

