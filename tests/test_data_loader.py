import pytest
from pathlib import Path
import pandas as pd
from backend.services.data_loader import (
    DataLoader,
    load_gateway,
    load_bank,
    load_ledger,
    load_all_data,
    load_demo_cases,
    find_gateway_records,
    find_gateway_transaction,
    find_bank_records,
    find_bank_transaction,
    find_ledger_records,
    find_ledger_transaction,
    clear_cache,
    GATEWAY_REQUIRED_COLUMNS,
    BANK_REQUIRED_COLUMNS,
    LEDGER_REQUIRED_COLUMNS,
)


@pytest.fixture(autouse=True)
def reset_loader_cache():
    clear_cache()
    yield
    clear_cache()


def test_load_all_datasets_successfully():
    gw_df, bnk_df, led_df = load_all_data()
    assert isinstance(gw_df, pd.DataFrame)
    assert isinstance(bnk_df, pd.DataFrame)
    assert isinstance(led_df, pd.DataFrame)
    assert len(gw_df) >= 12155
    assert len(bnk_df) >= 12000
    assert len(led_df) >= 12000



def test_required_columns_present():
    gw_df = load_gateway()
    bnk_df = load_bank()
    led_df = load_ledger()

    for col in GATEWAY_REQUIRED_COLUMNS:
        assert col in gw_df.columns, f"Missing gateway column: {col}"

    for col in BANK_REQUIRED_COLUMNS:
        assert col in bnk_df.columns, f"Missing bank column: {col}"

    for col in LEDGER_REQUIRED_COLUMNS:
        assert col in led_df.columns, f"Missing ledger column: {col}"


def test_transaction_ids_are_strings():
    gw_df = load_gateway()
    bnk_df = load_bank()
    led_df = load_ledger()

    assert all(isinstance(tid, str) for tid in gw_df["transaction_id"])
    assert all(isinstance(tid, str) for tid in bnk_df["transaction_id"])
    assert all(isinstance(tid, str) for tid in led_df["transaction_id"])

    # Verify lookups work with string types
    rec = find_gateway_transaction("TXN10001")
    assert rec is not None
    assert isinstance(rec["transaction_id"], str)
    assert rec["transaction_id"] == "TXN10001"


def test_missing_records_remain_missing():
    # TXN10211 has Gateway and Ledger, but is deliberately missing from bank
    gw_rec = find_gateway_transaction("TXN10211")
    bnk_rec = find_bank_transaction("TXN10211")
    led_rec = find_ledger_transaction("TXN10211")

    assert gw_rec is not None
    assert bnk_rec is None
    assert led_rec is not None
    assert led_rec["transaction_id"] == "TXN10211"
    assert find_bank_records("TXN10211") == []

    # TXN10304 is in gateway and bank, but deliberately missing from ledger
    assert find_gateway_transaction("TXN10304") is not None
    assert find_bank_transaction("TXN10304") is not None
    assert find_ledger_transaction("TXN10304") is None
    assert find_ledger_records("TXN10304") == []


def test_duplicate_gateway_record_detectable():
    # TXN10482 contains intentional duplicate records in Gateway
    records = find_gateway_records("TXN10482")
    assert len(records) == 2
    assert records[0]["transaction_id"] == "TXN10482"
    assert records[1]["transaction_id"] == "TXN10482"
    assert records[0]["gateway_reference"] != records[1]["gateway_reference"]

    # find_gateway_transaction returns the first record without crashing
    primary = find_gateway_transaction("TXN10482")
    assert primary is not None
    assert primary["transaction_id"] == "TXN10482"


def test_nonexistent_transaction_lookup():
    assert find_gateway_transaction("TXN_DOES_NOT_EXIST") is None
    assert find_bank_transaction("TXN_DOES_NOT_EXIST") is None
    assert find_ledger_transaction("TXN_DOES_NOT_EXIST") is None
    assert find_gateway_records("TXN_DOES_NOT_EXIST") == []


def test_demo_cases_loading():
    demo = load_demo_cases()
    assert isinstance(demo, dict)
    assert "normal" in demo
    assert "bank_delay" in demo
    assert "amount_mismatch" in demo
    assert demo["normal"] == "TXN10001"
    assert demo["bank_delay"] == "TXN10087"


def test_immutability_and_source_data_protection():
    # Mutating returned DataFrame must not modify the cached or underlying data
    df1 = load_gateway()
    original_val = df1.iloc[0]["amount"]
    df1.iloc[0, df1.columns.get_loc("amount")] = 999999.99

    df2 = load_gateway()
    assert df2.iloc[0]["amount"] == original_val
    assert df2.iloc[0]["amount"] != 999999.99


def test_invalid_missing_file_path_raises_error(tmp_path):
    loader = DataLoader(gateway_path=tmp_path / "nonexistent.csv")
    with pytest.raises(FileNotFoundError) as exc_info:
        loader.get_gateway_data()
    assert "not found" in str(exc_info.value).lower()


def test_missing_required_columns_raises_error(tmp_path):
    bad_csv = tmp_path / "bad_gateway.csv"
    bad_csv.write_text("transaction_id,amount\nTXN1,100\n", encoding="utf-8")

    loader = DataLoader(gateway_path=bad_csv)
    with pytest.raises(ValueError) as exc_info:
        loader.get_gateway_data()
    assert "missing required columns" in str(exc_info.value).lower()
