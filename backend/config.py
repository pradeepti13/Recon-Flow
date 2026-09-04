import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from project root
load_dotenv(BASE_DIR / ".env")

# Server settings
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# LLM settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Data paths (relative to project root)
DATA_DIR = BASE_DIR / "data"
GATEWAY_DATA_PATH = BASE_DIR / os.getenv("GATEWAY_DATA_PATH", "data/gateway.csv")
BANK_DATA_PATH = BASE_DIR / os.getenv("BANK_DATA_PATH", "data/bank.csv")
LEDGER_DATA_PATH = BASE_DIR / os.getenv("LEDGER_DATA_PATH", "data/ledger.csv")
DEMO_CASES_PATH = BASE_DIR / os.getenv("DEMO_CASES_PATH", "data/demo_cases.json")
