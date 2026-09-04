"""
Settlement Intelligence - Synthetic Data Generator
Generates reproducible synthetic datasets for Gateway, Bank, and Ledger records,
injecting controlled anomalies and systemic incident clusters.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Fixed random seed for complete reproducibility
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

BASE_DATE = datetime(2026, 9, 4)


def format_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def generate_dataset(num_transactions: int = 1000):
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    gateway_records = []
    bank_records = []
    ledger_records = []

    # Transaction IDs: TXN10001 to TXN11000
    txn_ids = [f"TXN{10000 + i}" for i in range(1, num_transactions + 1)]

    # Identify systemic incident cluster transactions:
    # Concentrated on HDFC_BANK + RAZORPAY between 14:00 and 16:00
    # Let's reserve ~125 transactions for the systemic incident cluster (including TXN10087)
    systemic_set = set()
    systemic_set.add("TXN10087")
    
    # We'll pick around 130 additional transactions to be part of the systemic incident
    candidate_incident_ids = [t for t in txn_ids[80:240] if t not in DEMO_CASES.values()]
    chosen_systemic = random.sample(candidate_incident_ids, 129)
    systemic_set.update(chosen_systemic)

    for i, txn_id in enumerate(txn_ids):
        # Default properties
        merchant_id = random.choice(MERCHANTS)
        currency = "INR"
        payment_method = random.choice(PAYMENT_METHODS)
        
        # Base timestamp spread across 09:00 to 18:00
        # For systemic cluster transactions, distribute between 14:00 and 15:55
        if txn_id in systemic_set:
            bank_name = "HDFC_BANK"
            gateway_provider = "RAZORPAY"
            # Random minute between 14:00:00 and 15:50:00
            offset_seconds = random.randint(0, 110 * 60)
            txn_time = BASE_DATE.replace(hour=14, minute=0, second=0) + timedelta(seconds=offset_seconds)
            # Realistic transaction amount for cluster
            amount = round(random.choice([1500.0, 2000.0, 3500.0, 5000.0, 7500.0, 10000.0, 12500.0, 18000.0, 25000.0]), 2)
        else:
            bank_name = random.choice(BANKS)
            gateway_provider = random.choice(GATEWAYS)
            # Outside cluster, distribute across 09:00 to 18:00
            hour = random.randint(9, 17)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            txn_time = BASE_DATE.replace(hour=hour, minute=minute, second=second)
            # Typical merchant amounts
            amount = round(float(random.choice([250, 499, 999, 1200, 1500, 2499, 3500, 4999, 6500, 8900, 12000, 15000])), 2)

        gw_ref = f"GW_{gateway_provider[:3]}_{txn_id}"
        bnk_ref = f"BNK_{bank_name[:3]}_{txn_id}"
        ledg_id = f"LEDG_{txn_id}"

        # -------------------------------------------------------------
        # 1. SPECIAL CASE: TXN10087 (Bank Delay & Systemic Incident Demo)
        # -------------------------------------------------------------
        if txn_id == "TXN10087":
            # Exact timestamps from PRD:
            # Gateway settlement initiated: 14:33
            # Expected bank settlement: 14:45
            # Actual bank settlement: 16:17
            # Ledger posted: 16:18
            init_at = BASE_DATE.replace(hour=14, minute=32, second=0)
            capt_at = BASE_DATE.replace(hour=14, minute=32, second=30)
            settle_init_at = BASE_DATE.replace(hour=14, minute=33, second=0)
            bank_recv_at = BASE_DATE.replace(hour=14, minute=33, second=15)
            exp_settle_at = BASE_DATE.replace(hour=14, minute=45, second=0)
            act_settle_at = BASE_DATE.replace(hour=16, minute=17, second=0)  # 92 min delay!
            ledg_created_at = BASE_DATE.replace(hour=16, minute=18, second=0)
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
                "ledger_entry_id": ledg_id,
                "amount": demo_amt,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": "2026-09-04",
                "reconciliation_status": "MATCHED"
            })
            continue

        # -------------------------------------------------------------
        # 2. SPECIAL CASE: TXN10142 (Amount Mismatch)
        # -------------------------------------------------------------
        if txn_id == "TXN10142":
            init_at = txn_time
            capt_at = init_at + timedelta(seconds=20)
            settle_init_at = capt_at + timedelta(seconds=30)
            bank_recv_at = settle_init_at + timedelta(seconds=15)
            exp_settle_at = bank_recv_at + timedelta(minutes=15)
            act_settle_at = exp_settle_at - timedelta(minutes=2)
            ledg_created_at = act_settle_at + timedelta(minutes=1)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": gw_ref,
                "merchant_id": merchant_id,
                "amount": 5000.00,
                "currency": "INR",
                "payment_method": payment_method,
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            bank_name = "ICICI_BANK"
            bnk_ref = f"BNK_{bank_name[:3]}_{txn_id}"

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": bnk_ref,
                "bank_name": bank_name,
                "amount": 4800.00,  # Mismatch: 4800 vs 5000
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "SETTLED_OK",
                "response_message": "Settlement completed"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": ledg_id,
                "amount": 5000.00,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": "2026-09-04",
                "reconciliation_status": "DISCREPANCY"
            })
            continue

        # -------------------------------------------------------------
        # 3. SPECIAL CASE: TXN10211 (Missing Bank Record)
        # -------------------------------------------------------------
        if txn_id == "TXN10211":
            init_at = txn_time
            capt_at = init_at + timedelta(seconds=25)
            settle_init_at = capt_at + timedelta(seconds=35)
            ledg_created_at = settle_init_at + timedelta(minutes=5)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": gw_ref,
                "merchant_id": merchant_id,
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
            # Deliberately OMIT bank record

            # Retain ledger record (Gateway exists, Bank missing, Ledger exists)
            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": ledg_id,
                "amount": 3200.00,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": "2026-09-04",
                "reconciliation_status": "UNRECONCILED"
            })
            continue

        # -------------------------------------------------------------
        # 4. SPECIAL CASE: TXN10304 (Missing Ledger Record)
        # -------------------------------------------------------------
        if txn_id == "TXN10304":
            init_at = txn_time
            capt_at = init_at + timedelta(seconds=15)
            settle_init_at = capt_at + timedelta(seconds=30)
            bank_recv_at = settle_init_at + timedelta(seconds=15)
            exp_settle_at = bank_recv_at + timedelta(minutes=10)
            act_settle_at = exp_settle_at - timedelta(minutes=2)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": gw_ref,
                "merchant_id": merchant_id,
                "amount": 7500.00,
                "currency": "INR",
                "payment_method": "CARD",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            bank_name = "AXIS_BANK"
            bnk_ref = f"BNK_{bank_name[:3]}_{txn_id}"

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": bnk_ref,
                "bank_name": bank_name,
                "amount": 7500.00,
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "SETTLED_OK",
                "response_message": "Settlement completed"
            })
            # Deliberately OMIT ledger record
            continue

        # -------------------------------------------------------------
        # 5. SPECIAL CASE: TXN10482 (Duplicate Gateway Record)
        # -------------------------------------------------------------
        if txn_id == "TXN10482":
            init_at = txn_time
            capt_at1 = init_at + timedelta(seconds=30)
            capt_at2 = init_at + timedelta(seconds=45)
            settle_init_at = capt_at1 + timedelta(seconds=30)
            bank_recv_at = settle_init_at + timedelta(seconds=15)
            exp_settle_at = bank_recv_at + timedelta(minutes=15)
            act_settle_at = exp_settle_at - timedelta(minutes=1)
            ledg_created_at = act_settle_at + timedelta(minutes=1)

            # Duplicate record 1
            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_DUP_A_{txn_id}",
                "merchant_id": merchant_id,
                "amount": 3500.00,
                "currency": "INR",
                "payment_method": "UPI",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at1),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully (attempt 1)"
            })
            # Duplicate record 2 (Duplicate transaction ID with conflicting reference/timestamp)
            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_DUP_B_{txn_id}",
                "merchant_id": merchant_id,
                "amount": 3500.00,
                "currency": "INR",
                "payment_method": "UPI",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at2),
                "settlement_initiated_at": format_iso(settle_init_at + timedelta(seconds=15)),
                "response_code": "DUPLICATE_SUBMISSION",
                "response_message": "Duplicate capture request detected"
            })

            bank_name = "SBI"
            bnk_ref = f"BNK_{bank_name[:3]}_{txn_id}"

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": bnk_ref,
                "bank_name": bank_name,
                "amount": 3500.00,
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "SETTLED_OK",
                "response_message": "Settlement completed"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": ledg_id,
                "amount": 3500.00,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": "2026-09-04",
                "reconciliation_status": "DISCREPANCY"
            })
            continue

        # -------------------------------------------------------------
        # 6. SPECIAL CASE: TXN10531 (Timestamp Inconsistency)
        # -------------------------------------------------------------
        if txn_id == "TXN10531":
            # Initiated at 15:30, but bank says settled at 13:10 (prior to initiation!)
            init_at = BASE_DATE.replace(hour=15, minute=30, second=0)
            capt_at = BASE_DATE.replace(hour=15, minute=30, second=45)
            settle_init_at = BASE_DATE.replace(hour=15, minute=31, second=15)
            impossible_settled_at = BASE_DATE.replace(hour=13, minute=10, second=0)
            impossible_recv_at = BASE_DATE.replace(hour=13, minute=5, second=0)
            exp_settle_at = BASE_DATE.replace(hour=13, minute=20, second=0)
            ledg_created_at = impossible_settled_at + timedelta(minutes=2)

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": gw_ref,
                "merchant_id": merchant_id,
                "amount": 4200.00,
                "currency": "INR",
                "payment_method": "NETBANKING",
                "gateway_status": "CAPTURED",
                "initiated_at": format_iso(init_at),
                "captured_at": format_iso(capt_at),
                "settlement_initiated_at": format_iso(settle_init_at),
                "response_code": "SUCCESS",
                "response_message": "Transaction captured successfully"
            })

            bank_name = "KOTAK_BANK"
            bnk_ref = f"BNK_{bank_name[:3]}_{txn_id}"

            bank_records.append({
                "transaction_id": txn_id,
                "bank_reference": bnk_ref,
                "bank_name": bank_name,
                "amount": 4200.00,
                "bank_status": "SETTLED",
                "received_at": format_iso(impossible_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(impossible_settled_at),
                "response_code": "SETTLED_OK",
                "response_message": "Settlement completed"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": ledg_id,
                "amount": 4200.00,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": "2026-09-04",
                "reconciliation_status": "DISCREPANCY"
            })
            continue

        # -------------------------------------------------------------
        # 7. SYSTEMIC INCIDENT TRANSACTIONS (Cluster)
        # -------------------------------------------------------------
        if txn_id in systemic_set:
            init_at = txn_time
            capt_at = init_at + timedelta(seconds=random.randint(10, 45))
            settle_init_at = capt_at + timedelta(seconds=random.randint(20, 60))
            bank_recv_at = settle_init_at + timedelta(seconds=random.randint(10, 30))
            # Expected settlement within 15 minutes
            exp_settle_at = bank_recv_at + timedelta(minutes=15)
            
            # Systemic incident: Severe bank processing delay (45 to 110 minutes after expected)
            delay_minutes = random.randint(45, 110)
            act_settle_at = exp_settle_at + timedelta(minutes=delay_minutes)
            ledg_created_at = act_settle_at + timedelta(seconds=random.randint(30, 90))

            gateway_records.append({
                "transaction_id": txn_id,
                "gateway_reference": f"GW_RAZ_{txn_id}",
                "merchant_id": merchant_id,
                "amount": amount,
                "currency": "INR",
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
                "bank_reference": f"BNK_HDF_{txn_id}",
                "bank_name": "HDFC_BANK",
                "amount": amount,
                "bank_status": "SETTLED",
                "received_at": format_iso(bank_recv_at),
                "expected_settlement_at": format_iso(exp_settle_at),
                "settled_at": format_iso(act_settle_at),
                "response_code": "BANK_TIMEOUT",
                "response_message": "Batch settlement delayed by core banking timeout"
            })

            ledger_records.append({
                "transaction_id": txn_id,
                "ledger_entry_id": ledg_id,
                "amount": amount,
                "ledger_status": "POSTED",
                "created_at": format_iso(ledg_created_at),
                "settlement_date": "2026-09-04",
                "reconciliation_status": "MATCHED"
            })
            continue

        # -------------------------------------------------------------
        # 8. STANDARD NORMAL TRANSACTIONS (or rare isolated failures)
        # -------------------------------------------------------------
        init_at = txn_time
        capt_at = init_at + timedelta(seconds=random.randint(10, 45))
        settle_init_at = capt_at + timedelta(seconds=random.randint(20, 60))
        bank_recv_at = settle_init_at + timedelta(seconds=random.randint(10, 30))
        exp_settle_at = bank_recv_at + timedelta(minutes=random.randint(10, 20))
        
        # 98% of standard transactions settle normally on-time (1-4 min before SLA)
        # 2% have an isolated normal delay of 5-10 min
        is_isolated_delay = (random.random() < 0.02)
        if is_isolated_delay:
            act_settle_at = exp_settle_at + timedelta(minutes=random.randint(5, 12))
            resp_code = "SLIGHT_DELAY"
            resp_msg = "Minor settlement delay"
        else:
            act_settle_at = exp_settle_at - timedelta(minutes=random.randint(1, 5))
            resp_code = "SETTLED_OK"
            resp_msg = "Settlement completed successfully"

        ledg_created_at = act_settle_at + timedelta(seconds=random.randint(30, 90))

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
            "response_code": resp_code,
            "response_message": resp_msg
        })

        ledger_records.append({
            "transaction_id": txn_id,
            "ledger_entry_id": ledg_id,
            "amount": amount,
            "ledger_status": "POSTED",
            "created_at": format_iso(ledg_created_at),
            "settlement_date": "2026-09-04",
            "reconciliation_status": "MATCHED"
        })

    # Convert to DataFrames
    df_gateway = pd.DataFrame(gateway_records)
    df_bank = pd.DataFrame(bank_records)
    df_ledger = pd.DataFrame(ledger_records)

    return df_gateway, df_bank, df_ledger, DEMO_CASES, systemic_set


def save_datasets(df_gateway, df_bank, df_ledger, demo_cases, data_dir: Path = DATA_DIR):
    data_dir.mkdir(parents=True, exist_ok=True)
    
    gateway_file = data_dir / "gateway.csv"
    bank_file = data_dir / "bank.csv"
    ledger_file = data_dir / "ledger.csv"
    demo_file = data_dir / "demo_cases.json"

    df_gateway.to_csv(gateway_file, index=False)
    df_bank.to_csv(bank_file, index=False)
    df_ledger.to_csv(ledger_file, index=False)

    with open(demo_file, "w", encoding="utf-8") as f:
        json.dump(demo_cases, f, indent=2)

    print(f"Generated datasets successfully:")
    print(f"  - Gateway records: {len(df_gateway)} -> {gateway_file}")
    print(f"  - Bank records:    {len(df_bank)} -> {bank_file}")
    print(f"  - Ledger records:  {len(df_ledger)} -> {ledger_file}")
    print(f"  - Demo scenarios:  {len(demo_cases)} -> {demo_file}")


def validate_dataset(data_dir: Path = DATA_DIR):
    gateway_file = data_dir / "gateway.csv"
    bank_file = data_dir / "bank.csv"
    ledger_file = data_dir / "ledger.csv"
    demo_file = data_dir / "demo_cases.json"

    assert gateway_file.exists(), f"Missing {gateway_file}"
    assert bank_file.exists(), f"Missing {bank_file}"
    assert ledger_file.exists(), f"Missing {ledger_file}"
    assert demo_file.exists(), f"Missing {demo_file}"

    df_gw = pd.read_csv(gateway_file)
    df_bnk = pd.read_csv(bank_file)
    df_led = pd.read_csv(ledger_file)
    with open(demo_file, "r", encoding="utf-8") as f:
        demo = json.load(f)

    # 1. Total base transactions count:
    unique_txns = set(df_gw["transaction_id"]).union(set(df_bnk["transaction_id"])).union(set(df_led["transaction_id"]))
    assert len(unique_txns) == 1000, f"Expected 1000 unique transactions, found {len(unique_txns)}"

    # 2. Normal case (TXN10001):
    norm_id = demo["normal"]
    gw_norm = df_gw[df_gw["transaction_id"] == norm_id].iloc[0]
    bnk_norm = df_bnk[df_bnk["transaction_id"] == norm_id].iloc[0]
    led_norm = df_led[df_led["transaction_id"] == norm_id].iloc[0]
    assert gw_norm["amount"] == bnk_norm["amount"] == led_norm["amount"], "Normal amounts mismatch"
    assert bnk_norm["settled_at"] <= bnk_norm["expected_settlement_at"], "Normal transaction not settled on time"
    assert led_norm["reconciliation_status"] == "MATCHED"

    # 3. Bank delay case (TXN10087):
    delay_id = demo["bank_delay"]
    gw_delay = df_gw[df_gw["transaction_id"] == delay_id].iloc[0]
    bnk_delay = df_bnk[df_bnk["transaction_id"] == delay_id].iloc[0]
    exp_dt = pd.to_datetime(bnk_delay["expected_settlement_at"])
    act_dt = pd.to_datetime(bnk_delay["settled_at"])
    delay_minutes = (act_dt - exp_dt).total_seconds() / 60
    assert delay_minutes == 92.0, f"Expected delay of 92 minutes for {delay_id}, got {delay_minutes}"

    # 4. Amount mismatch case (TXN10142):
    mismatch_id = demo["amount_mismatch"]
    gw_mismatch = df_gw[df_gw["transaction_id"] == mismatch_id].iloc[0]
    bnk_mismatch = df_bnk[df_bnk["transaction_id"] == mismatch_id].iloc[0]
    assert gw_mismatch["amount"] == 5000.00
    assert bnk_mismatch["amount"] == 4800.00
    assert gw_mismatch["amount"] != bnk_mismatch["amount"]

    # 5. Missing bank case (TXN10211):
    mb_id = demo["missing_bank"]
    assert mb_id in set(df_gw["transaction_id"]), f"{mb_id} should be in gateway"
    assert mb_id not in set(df_bnk["transaction_id"]), f"{mb_id} must NOT be in bank"
    assert mb_id in set(df_led["transaction_id"]), f"{mb_id} should be in ledger"

    # 6. Missing ledger case (TXN10304):
    ml_id = demo["missing_ledger"]
    assert ml_id in set(df_gw["transaction_id"]), f"{ml_id} should be in gateway"
    assert ml_id in set(df_bnk["transaction_id"]), f"{ml_id} should be in bank"
    assert ml_id not in set(df_led["transaction_id"]), f"{ml_id} must NOT be in ledger"

    # 7. Duplicate case (TXN10482):
    dup_id = demo["duplicate"]
    dup_gw_rows = df_gw[df_gw["transaction_id"] == dup_id]
    assert len(dup_gw_rows) == 2, f"Expected 2 duplicate rows in gateway for {dup_id}, got {len(dup_gw_rows)}"

    # 8. Timestamp inconsistency case (TXN10531):
    ts_id = demo["timestamp_error"]
    gw_ts = df_gw[df_gw["transaction_id"] == ts_id].iloc[0]
    bnk_ts = df_bnk[df_bnk["transaction_id"] == ts_id].iloc[0]
    gw_init = pd.to_datetime(gw_ts["initiated_at"])
    bnk_settled = pd.to_datetime(bnk_ts["settled_at"])
    assert bnk_settled < gw_init, f"Expected bank settled ({bnk_settled}) < gateway initiated ({gw_init})"

    # 9. Systemic incident cluster:
    sys_id = demo["systemic_incident"]
    sys_gw = df_gw[(df_gw["gateway_reference"].str.startswith("GW_RAZ")) & 
                   (df_gw["initiated_at"] >= "2026-09-04T14:00:00") & 
                   (df_gw["initiated_at"] <= "2026-09-04T16:00:00")]
    sys_bnk = df_bnk[(df_bnk["bank_name"] == "HDFC_BANK") & 
                     (df_bnk["response_code"] == "BANK_TIMEOUT")]
    # Verify cluster has > 100 transactions and matches TXN10087
    assert len(sys_bnk) >= 120, f"Expected at least 120 systemic bank timeout records, found {len(sys_bnk)}"
    assert sys_id in set(sys_bnk["transaction_id"]), f"{sys_id} must belong to systemic cluster"

    # 10. Demo cases JSON validity:
    for scenario, tid in demo.items():
        assert tid in unique_txns, f"Demo case {scenario} points to non-existent ID {tid}"

    # 11. Bank reference consistency check (invariant: BNK_{bank_name[:3]}_{txn_id}):
    for _, row in df_bnk.iterrows():
        expected_ref = f"BNK_{row['bank_name'][:3]}_{row['transaction_id']}"
        assert row["bank_reference"] == expected_ref, (
            f"Bank reference mismatch for {row['transaction_id']}: "
            f"expected {expected_ref}, got {row['bank_reference']}"
        )

    print("All 11 validation checks PASSED successfully!")


if __name__ == "__main__":
    df_gw, df_bnk, df_led, demo, sys_set = generate_dataset()
    save_datasets(df_gw, df_bnk, df_led, demo)
    validate_dataset()
