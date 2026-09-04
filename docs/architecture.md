# Settlement Intelligence --- Architecture

## 1. Architecture Goal

Build a simple, local, hackathon-friendly architecture that separates:

1.  User interface
2.  API/backend
3.  Deterministic investigation logic
4.  Systemic analytics
5.  AI explanation
6.  Synthetic data

The architecture intentionally avoids databases and complex
infrastructure because the problem statement permits mock CSV data and
the project must be buildable within an overnight hackathon.

------------------------------------------------------------------------

# 2. High-Level Architecture

``` text
                         USER / JUDGE
                              |
                              v
                    +---------------------+
                    |   React + Vite UI   |
                    |   Fintech Dashboard |
                    +----------+----------+
                               |
                         HTTP / JSON
                               |
                               v
                    +---------------------+
                    |       FastAPI       |
                    |       Backend       |
                    +----------+----------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
      +---------------+ +---------------+ +-------------+
      | Investigation | |   Systemic    | | AI Service  |
      |    Engine     | |   Analyzer    | | Gemini/Groq |
      +-------+-------+ +-------+-------+ +------+------+
              |                 |                |
              +-----------------+----------------+
                                |
                                v
                    +-------------------------+
                    |       Data Layer        |
                    |                         |
                    | gateway.csv             |
                    | bank.csv                |
                    | ledger.csv              |
                    +-------------------------+
```

------------------------------------------------------------------------

# 3. Why a Backend Is Used

The backend is not a large production server.

For this project, the backend is simply a Python application running
locally.

Example:

``` text
React frontend
http://localhost:5173

FastAPI backend
http://localhost:8000
```

The frontend sends an HTTP request:

``` http
POST /api/investigate
```

with:

``` json
{
  "transaction_id": "TXN10087"
}
```

The FastAPI backend:

1.  Loads/searches the datasets.
2.  Investigates the transaction.
3.  Calculates anomalies and confidence.
4.  Performs systemic checks.
5.  Calls the LLM when explanation is required.
6.  Returns structured JSON.

This separation keeps Python/Pandas logic out of the browser and makes
the system easier to explain and extend.

------------------------------------------------------------------------

# 4. Technology Stack

  Layer             Technology                Responsibility
  ----------------- ------------------------- ---------------------------------------
  Frontend          React                     User interface
  Build tool        Vite                      Frontend development
  Styling           CSS / optional Tailwind   UI styling
  Charts            Recharts                  System-health visualization
  Backend           Python                    Core application logic
  API               FastAPI                   REST endpoints
  Server            Uvicorn                   Runs FastAPI locally
  Data processing   Pandas                    CSV loading and analysis
  Data              CSV                       Synthetic gateway/bank/ledger records
  AI                Gemini or Groq            Explanation/orchestration
  Validation        Pydantic                  API request/response schemas
  Version control   Git                       Collaboration/versioning

------------------------------------------------------------------------

# 5. Systems That Are NOT Required

Do not add these unless there is a concrete requirement:

-   PostgreSQL
-   MongoDB
-   Firebase
-   Redis
-   Docker
-   Kubernetes
-   Authentication
-   Vector database
-   RAG
-   Fine-tuning
-   Microservices
-   Separate AI agents
-   Real bank APIs
-   Real payment APIs

The project is deliberately a single backend application with local
synthetic data.

------------------------------------------------------------------------

# 6. Backend Architecture

``` text
backend/
|
+-- main.py
|
+-- config.py
|
+-- api/
|   +-- investigation.py
|   +-- incidents.py
|
+-- models/
|   +-- schemas.py
|
+-- services/
    +-- data_loader.py
    +-- investigator.py
    +-- anomaly_detector.py
    +-- confidence.py
    +-- systemic_analyzer.py
    +-- ai_service.py
```

------------------------------------------------------------------------

# 7. Backend Responsibilities

## `main.py`

Responsibilities:

-   Create FastAPI application.
-   Register API routers.
-   Configure CORS.
-   Provide health endpoint.
-   Start application through Uvicorn.

Think of this as the backend entry point.

------------------------------------------------------------------------

## `config.py`

Responsibilities:

-   Environment variables
-   LLM API key
-   Data file paths
-   Application configuration

Example environment variables:

``` text
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
```

Never commit actual API keys.

------------------------------------------------------------------------

## `data_loader.py`

Responsibilities:

-   Load CSV datasets using Pandas.
-   Keep data access centralized.
-   Provide functions for retrieving records.

Potential functions:

``` python
load_gateway()
load_bank()
load_ledger()

find_gateway_transaction(transaction_id)
find_bank_transaction(transaction_id)
find_ledger_transaction(transaction_id)
```

------------------------------------------------------------------------

## `investigator.py`

This is the core deterministic engine.

Input:

``` text
transaction_id
```

Process:

``` text
Find Gateway
      |
Find Bank
      |
Find Ledger
      |
Compare amounts
      |
Compare statuses
      |
Compare timestamps
      |
Calculate delays
      |
Build timeline
      |
Build evidence
```

Output:

A structured investigation object.

------------------------------------------------------------------------

## `anomaly_detector.py`

Responsibilities:

-   Detect missing records.
-   Detect amount mismatch.
-   Detect duplicates.
-   Detect timestamp inconsistency.
-   Detect bank delay.
-   Detect status conflicts.

This service should contain deterministic rules.

------------------------------------------------------------------------

## `confidence.py`

Responsibilities:

-   Calculate evidence score.
-   Convert score to confidence category.
-   Provide confidence reasons.

Example:

``` text
Gateway found             +20
Bank found                +20
Ledger found              +20
Amounts match             +15
Timestamps consistent     +10
Statuses consistent       +10
Known response code        +5
                           ---
                           100
```

------------------------------------------------------------------------

## `systemic_analyzer.py`

Responsibilities:

-   Analyze all transactions.
-   Find concentrations.
-   Find spikes.
-   Group similar failures.
-   Estimate affected transaction count.
-   Estimate affected settlement value.
-   Produce incident objects.
-   Determine transaction-to-incident association.

Potential analyses:

``` text
Delayed transactions by bank
Failed transactions by gateway
Failures by response code
Failures by hour/time window
Failures by amount range
Bank + gateway + error combinations
```

------------------------------------------------------------------------

## `ai_service.py`

Responsibilities:

-   Call Gemini or Groq.
-   Receive structured evidence.
-   Generate natural-language explanation.
-   Generate merchant-facing response.
-   Summarize incidents where useful.

The LLM must not be responsible for:

-   Looking up CSV rows directly
-   Calculating settlement delay
-   Determining amount mismatches
-   Inventing confidence
-   Deciding that missing data exists

The deterministic engine is the source of truth.

------------------------------------------------------------------------

# 8. AI Architecture

Recommended flow:

``` text
User question
     |
     v
FastAPI
     |
     v
Deterministic investigation
     |
     v
Structured evidence
     |
     v
LLM
     |
     v
Structured explanation
     |
     v
FastAPI validation
     |
     v
React UI
```

Example evidence sent to LLM:

``` json
{
  "transaction_id": "TXN10087",
  "status": "DELAYED",
  "delay_minutes": 92,
  "gateway": {
    "status": "CAPTURED",
    "settlement_initiated_at": "14:33"
  },
  "bank": {
    "status": "SETTLED",
    "expected_settlement_at": "14:45",
    "settled_at": "16:17"
  },
  "ledger": {
    "status": "POSTED",
    "created_at": "16:18"
  },
  "anomalies": [
    "BANK_SETTLEMENT_DELAY"
  ],
  "confidence": 94
}
```

The AI converts this into a concise explanation.

------------------------------------------------------------------------

# 9. Frontend Architecture

``` text
frontend/src/
|
+-- main.jsx
+-- App.jsx
+-- api.js
|
+-- pages/
|   +-- Investigation.jsx
|   +-- SystemHealth.jsx
|   +-- IncidentDetails.jsx
|
+-- components/
|   +-- SearchBar.jsx
|   +-- StatusCard.jsx
|   +-- TransactionTimeline.jsx
|   +-- EvidencePanel.jsx
|   +-- ConfidenceScore.jsx
|   +-- ExceptionPanel.jsx
|   +-- IncidentBanner.jsx
|   +-- AgentActivity.jsx
|
+-- styles/
    +-- global.css
    +-- dashboard.css
    +-- components.css
```

------------------------------------------------------------------------

# 10. Frontend Responsibilities

## `App.jsx`

Controls navigation and application-level layout.

## `api.js`

Contains all backend HTTP calls.

Example:

``` javascript
investigateTransaction(transactionId)
getSystemHealth()
getIncidents()
getIncident(incidentId)
```

## `Investigation.jsx`

Displays the transaction investigation workflow.

## `SystemHealth.jsx`

Displays aggregate system metrics and detected incidents.

## `IncidentDetails.jsx`

Displays an incident and affected transactions.

------------------------------------------------------------------------

# 11. API Design

## POST `/api/investigate`

Request:

``` json
{
  "transaction_id": "TXN10087"
}
```

Response:

``` json
{
  "transaction_id": "TXN10087",
  "status": "DELAYED",
  "summary": "Settlement delayed by 92 minutes.",
  "confidence": 94,
  "gateway": {},
  "bank": {},
  "ledger": {},
  "timeline": [],
  "evidence": [],
  "exceptions": [],
  "similar_transactions": [],
  "incident": null
}
```

------------------------------------------------------------------------

## GET `/api/system-health`

Returns aggregate statistics.

Example:

``` json
{
  "total_transactions": 1000,
  "successful": 850,
  "failed": 25,
  "delayed": 100,
  "total_settlement_value": 2840000,
  "incident_count": 1
}
```

------------------------------------------------------------------------

## GET `/api/incidents`

Returns detected incidents.

------------------------------------------------------------------------

## GET `/api/incidents/{incident_id}`

Returns:

-   Incident metadata
-   Detection reasons
-   Affected transaction IDs
-   Affected value
-   Common bank
-   Common gateway
-   Common response code
-   Time window

------------------------------------------------------------------------

# 12. Data Architecture

The project uses three synthetic datasets.

## Gateway

``` text
data/gateway.csv
```

Fields:

``` text
transaction_id
gateway_reference
merchant_id
amount
currency
payment_method
gateway_status
initiated_at
captured_at
settlement_initiated_at
response_code
response_message
```

## Bank

``` text
data/bank.csv
```

Fields:

``` text
transaction_id
bank_reference
bank_name
amount
bank_status
received_at
expected_settlement_at
settled_at
response_code
response_message
```

## Ledger

``` text
data/ledger.csv
```

Fields:

``` text
transaction_id
ledger_entry_id
amount
ledger_status
created_at
settlement_date
reconciliation_status
```

------------------------------------------------------------------------

# 13. Data Generation Architecture

``` text
generate_data.py
       |
       v
Generate base transactions
       |
       v
Generate gateway records
       |
       v
Generate bank records
       |
       v
Generate ledger records
       |
       v
Inject controlled anomalies
       |
       v
Write CSV files
       |
       v
Write demo_cases.json
```

Use a fixed random seed.

The data generator must ensure normal records remain internally
consistent.

------------------------------------------------------------------------

# 14. Transaction Investigation Sequence

``` text
POST /api/investigate
        |
        v
Validate transaction ID
        |
        v
Load/find gateway record
        |
        v
Load/find bank record
        |
        v
Load/find ledger record
        |
        v
Compare records
        |
        +--> Amount mismatch?
        |
        +--> Missing record?
        |
        +--> Duplicate?
        |
        +--> Timestamp conflict?
        |
        +--> Settlement delay?
        |
        v
Build timeline
        |
        v
Build evidence
        |
        v
Calculate confidence
        |
        v
Find similar transactions
        |
        v
Check incident association
        |
        v
Generate AI explanation
        |
        v
Return validated JSON
```

------------------------------------------------------------------------

# 15. Systemic Analysis Sequence

``` text
All transaction records
          |
          v
Aggregate by bank
          |
          v
Aggregate by gateway
          |
          v
Aggregate by response code
          |
          v
Analyze time windows
          |
          v
Analyze amount ranges
          |
          v
Find unusual concentrations/spikes
          |
          v
Cluster related failures
          |
          v
Generate incident
          |
          v
Associate affected transactions
```

------------------------------------------------------------------------

# 16. Incident Object

Recommended structure:

``` json
{
  "incident_id": "INC-001",
  "title": "BANK_X settlement degradation",
  "severity": "HIGH",
  "affected_transaction_count": 417,
  "affected_value": 2840000,
  "primary_bank": "BANK_X",
  "primary_gateway": "GATEWAY_Y",
  "dominant_error": "BANK_TIMEOUT",
  "start_time": "14:00",
  "end_time": "16:00",
  "detection_reasons": [
    "82% of delayed transactions involve BANK_X",
    "Failure rate increased during 14:00-16:00",
    "BANK_TIMEOUT appears unusually frequently"
  ],
  "affected_transactions": [
    "TXN10087"
  ]
}
```

------------------------------------------------------------------------

# 17. Error Handling

## Transaction not found

Return a clear 404-style application response.

UI:

> Transaction TXN99999 was not found in the available datasets.

## Missing data

Return investigation with explicit missing status.

## LLM failure

The transaction investigation must still be displayed using
deterministic results.

Example fallback:

> AI explanation unavailable. Deterministic investigation completed
> successfully.

## Backend unavailable

Frontend should display a clear connection error.

------------------------------------------------------------------------

# 18. Local Development

Start backend:

``` bash
python -m uvicorn backend.main:app --reload
```

Backend:

``` text
http://localhost:8000
```

FastAPI docs:

``` text
http://localhost:8000/docs
```

Start frontend:

``` bash
npm run dev
```

Frontend:

``` text
http://localhost:5173
```

Both applications run on the same laptop during the hackathon.

------------------------------------------------------------------------

# 19. Security and Configuration

Use:

``` text
.env
```

for API keys.

Provide:

``` text
.env.example
```

Example:

``` text
LLM_PROVIDER=gemini
GEMINI_API_KEY=
```

`.env` must be ignored by Git.

Only synthetic data may be used.

------------------------------------------------------------------------

# 20. Architectural Principle

The architecture follows:

> Deterministic systems establish facts. AI explains those facts.

This is important for reliability and for the project presentation.

The system is not:

``` text
CSV -> LLM -> random answer
```

It is:

``` text
CSV
 ↓
Deterministic investigation
 ↓
Validated evidence
 ↓
Systemic analysis
 ↓
AI explanation
 ↓
Human-readable result
```

------------------------------------------------------------------------

# 21. Why This Architecture Is Appropriate for the Hackathon

It provides:

-   Simple implementation
-   Clear separation of responsibilities
-   No database setup
-   Easy local execution
-   Reliable deterministic calculations
-   AI where it adds real value
-   A strong demonstration of agentic behavior
-   A clear path to production evolution

A future production version could replace the CSV layer with real
gateway, bank, and ledger APIs/databases without fundamentally changing
the investigation interface.
