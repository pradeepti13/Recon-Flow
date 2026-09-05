# Recon Flow — Settlement Intelligence Platform

>**From reconciliation to investigation. From isolated failures to systemic intelligence.**


>## 🔗 Quick Links & Live Links

- **🐙 GitHub Repository**: [https://github.com/pradeepti13/Recon-Flow](https://github.com/pradeepti13/Recon-Flow)
- **🚀 Live Deployed Application**: [https://recon-flow.onrender.com](https://recon-flow.onrender.com)
- **📖 API Documentation**: [https://recon-flow-backend.onrender.com/docs](https://recon-flow-backend.onrender.com/docs)
Recon Flow is an **autonomous fintech settlement investigation platform** designed to investigate transaction failures across the complete payment settlement chain.

Instead of treating a failed transaction as an isolated record, Recon Flow performs deterministic **three-leg reconciliation** across the **Payment Gateway, Acquiring Bank, and Internal Ledger**, identifies anomalies, detects recurring systemic failures, reconstructs the evidence trail, and uses AI to generate human-readable explanations and operational recommendations.

---

## 🚀 Why Recon Flow?

Modern payment systems involve multiple independent systems that must agree on the same transaction.

A transaction can appear successful at the gateway while being delayed by the bank, recorded with a different amount, or missing from the internal ledger.

Traditional reconciliation tells an operator **that something is wrong**.

Recon Flow goes further:

```text
Transaction
     │
     ▼
Cross-System Reconciliation
     │
     ├── Gateway
     ├── Acquiring Bank
     └── Internal Ledger
     │
     ▼
Anomaly Detection
     │
     ▼
Evidence & Confidence Analysis
     │
     ▼
Systemic Pattern Detection
     │
     ▼
AI-Assisted Explanation
     │
     ▼
Operational Recommendation
```

The result is an investigation workflow rather than a simple transaction lookup.

---

# ✨ Core Capabilities

### 1. Deterministic 3-Leg Reconciliation

Recon Flow independently compares transaction records across:

* **Payment Gateway**
* **Acquiring Bank**
* **Internal Ledger**

The investigation engine verifies:

* Transaction presence
* Amount parity
* Status alignment
* Timestamp chronology
* Settlement completion
* Cross-system consistency

This deterministic layer establishes the **facts before AI is involved**.

---

### 2. Automated Anomaly Detection

The platform identifies multiple classes of settlement anomalies:

| Anomaly                 | Detection                                            |
| ----------------------- | ---------------------------------------------------- |
| Bank SLA Delay          | Settlement exceeds configured SLA                    |
| Amount Mismatch         | Gateway and bank amounts differ                      |
| Missing Bank Record     | Gateway capture has no corresponding bank record     |
| Missing Ledger Record   | Bank settlement has no corresponding ledger entry    |
| Duplicate Capture       | Multiple capture records detected                    |
| Timestamp Inconsistency | Transaction chronology violates expected sequence    |
| Systemic Failure        | Multiple related failures clustered into an incident |

---

### 3. Systemic Incident Detection

Recon Flow does not stop after finding one failed transaction.

It analyzes transaction failures across time windows to identify **system-level degradation**.

For example:

```text
Individual Transactions
       │
       ├── TXN10087 ── Bank Delay
       ├── TXN10091 ── Bank Delay
       ├── TXN10103 ── Bank Delay
       ├── TXN10142 ── Bank Delay
       │
       ▼
Temporal Clustering
       │
       ▼
SYSTEMIC INCIDENT
       │
       ▼
Potential Bank / Gateway Infrastructure Issue
```

This allows operators to distinguish between:

**"This transaction failed."**

and

**"These transactions are failing because the same underlying infrastructure issue is affecting the settlement system."**

---

### 4. Historical Pattern Telemetry

Recon Flow analyzes multi-day transaction data to identify recurring patterns such as:

* Repeated bank delays
* Recurring gateway failures
* Repeated amount discrepancies
* Persistent missing records
* Recurring systemic incidents
* Historical anomaly concentration

This adds temporal context to individual investigations.

---

### 5. Evidence-Based Confidence Scoring

Every investigation is supported by structured evidence.

The confidence layer evaluates the consistency and completeness of the available records before an AI explanation is generated.

```text
Gateway Evidence
       +
Bank Evidence
       +
Ledger Evidence
       +
Chronology
       +
Anomaly Rules
       │
       ▼
Evidence Score
       │
       ▼
Investigation Confidence
```

The AI therefore interprets **verified evidence** rather than independently inventing the underlying transaction facts.

---

### 6. AI Investigation Narratives

Recon Flow uses AI as an interpretation layer.

Supported providers include:

* Google Gemini
* Groq / Llama

The AI receives structured investigation results and produces:

* Root-cause explanations
* Human-readable investigation summaries
* Operational recommendations
* Merchant-facing notification copy

If an external AI provider is unavailable, the platform falls back to a **deterministic explanation path**.

---

# 🧠 Deterministic + AI Architecture

One of the central design principles of Recon Flow is:

> **Deterministic systems establish what happened. AI explains what it means.**

```text
                 ┌──────────────────────┐
                 │   Gateway / Bank /   │
                 │       Ledger         │
                 └──────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Deterministic Engine  │
                │                       │
                │ • Reconciliation      │
                │ • Anomaly Detection   │
                │ • Chronology Checks   │
                │ • Confidence Scoring  │
                │ • Systemic Analysis   │
                └───────────┬───────────┘
                            │
                     Verified Evidence
                            │
                            ▼
                ┌───────────────────────┐
                │      AI Service       │
                │                       │
                │ • Gemini              │
                │ • Groq / Llama        │
                │ • Fallback Narrative  │
                └───────────┬───────────┘
                            │
                            ▼
                Human-Readable Explanation
                            │
                            ▼
                ┌───────────────────────┐
                │    React Dashboard    │
                └───────────────────────┘
```

This separation improves reliability, explainability, and testability.

---

# 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     React 19 + Vite                         │
│                                                             │
│  Search • Investigation Conclusion • Evidence • Timeline    │
│  Cross-System Comparison • Historical Patterns • AI         │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP / JSON
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                         │
│                                                             │
│  REST API Routers                                           │
│       │                                                     │
│       ├── Investigation API                                 │
│       ├── Incidents API                                     │
│       ├── Explain API                                       │
│       └── Transactions API                                  │
│                                                             │
│  Core Services                                              │
│       │                                                     │
│       ├── Data Loader                                       │
│       ├── Investigation Engine                              │
│       ├── Anomaly Detector                                  │
│       ├── Confidence Engine                                 │
│       ├── Systemic Analyzer                                 │
│       ├── Historical Pattern Analyzer                       │
│       └── AI Narrative Service                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Deterministic Data Layer                   │
│                                                             │
│      gateway.csv       bank.csv       ledger.csv            │
│                                                             │
│       12,155 synthetic but internally consistent            │
│                  transaction records                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Investigation Flow

```text
User enters Transaction ID
            │
            ▼
     Investigation API
            │
            ▼
      Data Loader
            │
            ▼
 ┌──────────────────────────┐
 │  Gateway / Bank / Ledger │
 └────────────┬─────────────┘
              │
              ▼
      3-Leg Reconciliation
              │
              ▼
       Anomaly Detection
              │
              ▼
      Confidence Scoring
              │
              ▼
   Systemic Pattern Analysis
              │
              ▼
      Verified Evidence
              │
              ▼
        AI Explanation
              │
              ▼
        React Dashboard
```

---

# 📂 Repository Architecture

The repository is organized into separate layers for the **FastAPI backend, deterministic reconciliation services, synthetic financial datasets, React frontend, documentation, and automated testing**.

```text
Origin/
│
├── .env.example                     # Environment variable template for backend & LLM keys
├── .gitignore                       # Git ignore patterns (venv, node_modules, dist, secrets)
├── pytest.ini                       # Pytest test suite configuration
├── README.md                         # Complete platform documentation & setup guide
├── requirements.txt                  # Python dependencies (FastAPI, Pandas, Pydantic, GenAI)
│
├── backend/                          # FastAPI Backend Application
│   ├── __init__.py
│   ├── main.py                       # Application entry point, CORS config & health endpoints
│   ├── config.py                     # Environment variables, LLM settings & dataset path config
│   │
│   ├── api/                          # REST API Routers
│   │   ├── __init__.py
│   │   ├── investigation.py          # /api/investigate endpoints (POST / GET)
│   │   ├── incidents.py              # /api/incidents endpoints (Systemic & History)
│   │   ├── explain.py                # /api/explain endpoint (LLM explanation)
│   │   └── transactions.py           # /api/transactions endpoint (Dataset index API)
│   │
│   ├── models/                       # Pydantic Schemas & Data Contracts
│   │   ├── __init__.py
│   │   └── schemas.py                # InvestigationResult, SystemicIncident, AnomalyItem
│   │
│   └── services/                     # Core Business Logic & Deterministic Services
│       ├── __init__.py
│       ├── data_loader.py            # Centralized Pandas CSV loading & caching layer
│       ├── investigator.py            # Core deterministic 3-leg investigation engine
│       ├── anomaly_detector.py       # Rule-based anomaly detection rules
│       ├── confidence.py              # Evidence scoring & confidence calculation
│       ├── systemic_analyzer.py       # Systemic failure clustering & incident discovery
│       ├── historical_pattern_analyzer.py # Multi-day historical recurrence telemetry
│       └── ai_service.py              # Gemini / Groq narrative generator with fallback
│
├── data/                             # Synthetic Datasets & Generator
│   ├── generate_data.py              # 12,155 transaction master dataset generator
│   ├── gateway.csv                   # Synthetic Gateway capture records
│   ├── bank.csv                      # Synthetic Acquiring Bank settlement records
│   ├── ledger.csv                    # Synthetic Internal Ledger accounting entries
│   ├── demo_cases.json               # Key official demo transaction mappings
│   └── transaction_classifications.csv # Private developer reference classification dataset
│
├── docs/                             # Documentation & Design System
│   ├── architecture.md               # Detailed system architecture document
│   └── todo.md                       # Task & phase tracking record
│
├── frontend/                         # React 19 + Vite Frontend Application
│   ├── index.html                    # Single-page app HTML template
│   ├── package.json                  # Frontend dependencies (React, Vite, Lucide, Recharts)
│   ├── package-lock.json             # Locked dependency tree
│   ├── vite.config.js                # Vite build and proxy configuration
│   │
│   └── src/                          # Application Source Code
│       ├── main.jsx                  # React DOM root render entry point
│       ├── App.jsx                   # Main layout container & search orchestration
│       ├── api.js                    # API client helper functions (configurable VITE_API_BASE_URL)
│       │
│       ├── components/               # UI Components (Receipt Aesthetic)
│       │   ├── Header.jsx            # Paper header & server health badge
│       │   ├── SearchBar.jsx         # Transaction ID search input
│       │   ├── InvestigationConclusion.jsx # Hero finding banner, status stamp & root cause
│       │   ├── CrossSystemComparison.jsx   # 3-Leg Gateway/Bank/Ledger comparison table
│       │   ├── TransactionTimeline.jsx     # Compact 6-column horizontal chronology timeline
│       │   ├── HistoricalPatternPanel.jsx  # Systemic incident & multi-day telemetry box
│       │   ├── EvidencePanel.jsx           # Audit checklist verification & variance summary
│       │   ├── AIExplanationPanel.jsx       # Subordinate AI explanation & merchant notice copy
│       │   └── EmptyState.jsx               # Default search welcome state
│       │
│       └── styles/                   # Financial Receipt Styling
│           └── dashboard.css         # Off-white paper theme, rules, badge & annotation styles
│
└── tests/                            # Automated Pytest Backend Test Suite (147 Tests)
    ├── test_api.py                   # API router & endpoint response tests
    ├── test_data_generation.py       # Dataset invariants & 12,155 row validation tests
    ├── test_data_loader.py           # DataLoader schema & immutability tests
    ├── test_explain_api.py           # AI explanation service & fallback tests
    ├── test_health.py                # System health endpoint tests
    ├── test_historical_pattern_analyzer.py # Historical pattern analyzer tests
    ├── test_incidents_api.py         # Systemic incident router tests
    ├── test_investigator.py           # Deterministic investigation engine unit tests
    └── test_systemic_analyzer.py      # Incident clustering & deduplication unit tests
```

### Repository Layer Overview

| Layer              | Directory           | Responsibility                                                                   |
| ------------------ | ------------------- | -------------------------------------------------------------------------------- |
| **API**            | `backend/api/`      | REST endpoints exposed to the frontend                                           |
| **Data Contracts** | `backend/models/`   | Pydantic schemas and structured response models                                  |
| **Core Logic**     | `backend/services/` | Reconciliation, anomaly detection, systemic analysis and AI narrative generation |
| **Data**           | `data/`             | Synthetic Gateway, Bank and Ledger datasets                                      |
| **Frontend**       | `frontend/`         | React application and financial receipt interface                                |
| **Documentation**  | `docs/`             | Architecture and project planning documentation                                  |
| **Testing**        | `tests/`            | Automated backend verification suite                                             |

---

# 📊 Master Dataset

Recon Flow operates on a synthetic but internally consistent multi-system transaction dataset designed to reproduce realistic settlement scenarios.

### Dataset Summary

| Classification          |      Count |
| ----------------------- | ---------: |
| Normal                  |     11,075 |
| Systemic                |        225 |
| Delay                   |        200 |
| Amount Mismatch         |        151 |
| Missing Bank            |        151 |
| Missing Ledger          |        151 |
| Duplicate               |        101 |
| Timestamp Inconsistency |        101 |
| **Total**               | **12,155** |

### Dataset Coverage

```text
12,155 unique transactions
        │
        ├── Gateway Records
        ├── Bank Records
        └── Ledger Records
```

Transactions span:

**2026-08-27 → 2026-09-04**

Transaction identifiers range from:

`TXN00001 → TXN12155`

The dataset generator is included in:

```text
data/generate_data.py
```

This allows the synthetic environment to be regenerated and its invariants independently tested.

---

# 🧪 Official Demo Cases

The following transactions are included as representative investigation scenarios.

| Transaction | Scenario                                               |
| ----------- | ------------------------------------------------------ |
| `TXN10001`  | Normal / SUCCESS                                       |
| `TXN10087`  | DELAYED — HDFC Bank SLA timeout (~92 min)              |
| `TXN10142`  | MISMATCH — Gateway ₹5,000 vs Bank ₹4,800               |
| `TXN10211`  | MISSING_DATA — Gateway captured, Bank missing          |
| `TXN10304`  | MISSING_DATA — Bank settled, Ledger missing            |
| `TXN10482`  | DUPLICATE capture                                      |
| `TXN10531`  | INCONSISTENT — Bank received before Gateway initiation |
| `TXN09135`  | Normal / SUCCESS                                       |
| `TXN99999`  | Not Found — HTTP 404                                   |

### Example Investigation

For:

```text
TXN10087
```

Recon Flow can establish:

```text
Gateway
   │
   └── Transaction captured successfully
              │
              ▼
Bank
   │
   └── Settlement delayed beyond SLA
              │
              ▼
Systemic Analyzer
   │
   └── Related bank delays detected
              │
              ▼
Incident
   │
   └── INC-HDF-20260904-03
              │
              ▼
AI Explanation
   │
   └── Human-readable root-cause narrative
```

This demonstrates the difference between **transaction-level investigation** and **systemic settlement intelligence**.

---

# 🤖 AI Architecture

Recon Flow intentionally keeps AI downstream of deterministic analysis.

### AI Input

The AI service receives structured evidence including:

* Transaction status
* Gateway record
* Bank record
* Ledger record
* Detected anomalies
* Timestamp relationships
* Evidence confidence
* Systemic incident information
* Historical patterns

### AI Output

The model generates:

* Investigation explanation
* Root-cause narrative
* Operational recommendation
* Merchant-facing notification

### Supported Providers

```text
                    AI Service
                        │
              ┌─────────┴─────────┐
              │                   │
           Gemini               Groq
              │                   │
              └─────────┬─────────┘
                        │
                 Deterministic
                    Fallback
```

Supported AI integrations:

* **Google Gemini 2.5 Flash**
* **Groq / Llama 3.3 70B**

AI credentials are optional.

The platform remains operational through its deterministic fallback path when an external model is unavailable.

---

# 🎨 Interface

Recon Flow uses a **financial receipt / working-paper visual language** rather than a conventional chatbot interface.

The dashboard includes:

* Transaction search
* Investigation conclusion banner
* Root-cause status
* Gateway / Bank / Ledger comparison
* Transaction chronology
* Historical pattern telemetry
* Systemic incident information
* Evidence checklist
* Variance summary
* AI explanation
* Merchant notification copy
* Backend health status

The interface is designed to make the investigation feel like an **auditable financial working paper**, not an AI chat window.

---

# 🧩 Backend Components

| Component                        | Purpose                                       |
| -------------------------------- | --------------------------------------------- |
| `data_loader.py`                 | Centralized CSV loading and caching           |
| `investigator.py`                | Core deterministic 3-leg reconciliation       |
| `anomaly_detector.py`            | Rule-based anomaly detection                  |
| `confidence.py`                  | Evidence scoring and confidence calculation   |
| `systemic_analyzer.py`           | Failure clustering and incident discovery     |
| `historical_pattern_analyzer.py` | Multi-day recurrence analysis                 |
| `ai_service.py`                  | Gemini/Groq narrative generation and fallback |

---

# 🔌 API Surface

The backend exposes REST endpoints for:

### Investigation

```text
/api/investigate
```

Investigates an individual transaction across Gateway, Bank and Ledger.

### Systemic Incidents

```text
/api/incidents
```

Provides systemic incident and historical pattern information.

### AI Explanation

```text
/api/explain
```

Generates an AI-assisted explanation from verified investigation evidence.

### Transactions

```text
/api/transactions
```

Provides access to the transaction dataset index.

### Health

```text
/health
```

Provides backend health information used by the frontend server-status indicator.

Interactive API documentation is available through FastAPI's Swagger interface.

---

# 🧪 Testing

Recon Flow includes an automated backend test suite containing:

**147 tests**

```text
tests/
├── test_api.py
├── test_data_generation.py
├── test_data_loader.py
├── test_explain_api.py
├── test_health.py
├── test_historical_pattern_analyzer.py
├── test_incidents_api.py
├── test_investigator.py
└── test_systemic_analyzer.py
```

The tests cover:

* API responses
* Dataset generation invariants
* Data loader behavior
* Schema validation
* AI fallback behavior
* Health endpoints
* Historical pattern analysis
* Incident detection
* Deterministic investigation logic
* Systemic clustering and deduplication

Run the complete backend suite with:

```bash
pytest tests/ -v
```

---

# 🛠️ Technology Stack

## Backend

* Python 3.11+
* FastAPI
* Uvicorn
* Pandas
* Pydantic
* Pytest

## Frontend

* React 19
* Vite
* Lucide React
* Recharts
* CSS Variables

## AI

* Google GenAI SDK
* Gemini 2.5 Flash
* Groq API
* Llama 3.3 70B

## Data

* CSV-based synthetic transaction datasets
* Pandas-based processing
* Deterministic rule engine

---

# ⚡ Quick Start

## Prerequisites

Install:

* Python 3.11+
* Node.js 18+

---

## 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd recon-flow
```

---

## 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Add either an AI provider key:

```env
GEMINI_API_KEY=your_key_here
```

or:

```env
GROQ_API_KEY=your_key_here
```

AI keys are optional because Recon Flow includes a deterministic fallback.

---

## 3. Start the Backend

Create a Python virtual environment:

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 4. Start the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔄 Development Workflow

```text
Synthetic Data
      │
      ▼
Data Loader
      │
      ▼
Deterministic Investigation
      │
      ├── Reconciliation
      ├── Anomaly Detection
      ├── Confidence
      ├── Systemic Analysis
      └── Historical Patterns
      │
      ▼
Structured Investigation Result
      │
      ▼
AI Narrative Service
      │
      ▼
FastAPI
      │
      ▼
React Dashboard
```

---

# 🏆 What Makes Recon Flow Different?

Most basic settlement-agent implementations can be reduced to:

```text
CSV → LLM → Answer
```

Recon Flow instead follows:

```text
Gateway + Bank + Ledger
          │
          ▼
Deterministic Reconciliation
          │
          ▼
Anomaly Detection
          │
          ▼
Evidence Verification
          │
          ▼
Systemic Pattern Detection
          │
          ▼
AI Interpretation
          │
          ▼
Operational Intelligence
```

### The key differentiators are:

**1. Three-system reconciliation**

The platform does not reason from a single transaction record.

**2. Deterministic-first architecture**

AI does not decide whether the underlying financial records match.

**3. Systemic incident discovery**

The system can identify patterns spanning multiple transactions.

**4. Historical context**

Individual failures can be interpreted against multi-day transaction behavior.

**5. Evidence-backed AI**

AI explanations are grounded in structured investigation results.

**6. Graceful AI fallback**

The core investigation remains functional without an external LLM.

**7. Audit-oriented interface**

The UI presents evidence, chronology and reconciliation results rather than only conversational responses.

---

# 📈 Design Principles

### Deterministic Before Generative

Financial facts are calculated by deterministic logic.

### Evidence Before Explanation

An explanation is generated only after the underlying evidence has been structured.

### Transaction-Level + System-Level Intelligence

A single failed transaction and a widespread infrastructure problem require different investigation strategies.

### Explainability

Every conclusion should be traceable back to the Gateway, Bank, Ledger, anomaly rules and evidence used to produce it.

### Graceful Degradation

External AI services enhance the system but are not a single point of failure.

### Testability

Core reconciliation and systemic analysis logic is independently tested rather than hidden inside prompts.

---

# 📁 Important Files

| File                                    | Purpose                             |
| --------------------------------------- | ----------------------------------- |
| `backend/services/investigator.py`      | Core reconciliation engine          |
| `backend/services/anomaly_detector.py`  | Settlement anomaly rules            |
| `backend/services/systemic_analyzer.py` | Systemic incident detection         |
| `backend/services/confidence.py`        | Evidence confidence scoring         |
| `backend/services/ai_service.py`        | AI narrative generation             |
| `data/generate_data.py`                 | Synthetic dataset generation        |
| `data/demo_cases.json`                  | Official demonstration scenarios    |
| `frontend/src/App.jsx`                  | Main frontend orchestration         |
| `frontend/src/components/`              | Investigation dashboard components  |
| `docs/architecture.md`                  | Detailed architecture documentation |
| `tests/`                                | Automated backend test suite        |

---

# 📋 Project Status

Recon Flow currently includes:

* ✅ 3-leg Gateway / Bank / Ledger reconciliation
* ✅ Automated anomaly detection
* ✅ Systemic incident clustering
* ✅ Historical pattern analysis
* ✅ Evidence confidence scoring
* ✅ Gemini integration
* ✅ Groq integration
* ✅ Deterministic AI fallback
* ✅ React investigation dashboard
* ✅ Transaction timeline
* ✅ Evidence panel
* ✅ AI explanation panel
* ✅ Merchant notification generation
* ✅ Synthetic 12,155-transaction dataset
* ✅ 147 automated backend tests
* ✅ API documentation through FastAPI Swagger

---

# ⚠️ Data & Demo Disclaimer

Recon Flow uses **synthetic transaction data** for demonstration and development purposes.

The Gateway, Bank and Ledger datasets do not represent real financial transactions, customers, merchants, banks, or payment information.

The project is intended as a **hackathon / prototype settlement intelligence platform** and should not be used for production financial reconciliation without appropriate security, compliance, data-integrity, access-control and operational safeguards.

---

# 🔮 Future Extensions

Potential future improvements include:

* Real payment processor integrations
* Production database support
* Streaming transaction ingestion
* Real-time settlement monitoring
* Predictive settlement risk scoring
* Automated remediation workflows
* Human-in-the-loop approval flows
* Merchant-level anomaly profiling
* Advanced systemic root-cause correlation
* Distributed event processing
* Role-based operational access
* Full audit-log persistence

---

# 💡 Project Philosophy

Recon Flow is built around a simple idea:

> **Don't just tell an operator that a transaction failed. Show them what happened, prove why it happened, determine whether it is part of something larger, and explain what should happen next.**

```text
RECONCILE
    ↓
DETECT
    ↓
CORRELATE
    ↓
INVESTIGATE
    ↓
EXPLAIN
    ↓
ACT
```

**Recon Flow — Settlement Intelligence Platform**

*From reconciliation to investigation. From isolated failures to systemic intelligence.*
