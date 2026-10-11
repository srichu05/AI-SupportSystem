# API Specification Contract (v1.0.0)
## Project: PolicyPulse AI — Intelligent Customer Complaint Response Assistant
**Team**: TENSOR TITANS | PS-40

---

## 1. Specification Overview
This document serves as the formal REST API contract between the presentation layer (React/Vite) and the backend orchestration layer (FastAPI). All endpoints use standard HTTP status codes and JSON payloads.

Base URL (Local): `http://127.0.0.1:8000`  
Base URL (Production): `https://policypulse-api.onrender.com`  
Prefix: `/api/v1`

---

## 2. Common Types & Enums

### 2.1 Issue Coverage Status
```typescript
type IssueCoverageStatus = 
  | "covered"
  | "partially_covered"
  | "uncovered"
  | "prohibited"
  | "conflict"
  | "needs_human_review";
```

### 2.2 Tone Preset
```typescript
type TonePreset = "empathetic" | "concise" | "formal";
```

### 2.3 Guardrail Status
```typescript
type GuardrailVerdict = "PASSED" | "FLAGGED";
```

---

## 3. Endpoints

### 3.1 Health Check
- **Endpoint**: `GET /api/v1/health`
- **Description**: Verifies backend availability, database connection, and vector search readiness.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "database_connected": true,
  "vector_search_ready": true,
  "timestamp": "2026-10-10T12:00:00Z"
}
```

---

### 3.2 Analyze Complaint
- **Endpoint**: `POST /api/v1/complaints/analyze`
- **Description**: Decomposes a multi-issue complaint, retrieves grounded policy chunks via hybrid RRF search, validates against unauthorized commitment guardrails, and produces a grounded response draft.
- **Request Body**:
```json
{
  "complaint_id": "CMP-2026-9042",
  "customer_id": "CUST-8102",
  "customer_name": "Eleanor Vance",
  "channel": "email",
  "raw_text": "I received my order #48192 three days late, and when I opened the box, the espresso machine was dented and leaking water. Your delivery driver was dismissive and refused to note the damage on the receipt. I demand an immediate full refund and a $100 gift card for my trouble.",
  "tone_preference": "empathetic"
}
```

- **Response `200 OK`**:
```json
{
  "complaint_id": "CMP-2026-9042",
  "analysis_timestamp": "2026-10-10T12:00:02Z",
  "overall_sentiment": "negative",
  "overall_severity": "high",
  "decomposed_concerns": [
    {
      "concern_id": "CONC-1",
      "category": "Damaged Merchandise",
      "summary": "Espresso machine delivered with exterior dent and internal water leak.",
      "severity": "high",
      "status": "covered",
      "citations": [
        {
          "citation_id": "CIT-POL-01-SEC-3",
          "document_title": "Enterprise Refund & Return Policy v2.4",
          "clause_id": "Clause 3.2 (Transit Damage)",
          "section_name": "Section 3: Damaged or Defective Items",
          "page_number": 4,
          "excerpt": "Goods damaged during transit are eligible for an immediate replacement or full refund upon submission of photographic evidence within 14 days of delivery receipt.",
          "confidence_score": 0.94
        }
      ]
    },
    {
      "concern_id": "CONC-2",
      "category": "Delivery Delay",
      "summary": "Package delivered 3 days past scheduled delivery date.",
      "severity": "medium",
      "status": "partially_covered",
      "citations": [
        {
          "citation_id": "CIT-POL-04-SEC-2",
          "document_title": "Shipping & Fulfillment SLA v1.8",
          "clause_id": "Clause 2.1 (Standard Delay Recourse)",
          "section_name": "Section 2: Delivery Guarantees",
          "page_number": 2,
          "excerpt": "For carrier delays exceeding 48 hours beyond the guaranteed window, standard shipping charges shall be credited to the customer account.",
          "confidence_score": 0.88
        }
      ]
    },
    {
      "concern_id": "CONC-3",
      "category": "Courier Demeanor",
      "summary": "Delivery agent was dismissive and declined to record transit damage.",
      "severity": "low",
      "status": "needs_human_review",
      "citations": [
        {
          "citation_id": "CIT-POL-09-SEC-1",
          "document_title": "Courier Partner Code of Conduct v3.1",
          "clause_id": "Clause 1.4 (Driver Escalation Protocol)",
          "section_name": "Section 1: Service Quality",
          "page_number": 1,
          "excerpt": "Courier behavioral complaints are logged to the 3PL Logistics Partner Council for formal review within 5 business days.",
          "confidence_score": 0.79
        }
      ]
    },
    {
      "concern_id": "CONC-4",
      "category": "Inconvenience Compensation",
      "summary": "Customer demanded an unprompted $100 gift card compensation.",
      "severity": "medium",
      "status": "prohibited",
      "citations": [
        {
          "citation_id": "CIT-POL-01-SEC-7",
          "document_title": "Enterprise Refund & Return Policy v2.4",
          "clause_id": "Clause 7.1 (Discretionary Goodwill Limits)",
          "section_name": "Section 7: Consequential Goodwill & Credit",
          "page_number": 9,
          "excerpt": "Goodwill store credits exceeding $25 require written authorization from a Support Operations Director and may not be promised by frontline agents.",
          "confidence_score": 0.96
        }
      ]
    }
  ],
  "guardrail_report": {
    "verdict": "FLAGGED",
    "unsupported_commitments_detected": [
      {
        "claim": "Demand for $100 gift card compensation",
        "reason": "Exceeds authorized frontline discretionary credit threshold ($25). Promise blocked by Clause 7.1.",
        "severity": "CRITICAL"
      }
    ],
    "policy_conflicts_detected": [],
    "policy_gaps_detected": []
  },
  "grounded_draft": {
    "tone": "empathetic",
    "subject": "Regarding your order #48192 — Resolution & Next Steps",
    "body": "Dear Eleanor,\n\nThank you for reaching out to us. I sincerely apologize for the frustration caused by the delay in your shipment, the damaged condition of your espresso machine, and the unacceptable interaction with the courier.\n\nPer our Damaged Merchandise Policy (Clause 3.2), we are ready to initiate an immediate replacement or full refund for your espresso machine once we receive photos of the damage. Additionally, under our Shipping SLA (Clause 2.1), we have refunded the standard shipping fee for the carrier delay.\n\nRegarding the courier conduct, we have logged a formal review with our logistics partner under Clause 1.4. While company policy limits discretionary goodwill credits to authorized thresholds and does not support third-party gift card allocations, our primary focus is ensuring your damaged appliance is replaced immediately without additional expense to you.\n\nPlease reply with photos of the damaged unit so we can process your dispatch today.",
    "anchored_clause_ids": [
      "Clause 3.2 (Transit Damage)",
      "Clause 2.1 (Standard Delay Recourse)",
      "Clause 1.4 (Driver Escalation Protocol)",
      "Clause 7.1 (Discretionary Goodwill Limits)"
    ]
  },
  "human_review_required": true,
  "review_reasons": [
    "High severity product transit damage",
    "Prohibited goodwill demand flagged by guardrails",
    "Courier conduct triage required"
  ]
}
```

---

### 3.3 List Policies
- **Endpoint**: `GET /api/v1/policies`
- **Description**: Returns all enterprise policy manuals indexed in the vector and full-text database.
- **Response `200 OK`**:
```json
[
  {
    "policy_id": "POL-REFUND-2026",
    "title": "Enterprise Refund & Return Policy",
    "version": "v2.4",
    "updated_at": "2026-09-15T00:00:00Z",
    "total_chunks": 48,
    "status": "active"
  },
  {
    "policy_id": "POL-SHIPPING-2026",
    "title": "Shipping & Fulfillment SLA",
    "version": "v1.8",
    "updated_at": "2026-08-20T00:00:00Z",
    "total_chunks": 24,
    "status": "active"
  },
  {
    "policy_id": "POL-WARRANTY-2026",
    "title": "Hardware Warranty & Defect Terms",
    "version": "v3.0",
    "updated_at": "2026-07-01T00:00:00Z",
    "total_chunks": 62,
    "status": "active"
  }
]
```

---

### 3.4 Upload Policy Manual
- **Endpoint**: `POST /api/v1/policies/upload`
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `file`: PDF or Markdown file.
  - `title`: String.
  - `version`: String.
- **Response `201 Created`**:
```json
{
  "policy_id": "POL-NEW-910",
  "title": "Hardware Warranty & Defect Terms",
  "version": "v3.1",
  "chunks_created": 34,
  "status": "indexed"
}
```

---

### 3.5 Dispatch / Approve Complaint Response
- **Endpoint**: `POST /api/v1/complaints/dispatch`
- **Description**: Submits the final human-verified response for external ticketing dispatch. Validates that human approval was granted and logs the action to compliance audit records.
- **Request Body**:
```json
{
  "complaint_id": "CMP-2026-9042",
  "agent_id": "AGENT-042",
  "agent_name": "Marcus Aurelius",
  "action": "APPROVE",
  "final_text": "Dear Eleanor, Thank you for reaching out...",
  "notes": "Verified transit damage photos uploaded to case files. Shipping fee waived.",
  "override_reasons": []
}
```

- **Response `200 OK`**:
```json
{
  "dispatch_id": "DISP-8842-SIMULATED",
  "complaint_id": "CMP-2026-9042",
  "status": "SIMULATED_DISPATCH",
  "dispatched_at": "2026-10-10T12:05:00Z",
  "audit_log_id": "AUDIT-SIMULATED-9921",
  "delivery_channel": "SIMULATED_LOCAL_DEMO"
}
```

---

### 3.6 Conversations & Interactive Sessions
- `GET /api/v1/conversations`: Returns recent ticket conversations.
- `POST /api/v1/conversations/{id}/messages`: Appends customer or agent messages to an active thread.

---

## 4. Error Codes & Structured Error Response
```json
{
  "error": {
    "code": "UNAUTHORIZED_COMMITMENT_DETECTED",
    "message": "The proposed text contains an unauthorized financial promise not grounded in active policy.",
    "details": {
      "clause_violated": "Clause 7.1",
      "flagged_token": "$100 gift card"
    }
  }
}
```
Common error codes:
- `COMPLAINT_NOT_FOUND` (`404`)
- `INVALID_TONE_PRESET` (`400`)
- `POLICY_INDEXING_FAILED` (`500`)
- `HUMAN_APPROVAL_MISSING` (`403`)
