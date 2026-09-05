import json
import hashlib
from pathlib import Path
import pandas as pd
from data.generate_data import generate_dataset, save_datasets, validate_dataset
from backend.services.investigator import investigate
from backend.services.systemic_analyzer import SystemicAnalyzer

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def test_files_exist():
    assert (DATA_DIR / "gateway.csv").exists()
    assert (DATA_DIR / "bank.csv").exists()
    assert (DATA_DIR / "ledger.csv").exists()
    assert (DATA_DIR / "demo_cases.json").exists()

def test_exact_12155_unique_ids_and_range():
    """Verify master population has exactly 12,155 unique IDs from TXN00001 to TXN12155."""
    gw_df = pd.read_csv(DATA_DIR / "gateway.csv")
    unique_ids = sorted(gw_df["transaction_id"].unique())
    expected_ids = [f"TXN{i:05d}" for i in range(1, 12156)]

    assert len(unique_ids) == 12155, f"Expected 12,155 unique IDs, got {len(unique_ids)}"
    assert unique_ids[0] == "TXN00001", f"Min ID should be TXN00001, got {unique_ids[0]}"
    assert unique_ids[-1] == "TXN12155", f"Max ID should be TXN12155, got {unique_ids[-1]}"
    assert unique_ids == expected_ids, "Master transaction IDs must be TXN00001..TXN12155 without gaps or extras"
    assert "TXN09135" in unique_ids, "TXN09135 must exist in master transaction universe"

def test_nine_dates_distribution_and_mixed_traffic():
    """Verify 9 dates, daily volume sum to 12,155, and mixed traffic across days."""
    gw_df = pd.read_csv(DATA_DIR / "gateway.csv")
    daily = gw_df.groupby(gw_df["initiated_at"].str.slice(0, 10))["transaction_id"].nunique()

    assert len(daily) == 9, f"Expected 9 calendar dates, got {len(daily)}"
    assert list(daily.index) == [
        "2026-08-27", "2026-08-28", "2026-08-29", "2026-08-30",
        "2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04"
    ]
    assert daily.sum() == 12155, f"Daily counts must sum to 12,155, got {daily.sum()}"

    # Verify every day contains a mix of banks and gateways
    for d, sub_df in gw_df.groupby(gw_df["initiated_at"].str.slice(0, 10)):
        assert sub_df["merchant_id"].nunique() > 1, f"Day {d} should have multiple merchants"
        assert sub_df["payment_method"].nunique() > 1, f"Day {d} should have multiple payment methods"

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

def test_demo_semantics_preserved():
    """Verify all 7 demo transaction IDs preserve their required deterministic investigation status."""
    res_normal = investigate("TXN10001")
    assert res_normal.status == "SUCCESS"

    res_delayed = investigate("TXN10087")
    assert res_delayed.status == "DELAYED"

    res_mismatch = investigate("TXN10142")
    assert res_mismatch.status == "MISMATCH"

    res_missing_bank = investigate("TXN10211")
    assert res_missing_bank.status == "MISSING_DATA"
    assert res_missing_bank.bank is None and res_missing_bank.ledger is not None

    res_missing_ledger = investigate("TXN10304")
    assert res_missing_ledger.status == "MISSING_DATA"
    assert res_missing_ledger.bank is not None and res_missing_ledger.ledger is None

    res_dup = investigate("TXN10482")
    assert res_dup.status == "DUPLICATE"
    assert len(res_dup.gateway_records) == 2

    res_ts = investigate("TXN10531")
    assert res_ts.status == "INCONSISTENT"

    res_09135 = investigate("TXN09135")
    assert res_09135.transaction_id == "TXN09135"
    assert res_09135.status in ("SUCCESS", "DELAYED", "MISMATCH", "MISSING_DATA", "DUPLICATE", "INCONSISTENT")

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
