# Settlement Intelligence --- Product Requirements Document

## 1. Product Overview

**Project:** Settlement Intelligence\
**Category:** AI + Development / Fintech Support\
**Primary goal:** Automate settlement investigation across gateway,
bank, and ledger data, then identify whether individual settlement
failures are part of a larger systemic incident.

### Product vision

Settlement Intelligence is an AI-powered investigation and operations
system that:

1.  Traces an individual transaction across gateway, bank, and ledger
    records.
2.  Reconciles the records and identifies discrepancies.
3.  Produces an evidence-backed explanation in plain English.
4.  Quantifies investigation confidence and explicitly reports
    missing/conflicting evidence.
5.  Detects patterns across many transactions that indicate a systemic
    settlement incident.
6.  Connects an individual transaction to a larger incident when
    appropriate.

### Core product statement

> We do not just explain why one settlement failed. We determine whether
> that failure is part of a bigger problem.

------------------------------------------------------------------------

# 2. Problem Statement

Businesses may contact fintech support with questions such as:

> "Why wasn't my settlement processed?"

The information required to answer this question may be distributed
across:

-   Payment gateway records
-   Bank records
-   Internal ledger records

A support agent may have to manually locate the transaction in each
system, compare amounts and timestamps, determine what happened, and
communicate the result.

Settlement Intelligence automates this workflow using synthetic gateway,
bank, and ledger datasets.

------------------------------------------------------------------------

# 3. Target Users

## 3.1 Support Agent

Needs to investigate a transaction quickly and provide a clear
explanation to a merchant.

Primary needs:

-   Search transaction ID
-   See gateway/bank/ledger status
-   Understand delay or failure reason
-   See supporting evidence
-   Know what information is missing
-   Generate a merchant-facing explanation

## 3.2 Operations Team

Needs to understand whether settlement problems are isolated or
systemic.

Primary needs:

-   Monitor transaction health
-   Detect unusual failure/delay patterns
-   Identify affected banks/gateways
-   Estimate affected transaction count and settlement value
-   Investigate incidents
-   Drill down from an incident to individual transactions

------------------------------------------------------------------------

# 4. Product Scope

## In scope

-   Synthetic CSV datasets
-   Transaction investigation
-   Gateway/bank/ledger reconciliation
-   Delay calculation
-   Anomaly detection
-   Evidence generation
-   Confidence scoring
-   Plain-English AI explanation
-   Similar transaction detection
-   Systemic pattern detection
-   Incident generation
-   System Health dashboard
-   Incident drill-down
-   Demo scenarios

## Out of scope

-   Real payment processing
-   Real banking APIs
-   Real customer data
-   Production financial transactions
-   Authentication
-   Payment execution
-   Production database infrastructure
-   Kubernetes/Docker/microservices
-   RAG/vector database
-   Fine-tuning
-   Complex ML
-   Multi-agent architecture unless specifically required later

------------------------------------------------------------------------

# 5. Product Modes

The application has two connected modes.

## Mode A --- Transaction Investigation

Answers:

> "What happened to this transaction?"

Flow:

Transaction ID → Gateway → Bank → Ledger → Reconciliation → Evidence →
Root cause → Confidence → Explanation

## Mode B --- System Intelligence

Answers:

> "Is there a larger problem?"

Flow:

All transactions → Pattern analysis → Anomaly concentration → Incident
detection → Affected transactions → Individual investigation

------------------------------------------------------------------------

# 6. Functional Requirements

## FR-01 --- Transaction Search

The user must be able to enter a transaction ID.

Example:

`TXN10087`

The frontend sends the ID to the backend.

The backend returns the investigation result.

------------------------------------------------------------------------

## FR-02 --- Gateway Investigation

The system must search the gateway dataset for the transaction.

Relevant information includes:

-   Transaction ID
-   Gateway reference
-   Merchant ID
-   Amount
-   Currency
-   Payment method
-   Gateway status
-   Initiated timestamp
-   Captured timestamp
-   Settlement initiation timestamp
-   Response code
-   Response message

If the record does not exist, it must be explicitly marked as missing.

------------------------------------------------------------------------

## FR-03 --- Bank Investigation

The system must search the bank dataset.

Relevant information includes:

-   Transaction ID
-   Bank reference
-   Bank name
-   Amount
-   Bank status
-   Received timestamp
-   Expected settlement timestamp
-   Actual settlement timestamp
-   Response code
-   Response message

Missing records must be explicitly reported.

------------------------------------------------------------------------

## FR-04 --- Ledger Investigation

The system must search the ledger dataset.

Relevant information includes:

-   Transaction ID
-   Ledger entry ID
-   Amount
-   Ledger status
-   Created timestamp
-   Settlement date
-   Reconciliation status

Missing records must be explicitly reported.

------------------------------------------------------------------------

## FR-05 --- Cross-System Reconciliation

The backend must compare available records.

Minimum comparisons:

-   Transaction IDs
-   Amounts
-   Statuses
-   Timestamps
-   Settlement information
-   Response codes
-   References where relevant

The system must identify:

-   Matching records
-   Amount mismatches
-   Missing records
-   Conflicting statuses
-   Timestamp inconsistencies
-   Duplicate records
-   Settlement delays

------------------------------------------------------------------------

# 7. Transaction Status Model

The investigation engine may classify transactions as:

-   `SUCCESS`
-   `DELAYED`
-   `FAILED`
-   `PARTIAL`
-   `MISMATCH`
-   `MISSING_DATA`
-   `CONFLICTING`

The final status must be derived from evidence, not invented by the LLM.

------------------------------------------------------------------------

# 8. Anomaly Types

The synthetic dataset must contain controlled examples of:

## 8.1 Normal

Gateway, bank, and ledger records agree.

## 8.2 Bank Settlement Delay

Bank settlement happens after the expected settlement time.

## 8.3 Amount Mismatch

Example:

Gateway: ₹5,000\
Bank: ₹4,800\
Ledger: ₹5,000

## 8.4 Missing Bank Record

Gateway exists but the expected bank record is missing.

## 8.5 Missing Ledger Record

Gateway and bank exist but ledger confirmation is missing.

## 8.6 Duplicate Transaction

More than one record exists where only one is expected.

## 8.7 Timestamp Inconsistency

Records contain an impossible or suspicious chronological sequence.

## 8.8 Systemic Incident

Many transactions share a common failure characteristic such as:

-   Same bank
-   Same gateway
-   Same response code
-   Same time window
-   Similar failure/delay behavior

------------------------------------------------------------------------

# 9. Evidence Engine

The backend must construct a structured evidence trail.

Example:

-   Gateway settlement initiated: 14:33
-   Expected bank settlement: 14:45
-   Actual bank settlement: 16:17
-   Ledger posted: 16:18

The UI must display evidence separately from the AI-generated
explanation.

------------------------------------------------------------------------

# 10. Confidence System

Confidence must be calculated deterministically.

Suggested scoring:

  Evidence                    Score
  ----------------------- ---------
  Gateway record found          +20
  Bank record found             +20
  Ledger record found           +20
  Amounts match                 +15
  Timestamps consistent         +10
  Statuses consistent           +10
  Known response code            +5
  **Maximum**               **100**

Suggested interpretation:

-   95--100: Very High
-   75--94: High
-   50--74: Medium
-   Below 50: Low

The LLM must not generate or override this score.

------------------------------------------------------------------------

# 11. Exception Handling

The system must explicitly identify uncertainty.

Examples:

### Missing ledger

> Ledger confirmation could not be established because no matching
> ledger record was found.

### Amount mismatch

> Gateway amount is ₹5,000 while bank amount is ₹4,800.

### Conflicting records

> Available records contain conflicting information. A definitive root
> cause cannot be established.

The system must never claim certainty when evidence is insufficient.

------------------------------------------------------------------------

# 12. AI Requirements

The LLM is an explanation/orchestration layer, not the source of truth.

The AI may:

-   Interpret user requests
-   Summarize structured evidence
-   Explain root causes
-   Generate merchant-facing explanations
-   Explain exceptions
-   Summarize systemic incidents

The AI must:

1.  Use only backend-provided evidence.
2.  Never invent records.
3.  Never invent amounts.
4.  Never invent timestamps.
5.  Never claim a missing record exists.
6.  Never override deterministic calculations.
7.  Clearly distinguish confirmed facts from possibilities.
8.  Preserve backend confidence.

------------------------------------------------------------------------

# 13. Structured AI Output

Target schema:

``` json
{
  "status": "DELAYED",
  "summary": "Settlement was delayed by 92 minutes due to delayed bank processing.",
  "root_cause": "BANK_PROCESSING_DELAY",
  "confidence": 94,
  "evidence": [
    "Gateway settlement initiated at 14:33",
    "Expected bank settlement was 14:45",
    "Actual bank settlement occurred at 16:17"
  ],
  "exceptions": [],
  "recommended_action": "Inform the merchant that settlement was completed late due to bank processing delay."
}
```

The backend should validate the structure before returning it to the
frontend.

------------------------------------------------------------------------

# 14. Timeline

The UI should display a chronological transaction timeline.

Example:

``` text
14:32  Payment captured
14:33  Settlement initiated
14:45  Expected bank settlement
16:17  Bank settlement completed
16:18  Ledger posted
```

The backend should calculate delay values from timestamps.

------------------------------------------------------------------------

# 15. Similar Transaction Detection

For an investigated transaction, the system should identify transactions
with similar characteristics.

Potential similarity dimensions:

-   Bank
-   Gateway
-   Response code
-   Status
-   Time window
-   Amount range

Example:

> 39 similar transactions found.

Common pattern:

-   Bank: BANK_X
-   Gateway: GATEWAY_Y
-   Error: BANK_TIMEOUT
-   Time: 14:00--16:00

------------------------------------------------------------------------

# 16. Systemic Incident Detection

The systemic analyzer must analyze the complete dataset.

It should detect unusual concentrations or spikes involving:

-   Banks
-   Gateways
-   Response codes
-   Time windows
-   Amount ranges
-   Merchant IDs where useful
-   Failure/delay rates
-   Affected settlement value

Example incident:

``` text
INCIDENT DETECTED

417 transactions affected
₹28.4L settlement value affected

Primary bank: BANK_X
Primary gateway: GATEWAY_Y
Peak period: 14:00–16:00
Dominant error: BANK_TIMEOUT
```

The incident should also contain reasons for detection.

------------------------------------------------------------------------

# 17. Transaction-to-Incident Association

When an investigated transaction matches an incident's defining
characteristics, the result should include an incident association.

Example:

> This transaction appears to be part of a larger settlement incident.

The user should be able to open the incident from the transaction page.

------------------------------------------------------------------------

# 18. UI Requirements

The product must look like a fintech operations platform, not a generic
chatbot.

## Main navigation

-   Transaction Investigation
-   System Health
-   Incidents

## Transaction Investigation page

Required components:

-   Transaction search bar
-   Investigate button
-   Gateway card
-   Bank card
-   Ledger card
-   Timeline
-   AI investigation summary
-   Confidence indicator
-   Evidence panel
-   Exceptions panel
-   Similar transactions
-   Incident association
-   Agent activity/status

## System Health page

Show:

-   Total transactions
-   Successful transactions
-   Failed transactions
-   Delayed transactions
-   Total settlement value
-   Detected incidents
-   Failure/delay trends
-   Bank breakdown
-   Gateway breakdown
-   Response-code breakdown

## Incident page

Show:

-   Incident title
-   Severity
-   Affected transaction count
-   Affected settlement value
-   Primary bank
-   Primary gateway
-   Time window
-   Dominant error
-   Detection reasons
-   Affected transactions
-   Link to investigate each transaction

------------------------------------------------------------------------

# 19. Demo Scenarios

Create deterministic demo cases:

``` json
{
  "normal": "TXN10001",
  "bank_delay": "TXN10087",
  "amount_mismatch": "TXN10142",
  "missing_bank": "TXN10211",
  "missing_ledger": "TXN10304",
  "duplicate": "TXN10482",
  "timestamp_error": "TXN10531",
  "systemic_incident": "TXN10087"
}
```

The actual IDs may differ, but the mapping must be generated and stored
in `demo_cases.json`.

------------------------------------------------------------------------

# 20. Data Requirements

Generate approximately 1,000 synthetic transactions.

Use a fixed random seed so the data is reproducible.

Create:

-   `data/gateway.csv`
-   `data/bank.csv`
-   `data/ledger.csv`
-   `data/demo_cases.json`

Normal transactions should be internally consistent.

Anomalies should be intentionally injected.

The frontend must never contain hardcoded fake transaction responses.

------------------------------------------------------------------------

# 21. Non-Functional Requirements

## Reliability

The deterministic investigator must work even if the LLM API is
unavailable.

## Explainability

Every conclusion should be traceable to evidence.

## Reproducibility

Synthetic data must be reproducible using a fixed random seed.

## Simplicity

The architecture must remain appropriate for an overnight hackathon.

## Local Development

The entire project must run locally.

------------------------------------------------------------------------

# 22. Primary Demo Flow

1.  Open Settlement Intelligence.
2.  Search `TXN10087`.
3.  Show gateway, bank, and ledger investigation.
4.  Show timeline.
5.  Show delayed settlement explanation.
6.  Show confidence and evidence.
7.  Show: \> This transaction appears to be part of a larger settlement
    incident.
8.  Open the incident.
9.  Show affected transactions and affected value.
10. Explain the common bank/gateway/error/time pattern.
11. Ask AI: \> What should I tell the merchant?
12. Show a concise merchant-facing response.

------------------------------------------------------------------------

# 23. Product Success Criteria

A judge should be able to understand the product without technical
explanation.

The complete demo should demonstrate:

**Transaction → Evidence → Root Cause → Confidence → Systemic Pattern →
Incident**

The product should feel like a financial operations intelligence system
rather than an LLM wrapper.
