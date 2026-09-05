"""
Settlement Intelligence - Data Loader Service
Provides centralized, validated, and cached loading of Gateway, Bank, and Ledger CSV datasets.
Preserves data types (strings for IDs) and leaves anomalies intact for downstream analysis.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import pandas as pd
import numpy as np

from backend.config import (
    BASE_DIR,
    GATEWAY_DATA_PATH,
    BANK_DATA_PATH,
    LEDGER_DATA_PATH,
    DEMO_CASES_PATH,
)

# Schema definitions
GATEWAY_REQUIRED_COLUMNS = [
    "transaction_id",
    "gateway_reference",
    "merchant_id",
    "amount",
    "currency",
    "payment_method",
    "gateway_status",
    "initiated_at",
    "captured_at",
    "settlement_initiated_at",
    "response_code",
    "response_message",
]

BANK_REQUIRED_COLUMNS = [
    "transaction_id",
    "bank_reference",
    "bank_name",
    "amount",
    "bank_status",
    "received_at",
    "expected_settlement_at",
    "settled_at",
    "response_code",
    "response_message",
]

LEDGER_REQUIRED_COLUMNS = [
    "transaction_id",
    "ledger_entry_id",
    "amount",
    "ledger_status",
    "created_at",
    "settlement_date",
    "reconciliation_status",
]

# Explicit dtypes to prevent transaction IDs or references from ever being parsed as integers/floats
GATEWAY_DTYPES = {
    "transaction_id": str,
    "gateway_reference": str,
    "merchant_id": str,
    "currency": str,
    "payment_method": str,
    "gateway_status": str,
    "response_code": str,
    "response_message": str,
}

BANK_DTYPES = {
    "transaction_id": str,
    "bank_reference": str,
    "bank_name": str,
    "bank_status": str,
    "response_code": str,
    "response_message": str,
}

LEDGER_DTYPES = {
    "transaction_id": str,
    "ledger_entry_id": str,
    "ledger_status": str,
    "settlement_date": str,
    "reconciliation_status": str,
}


def _clean_record(d: Dict[str, Any]) -> Dict[str, Any]:
    """Replaces NaN/NaT values with None for clean serialization and inspection."""
    cleaned = {}
    for k, v in d.items():
        if pd.isna(v):
            cleaned[k] = None
        else:
            cleaned[k] = v
    return cleaned


class DataLoader:
    """
    Centralized data access layer for settlement records.
    Caches DataFrames in memory to avoid repeated disk reads.
    """

    def __init__(
        self,
        gateway_path: Optional[Path] = None,
        bank_path: Optional[Path] = None,
        ledger_path: Optional[Path] = None,
        demo_cases_path: Optional[Path] = None,
    ):
        self.gateway_path = Path(gateway_path or GATEWAY_DATA_PATH).resolve()
        self.bank_path = Path(bank_path or BANK_DATA_PATH).resolve()
        self.ledger_path = Path(ledger_path or LEDGER_DATA_PATH).resolve()
        self.demo_cases_path = Path(demo_cases_path or DEMO_CASES_PATH).resolve()

        self._df_gateway: Optional[pd.DataFrame] = None
        self._df_bank: Optional[pd.DataFrame] = None
        self._df_ledger: Optional[pd.DataFrame] = None
        self._demo_cases: Optional[Dict[str, str]] = None

    def _load_csv(
        self,
        file_path: Path,
        required_cols: List[str],
        dtypes: Dict[str, Any],
        dataset_name: str,
    ) -> pd.DataFrame:
        """Validates file existence and schema, then loads into a DataFrame."""
        if not file_path.exists():
            raise FileNotFoundError(
                f"{dataset_name} dataset file not found at: {file_path}"
            )

        df = pd.read_csv(file_path, dtype=dtypes)

        # Validate required columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"{dataset_name} dataset missing required columns: {missing_cols}"
            )

        # Ensure transaction_id is cleanly formatted string without trailing whitespace
        df["transaction_id"] = df["transaction_id"].astype(str).str.strip()

        return df

    def get_gateway_data(self, reload: bool = False) -> pd.DataFrame:
        """Returns the Gateway DataFrame (cached after initial load)."""
        if self._df_gateway is None or reload:
            self._df_gateway = self._load_csv(
                self.gateway_path,
                GATEWAY_REQUIRED_COLUMNS,
                GATEWAY_DTYPES,
                "Gateway",
            )
        return self._df_gateway.copy()

    def get_bank_data(self, reload: bool = False) -> pd.DataFrame:
        """Returns the Bank DataFrame (cached after initial load)."""
        if self._df_bank is None or reload:
            self._df_bank = self._load_csv(
                self.bank_path,
                BANK_REQUIRED_COLUMNS,
                BANK_DTYPES,
                "Bank",
            )
        return self._df_bank.copy()

    def get_ledger_data(self, reload: bool = False) -> pd.DataFrame:
        """Returns the Ledger DataFrame (cached after initial load)."""
        if self._df_ledger is None or reload:
            self._df_ledger = self._load_csv(
                self.ledger_path,
                LEDGER_REQUIRED_COLUMNS,
                LEDGER_DTYPES,
                "Ledger",
            )
        return self._df_ledger.copy()

    def get_all_data(
        self, reload: bool = False
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Loads and returns all three datasets."""
        return (
            self.get_gateway_data(reload=reload),
            self.get_bank_data(reload=reload),
            self.get_ledger_data(reload=reload),
        )

    def get_demo_cases(self, reload: bool = False) -> Dict[str, str]:
        """Loads and returns the demo scenario mapping."""
        if self._demo_cases is None or reload:
            if not self.demo_cases_path.exists():
                raise FileNotFoundError(
                    f"Demo cases file not found at: {self.demo_cases_path}"
                )
            with open(self.demo_cases_path, "r", encoding="utf-8") as f:
                self._demo_cases = json.load(f)
        return dict(self._demo_cases)

    def clear_cache(self) -> None:
        """Clears cached in-memory DataFrames."""
        self._df_gateway = None
        self._df_bank = None
        self._df_ledger = None
        self._demo_cases = None

    # -------------------------------------------------------------
    # Record Lookup Functions
    # -------------------------------------------------------------
    def find_gateway_records(self, transaction_id: str) -> List[Dict[str, Any]]:
        """
        Returns all matching gateway records for a transaction ID as a list of dicts.
        Returns empty list if not found.
        """
        tid = str(transaction_id).strip()
        df = self.get_gateway_data()
        matches = df[df["transaction_id"] == tid]
        if matches.empty:
            return []
        return [_clean_record(r) for r in matches.to_dict(orient="records")]

    def find_gateway_transaction(
        self, transaction_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Returns the primary gateway record as a dict, or None if missing.
        """
        records = self.find_gateway_records(transaction_id)
        return records[0] if records else None

    def find_bank_records(self, transaction_id: str) -> List[Dict[str, Any]]:
        """
        Returns all matching bank records for a transaction ID as a list of dicts.
        Returns empty list if not found.
        """
        tid = str(transaction_id).strip()
        df = self.get_bank_data()
        matches = df[df["transaction_id"] == tid]
        if matches.empty:
            return []
        return [_clean_record(r) for r in matches.to_dict(orient="records")]

    def find_bank_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns the primary bank record as a dict, or None if missing.
        """
        records = self.find_bank_records(transaction_id)
        return records[0] if records else None

    def find_ledger_records(self, transaction_id: str) -> List[Dict[str, Any]]:
        """
        Returns all matching ledger records for a transaction ID as a list of dicts.
        Returns empty list if not found.
        """
        tid = str(transaction_id).strip()
        df = self.get_ledger_data()
        matches = df[df["transaction_id"] == tid]
        if matches.empty:
            return []
        return [_clean_record(r) for r in matches.to_dict(orient="records")]

    def find_ledger_transaction(
        self, transaction_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Returns the primary ledger record as a dict, or None if missing.
        """
        records = self.find_ledger_records(transaction_id)
        return records[0] if records else None


# Module-level default singleton instance
_default_loader = DataLoader()


# Convenient module-level functional interface
def load_gateway_data(reload: bool = False) -> pd.DataFrame:
    return _default_loader.get_gateway_data(reload=reload)


def load_bank_data(reload: bool = False) -> pd.DataFrame:
    return _default_loader.get_bank_data(reload=reload)


def load_ledger_data(reload: bool = False) -> pd.DataFrame:
    return _default_loader.get_ledger_data(reload=reload)


# Aliases as specified in docs/todo.md
load_gateway = load_gateway_data
load_bank = load_bank_data
load_ledger = load_ledger_data


def load_all_data(
    reload: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return _default_loader.get_all_data(reload=reload)


def load_demo_cases(reload: bool = False) -> Dict[str, str]:
    return _default_loader.get_demo_cases(reload=reload)


def find_gateway_records(transaction_id: str) -> List[Dict[str, Any]]:
    return _default_loader.find_gateway_records(transaction_id)


def find_gateway_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    return _default_loader.find_gateway_transaction(transaction_id)


def find_bank_records(transaction_id: str) -> List[Dict[str, Any]]:
    return _default_loader.find_bank_records(transaction_id)


def find_bank_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    return _default_loader.find_bank_transaction(transaction_id)


def find_ledger_records(transaction_id: str) -> List[Dict[str, Any]]:
    return _default_loader.find_ledger_records(transaction_id)


def find_ledger_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    return _default_loader.find_ledger_transaction(transaction_id)


def clear_cache() -> None:
    _default_loader.clear_cache()
