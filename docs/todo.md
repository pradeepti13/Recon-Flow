# Settlement Intelligence --- TODO

## How to Use This File

Build in the order shown below.

**Rule:** Do not move to the next major phase until the current phase
works.

**Priority levels:**

-   🔴 MUST HAVE --- required for a working demo
-   🟠 SHOULD HAVE --- important differentiators
-   🟢 NICE TO HAVE --- only after the core is stable

------------------------------------------------------------------------

# PHASE 0 --- Project Setup

## Goal

Get a React frontend and FastAPI backend running locally.

### Tasks

-   [ ] 🔴 Create project repository
-   [ ] 🔴 Create root project folder
-   [ ] 🔴 Initialize Git
-   [ ] 🔴 Create React + Vite frontend
-   [ ] 🔴 Create Python backend
-   [ ] 🔴 Create virtual environment
-   [ ] 🔴 Install FastAPI
-   [ ] 🔴 Install Uvicorn
-   [ ] 🔴 Install Pandas
-   [ ] 🔴 Install Pydantic
-   [ ] 🔴 Install selected LLM SDK
-   [ ] 🔴 Create `.env`
-   [ ] 🔴 Create `.env.example`
-   [ ] 🔴 Create `.gitignore`
-   [ ] 🔴 Create `requirements.txt`
-   [ ] 🔴 Verify frontend starts
-   [ ] 🔴 Verify backend starts
-   [ ] 🔴 Verify `http://localhost:8000/docs`

### Expected result

``` text
React      -> localhost:5173
FastAPI    -> localhost:8000
Swagger    -> localhost:8000/docs
```

### Git checkpoint

``` text
v1-setup
```

------------------------------------------------------------------------

# PHASE 1 --- Synthetic Data

## Goal

Create reliable, internally consistent gateway/bank/ledger datasets.

### Files

-   [ ] 🔴 `data/generate_data.py`
-   [ ] 🔴 `data/gateway.csv`
-   [ ] 🔴 `data/bank.csv`
-   [ ] 🔴 `data/ledger.csv`
-   [ ] 🔴 `data/demo_cases.json`

### Dataset

Generate approximately 1,000 transactions.

Use a fixed random seed.

### Normal data

-   [ ] 🔴 Generate transaction IDs
-   [ ] 🔴 Generate merchant IDs
-   [ ] 🔴 Generate amounts
-   [ ] 🔴 Generate currencies
-   [ ] 🔴 Generate payment methods
-   [ ] 🔴 Generate timestamps
-   [ ] 🔴 Generate bank names
-   [ ] 🔴 Generate gateway references
-   [ ] 🔴 Generate bank references
-   [ ] 🔴 Generate ledger references

### Controlled anomalies

-   [ ] 🔴 Normal transaction
-   [ ] 🔴 Bank settlement delay
-   [ ] 🔴 Amount mismatch
-   [ ] 🔴 Missing bank
-   [ ] 🔴 Missing ledger
-   [ ] 🔴 Duplicate transaction
-   [ ] 🔴 Timestamp inconsistency
-   [ ] 🟠 Systemic incident cluster

### Validation

-   [ ] 🔴 Verify normal transaction matches across systems
-   [ ] 🔴 Verify amount mismatch case
-   [ ] 🔴 Verify missing bank case
-   [ ] 🔴 Verify missing ledger case
-   [ ] 🔴 Verify duplicate case
-   [ ] 🔴 Verify timestamp case
-   [ ] 🟠 Verify systemic cluster contains many related failures
-   [ ] 🔴 Verify demo IDs are stored in `demo_cases.json`

### Git checkpoint

``` text
v2-data
```

------------------------------------------------------------------------

# PHASE 2 --- Data Loader

## Goal

Make CSV data accessible to backend services.

### Tasks

-   [ ] 🔴 Create `backend/services/data_loader.py`
-   [ ] 🔴 Load gateway CSV with Pandas
-   [ ] 🔴 Load bank CSV with Pandas
-   [ ] 🔴 Load ledger CSV with Pandas
-   [ ] 🔴 Handle missing files cleanly
-   [ ] 🔴 Add transaction lookup functions
-   [ ] 🔴 Verify lookups using demo IDs

### Expected functions

``` text
load_gateway()
load_bank()
load_ledger()

find_gateway_transaction(id)
find_bank_transaction(id)
find_ledger_transaction(id)
```

### Git checkpoint

``` text
v3-data-loader
```

------------------------------------------------------------------------

# PHASE 3 --- Deterministic Investigation Engine

## Goal

Investigate one transaction without AI.

### Files

-   [ ] 🔴 `backend/services/investigator.py`
-   [ ] 🔴 `backend/services/anomaly_detector.py`
-   [ ] 🔴 `backend/services/confidence.py`
-   [ ] 🔴 `backend/models/schemas.py`

### Investigation

-   [ ] 🔴 Find gateway record
-   [ ] 🔴 Find bank record
-   [ ] 🔴 Find ledger record
-   [ ] 🔴 Compare amounts
-   [ ] 🔴 Compare statuses
-   [ ] 🔴 Compare timestamps
-   [ ] 🔴 Calculate settlement delay
-   [ ] 🔴 Build transaction timeline
-   [ ] 🔴 Build evidence list

### Anomaly detection

-   [ ] 🔴 Bank delay
-   [ ] 🔴 Amount mismatch
-   [ ] 🔴 Missing bank
-   [ ] 🔴 Missing ledger
-   [ ] 🔴 Duplicate
-   [ ] 🔴 Timestamp inconsistency
-   [ ] 🔴 Conflicting statuses

### Confidence

-   [ ] 🔴 Implement evidence score
-   [ ] 🔴 Implement confidence category
-   [ ] 🔴 Store confidence reasons

### Testing

Run every demo transaction through the investigator.

Expected:

``` text
Normal            -> SUCCESS
Bank delay        -> DELAYED
Amount mismatch   -> MISMATCH
Missing bank      -> MISSING_DATA
Missing ledger    -> MISSING_DATA
Duplicate         -> CONFLICTING/MISMATCH
Timestamp error   -> CONFLICTING
```

### Git checkpoint

``` text
v4-investigator
```

------------------------------------------------------------------------

# PHASE 4 --- FastAPI Backend

## Goal

Expose the investigation engine through REST APIs.

### Files

-   [ ] 🔴 `backend/main.py`
-   [ ] 🔴 `backend/api/investigation.py`
-   [ ] 🔴 `backend/api/incidents.py`
-   [ ] 🔴 `backend/config.py`

### Endpoints

-   [ ] 🔴 `POST /api/investigate`
-   [ ] 🟠 `GET /api/system-health`
-   [ ] 🟠 `GET /api/incidents`
-   [ ] 🟠 `GET /api/incidents/{incident_id}`

### Configuration

-   [ ] 🔴 Enable CORS for local frontend
-   [ ] 🔴 Add health endpoint
-   [ ] 🔴 Add error handling
-   [ ] 🔴 Validate request schemas
-   [ ] 🔴 Validate response schemas

### Testing

Use:

``` text
http://localhost:8000/docs
```

Test:

``` json
{
  "transaction_id": "TXN10087"
}
```

### Git checkpoint

``` text
v5-api
```

------------------------------------------------------------------------

# PHASE 5 --- AI Explanation

## Goal

Add an LLM only after deterministic investigation works.

### File

-   [ ] 🔴 `backend/services/ai_service.py`

### Tasks

-   [ ] 🔴 Configure Gemini or Groq
-   [ ] 🔴 Read API key from `.env`
-   [ ] 🔴 Create strict system prompt
-   [ ] 🔴 Pass structured evidence to LLM
-   [ ] 🔴 Request structured JSON
-   [ ] 🔴 Validate response
-   [ ] 🔴 Preserve deterministic confidence
-   [ ] 🔴 Handle API failure
-   [ ] 🔴 Provide deterministic fallback

### AI rules

-   [ ] 🔴 Never invent transaction information
-   [ ] 🔴 Never invent timestamps
-   [ ] 🔴 Never invent amounts
-   [ ] 🔴 Never claim missing records exist
-   [ ] 🔴 Never override deterministic results
-   [ ] 🔴 Clearly communicate uncertainty
-   [ ] 🔴 Produce merchant-facing explanation

### Git checkpoint

``` text
v6-ai
```

------------------------------------------------------------------------

# PHASE 6 --- React Dashboard

## Goal

Create a professional fintech operations interface.

### Structure

-   [ ] 🔴 `frontend/src/App.jsx`
-   [ ] 🔴 `frontend/src/api.js`
-   [ ] 🔴 `frontend/src/pages/Investigation.jsx`
-   [ ] 🟠 `frontend/src/pages/SystemHealth.jsx`
-   [ ] 🟠 `frontend/src/pages/IncidentDetails.jsx`

### Components

-   [ ] 🔴 SearchBar
-   [ ] 🔴 StatusCard
-   [ ] 🔴 TransactionTimeline
-   [ ] 🔴 EvidencePanel
-   [ ] 🔴 ConfidenceScore
-   [ ] 🔴 ExceptionPanel
-   [ ] 🟠 IncidentBanner
-   [ ] 🟠 AgentActivity

### Investigation page

-   [ ] 🔴 Search transaction ID
-   [ ] 🔴 Call backend
-   [ ] 🔴 Show loading state
-   [ ] 🔴 Show gateway card
-   [ ] 🔴 Show bank card
-   [ ] 🔴 Show ledger card
-   [ ] 🔴 Show timeline
-   [ ] 🔴 Show AI summary
-   [ ] 🔴 Show confidence
-   [ ] 🔴 Show evidence
-   [ ] 🔴 Show exceptions
-   [ ] 🟠 Show similar transactions
-   [ ] 🟠 Show incident association

### Design

-   [ ] 🔴 Make it look like a fintech operations dashboard
-   [ ] 🔴 Avoid making chat the main UI
-   [ ] 🔴 Make status visually obvious
-   [ ] 🔴 Use clear success/warning/error states
-   [ ] 🔴 Add responsive layout
-   [ ] 🟠 Add polished loading animation

### Git checkpoint

``` text
v7-ui
```

------------------------------------------------------------------------

# PHASE 7 --- Systemic Intelligence

## Goal

Detect when individual settlement problems form a larger incident.

### File

-   [ ] 🟠 `backend/services/systemic_analyzer.py`

### Analysis

-   [ ] 🟠 Failure rate by bank
-   [ ] 🟠 Delay rate by bank
-   [ ] 🟠 Failure rate by gateway
-   [ ] 🟠 Response code frequency
-   [ ] 🟠 Time-window analysis
-   [ ] 🟠 Amount-range analysis
-   [ ] 🟠 Bank + gateway combinations
-   [ ] 🟠 Affected settlement value
-   [ ] 🟠 Identify unusual concentrations

### Incident generation

-   [ ] 🟠 Generate incident ID
-   [ ] 🟠 Generate title
-   [ ] 🟠 Determine severity
-   [ ] 🟠 Count affected transactions
-   [ ] 🟠 Calculate affected value
-   [ ] 🟠 Identify primary bank
-   [ ] 🟠 Identify primary gateway
-   [ ] 🟠 Identify dominant response code
-   [ ] 🟠 Identify time window
-   [ ] 🟠 Generate detection reasons
-   [ ] 🟠 Store affected transaction IDs

### Transaction association

-   [ ] 🟠 Determine whether investigated transaction belongs to
    incident
-   [ ] 🟠 Return incident information in investigation response

### Git checkpoint

``` text
v8-systemic
```

------------------------------------------------------------------------

# PHASE 8 --- System Health UI

## Goal

Show the project operating at system level.

### Tasks

-   [ ] 🟠 Create System Health page
-   [ ] 🟠 Total transaction metric
-   [ ] 🟠 Successful metric
-   [ ] 🟠 Failed metric
-   [ ] 🟠 Delayed metric
-   [ ] 🟠 Total settlement value
-   [ ] 🟠 Incident count
-   [ ] 🟠 Failure/delay trend chart
-   [ ] 🟠 Bank breakdown
-   [ ] 🟠 Gateway breakdown
-   [ ] 🟠 Response-code breakdown
-   [ ] 🟠 Incident cards

### Git checkpoint

``` text
v9-health-ui
```

------------------------------------------------------------------------

# PHASE 9 --- Incident Drill-Down

## Goal

Create the project's main WOW interaction.

### Tasks

-   [ ] 🟠 Show `INCIDENT DETECTED`
-   [ ] 🟠 Show affected transaction count
-   [ ] 🟠 Show affected settlement value
-   [ ] 🟠 Show common bank
-   [ ] 🟠 Show common gateway
-   [ ] 🟠 Show dominant error
-   [ ] 🟠 Show peak time window
-   [ ] 🟠 Show detection reasons
-   [ ] 🟠 List affected transactions
-   [ ] 🟠 Allow clicking an affected transaction
-   [ ] 🟠 Navigate to transaction investigation

### Critical interaction

Transaction page:

``` text
This transaction appears to be part
of a larger settlement incident.

[ VIEW INCIDENT ]
```

Clicking it opens the incident.

### Git checkpoint

``` text
v10-incident
```

------------------------------------------------------------------------

# PHASE 10 --- Similar Transactions

## Goal

Connect individual investigation to systemic intelligence.

### Tasks

-   [ ] 🟠 Identify similar transactions
-   [ ] 🟠 Compare bank
-   [ ] 🟠 Compare gateway
-   [ ] 🟠 Compare response code
-   [ ] 🟠 Compare time window
-   [ ] 🟠 Compare status
-   [ ] 🟠 Display count of similar transactions
-   [ ] 🟠 Display common characteristics
-   [ ] 🟠 Link to investigation of similar transaction

### Example

``` text
39 similar transactions found

Bank: BANK_X
Gateway: GATEWAY_Y
Error: BANK_TIMEOUT
Time: 14:00–16:00
```

------------------------------------------------------------------------

# PHASE 11 --- Demo Controls

## Goal

Make the presentation reliable.

### Tasks

-   [ ] 🟠 Load `demo_cases.json`
-   [ ] 🟠 Add Normal demo button
-   [ ] 🟠 Add Bank Delay demo button
-   [ ] 🟠 Add Amount Mismatch demo button
-   [ ] 🟠 Add Missing Bank demo button
-   [ ] 🟠 Add Missing Ledger demo button
-   [ ] 🟠 Add Systemic Incident demo button

Buttons should populate the transaction search field or directly trigger
investigation.

### Git checkpoint

``` text
v11-demo
```

------------------------------------------------------------------------

# PHASE 12 --- Agent Activity UI

## Goal

Make the investigation feel observable without exposing
chain-of-thought.

### Tasks

-   [ ] 🟢 Show "Transaction received"
-   [ ] 🟢 Show "Querying gateway"
-   [ ] 🟢 Show "Gateway record found"
-   [ ] 🟢 Show "Querying bank"
-   [ ] 🟢 Show "Bank record found"
-   [ ] 🟢 Show "Querying ledger"
-   [ ] 🟢 Show "Ledger record found"
-   [ ] 🟢 Show "Comparing records"
-   [ ] 🟢 Show "Checking systemic patterns"
-   [ ] 🟢 Show "Investigation complete"

Do not display hidden reasoning or chain-of-thought.

------------------------------------------------------------------------

# PHASE 13 --- Error Handling and Reliability

## Mandatory

-   [ ] 🔴 Test transaction not found
-   [ ] 🔴 Test missing bank
-   [ ] 🔴 Test missing ledger
-   [ ] 🔴 Test malformed transaction ID
-   [ ] 🔴 Test LLM API failure
-   [ ] 🔴 Test backend restart
-   [ ] 🔴 Test empty CSV
-   [ ] 🔴 Test duplicate records
-   [ ] 🔴 Test frontend API failure

### LLM fallback

If the LLM fails:

``` text
AI explanation unavailable.
Deterministic investigation completed successfully.
```

The transaction evidence must still display.

------------------------------------------------------------------------

# PHASE 14 --- End-to-End Testing

## Test 1 --- Normal

-   [ ] 🔴 Search normal transaction
-   [ ] 🔴 Gateway matches
-   [ ] 🔴 Bank matches
-   [ ] 🔴 Ledger matches
-   [ ] 🔴 Status correct
-   [ ] 🔴 Confidence high
-   [ ] 🔴 No false incident

## Test 2 --- Bank Delay

-   [ ] 🔴 Search bank-delay transaction
-   [ ] 🔴 Delay calculated correctly
-   [ ] 🔴 Evidence displayed
-   [ ] 🔴 AI explanation correct
-   [ ] 🟠 Incident association works

## Test 3 --- Amount Mismatch

-   [ ] 🔴 Search mismatch transaction
-   [ ] 🔴 Gateway amount displayed
-   [ ] 🔴 Bank amount displayed
-   [ ] 🔴 Ledger amount displayed
-   [ ] 🔴 Mismatch detected
-   [ ] 🔴 Exception displayed

## Test 4 --- Missing Bank

-   [ ] 🔴 Search transaction
-   [ ] 🔴 Gateway displayed
-   [ ] 🔴 Bank marked missing
-   [ ] 🔴 Ledger state handled correctly
-   [ ] 🔴 Confidence reduced
-   [ ] 🔴 AI does not invent bank record

## Test 5 --- Missing Ledger

-   [ ] 🔴 Search transaction
-   [ ] 🔴 Gateway displayed
-   [ ] 🔴 Bank displayed
-   [ ] 🔴 Ledger marked missing
-   [ ] 🔴 Exception displayed

## Test 6 --- Duplicate

-   [ ] 🔴 Search transaction
-   [ ] 🔴 Duplicate detected
-   [ ] 🔴 Conflict explained

## Test 7 --- Timestamp Error

-   [ ] 🔴 Search transaction
-   [ ] 🔴 Chronological inconsistency detected
-   [ ] 🔴 Evidence displayed

## Test 8 --- Systemic Incident

-   [ ] 🟠 Search transaction belonging to incident
-   [ ] 🟠 Incident banner appears
-   [ ] 🟠 Affected count is correct
-   [ ] 🟠 Affected value is correct
-   [ ] 🟠 Common bank shown
-   [ ] 🟠 Common gateway shown
-   [ ] 🟠 Dominant error shown
-   [ ] 🟠 Time window shown
-   [ ] 🟠 Detection reasons shown
-   [ ] 🟠 Affected transactions listed

------------------------------------------------------------------------

# PHASE 15 --- UI Polish

Only begin after functionality is stable.

-   [ ] 🟢 Improve typography
-   [ ] 🟢 Improve spacing
-   [ ] 🟢 Improve status indicators
-   [ ] 🟢 Add subtle transitions
-   [ ] 🟢 Improve timeline
-   [ ] 🟢 Improve confidence visualization
-   [ ] 🟢 Improve incident banner
-   [ ] 🟢 Add empty states
-   [ ] 🟢 Add loading skeletons
-   [ ] 🟢 Make dashboard presentation-ready

------------------------------------------------------------------------

# PHASE 16 --- Documentation

-   [ ] 🔴 Write README
-   [ ] 🔴 Add installation instructions
-   [ ] 🔴 Add environment-variable instructions
-   [ ] 🔴 Add backend startup instructions
-   [ ] 🔴 Add frontend startup instructions
-   [ ] 🔴 Explain architecture
-   [ ] 🔴 Explain synthetic data
-   [ ] 🔴 Explain AI safety/grounding
-   [ ] 🟠 Add screenshots
-   [ ] 🟠 Add demo walkthrough

Create:

``` text
docs/architecture.md
docs/api.md
docs/demo.md
```

------------------------------------------------------------------------

# PHASE 17 --- Final Demo Hardening

## Freeze the feature set.

Do NOT add new features after this point unless something is broken.

### Demo preparation

-   [ ] 🔴 Regenerate final dataset
-   [ ] 🔴 Verify demo IDs
-   [ ] 🔴 Start backend
-   [ ] 🔴 Start frontend
-   [ ] 🔴 Test Normal scenario
-   [ ] 🔴 Test Bank Delay scenario
-   [ ] 🔴 Test Amount Mismatch scenario
-   [ ] 🟠 Test Systemic Incident scenario
-   [ ] 🔴 Verify no console errors
-   [ ] 🔴 Verify no backend errors
-   [ ] 🔴 Verify API key works
-   [ ] 🔴 Verify LLM fallback
-   [ ] 🔴 Verify all buttons
-   [ ] 🔴 Verify presentation screen resolution

### Final Git checkpoint

``` text
v-final
```

------------------------------------------------------------------------

# FINAL DEMO SCRIPT

## Scene 1 --- Individual problem

Say:

> "A merchant asks why this settlement wasn't processed."

Enter:

``` text
TXN10087
```

Show:

``` text
Gateway    ✓
Bank       ⚠
Ledger     ✓
```

## Scene 2 --- Evidence

Show:

``` text
14:33 Settlement initiated
14:45 Expected settlement
16:17 Actual settlement
16:18 Ledger posted
```

Say:

> "The system doesn't just guess the reason. It reconstructs the
> evidence trail."

## Scene 3 --- Explanation

Show:

``` text
Settlement delayed by 92 minutes
Confidence: 94%
```

Show evidence and exceptions.

## Scene 4 --- The differentiator

Show:

``` text
⚠ This transaction appears to be part
  of a larger settlement incident.
```

Click:

``` text
VIEW INCIDENT
```

## Scene 5 --- Systemic intelligence

Show:

``` text
417 transactions affected
₹28.4L affected
BANK_X
GATEWAY_Y
14:00–16:00
BANK_TIMEOUT
```

Say:

> "This is where we go beyond a transaction chatbot. The system
> identifies that this individual failure is a symptom of a larger
> operational incident."

## Scene 6 --- Merchant response

Ask:

> "What should I tell the merchant?"

Show a concise AI-generated explanation.

------------------------------------------------------------------------

# PRIORITY IF TIME RUNS OUT

## If only 6 hours remain

Build:

1.  🔴 Data
2.  🔴 Investigator
3.  🔴 FastAPI
4.  🔴 React investigation page
5.  🔴 AI explanation
6.  🔴 Evidence/confidence
7.  🔴 Demo scenarios

Skip systemic UI if necessary.

## If 4 hours remain

Build only:

1.  Data
2.  Investigator
3.  FastAPI
4.  Basic React UI
5.  AI explanation

## If 2 hours remain

STOP adding features.

Fix:

-   API
-   data
-   UI
-   demo

## If everything is working

Do NOT refactor the entire project.

Do NOT introduce new frameworks.

Do NOT add a database.

Do NOT add authentication.

Do NOT add multi-agent architecture.

Polish the demo instead.
