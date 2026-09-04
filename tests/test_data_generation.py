import json
import hashlib
from pathlib import Path
import pandas as pd
from data.generate_data import generate_dataset, save_datasets, validate_dataset

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def test_files_exist():
    assert (DATA_DIR / "gateway.csv").exists()
    assert (DATA_DIR / "bank.csv").exists()
    assert (DATA_DIR / "ledger.csv").exists()
    assert (DATA_DIR / "demo_cases.json").exists()

def test_schemas():
    df_gw = pd.read_csv(DATA_DIR / "gateway.csv")
    df_bnk = pd.read_csv(DATA_DIR / "bank.csv")
    df_led = pd.read_csv(DATA_DIR / "ledger.csv")

    expected_gw_cols = [
        "transaction_id", "gateway_reference", "merchant_id", "amount",
        "currency", "payment_method", "gateway_status", "initiated_at",
        "captured_at", "settlement_initiated_at", "response_code", "response_message"
    ]
    expected_bnk_cols = [
        "transaction_id", "bank_reference", "bank_name", "amount",
        "bank_status", "received_at", "expected_settlement_at", "settled_at",
        "response_code", "response_message"
    ]
    expected_led_cols = [
        "transaction_id", "ledger_entry_id", "amount", "ledger_status",
        "created_at", "settlement_date", "reconciliation_status"
    ]

    assert list(df_gw.columns) == expected_gw_cols
    assert list(df_bnk.columns) == expected_bnk_cols
    assert list(df_led.columns) == expected_led_cols

def test_dataset_validation_suite():
    validate_dataset(DATA_DIR)

def test_bank_reference_invariant():
    df_bnk = pd.read_csv(DATA_DIR / "bank.csv")
    for _, row in df_bnk.iterrows():
        expected_ref = f"BNK_{row['bank_name'][:3]}_{row['transaction_id']}"
        assert row["bank_reference"] == expected_ref, (
            f"Bank reference invariant violated for {row['transaction_id']}: "
            f"expected {expected_ref}, got {row['bank_reference']}"
        )

def test_reproducibility():
    def get_file_hashes():
        hashes = {}
        for fname in ["gateway.csv", "bank.csv", "ledger.csv", "demo_cases.json"]:
            content = (DATA_DIR / fname).read_bytes()
            hashes[fname] = hashlib.sha256(content).hexdigest()
        return hashes

    initial_hashes = get_file_hashes()
    
    # Re-run generator
    df_gw, df_bnk, df_led, demo, _ = generate_dataset()
    save_datasets(df_gw, df_bnk, df_led, demo, DATA_DIR)
    
    second_hashes = get_file_hashes()
    assert initial_hashes == second_hashes, "Datasets are not byte-for-byte reproducible"
