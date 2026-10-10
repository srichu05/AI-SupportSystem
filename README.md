# Intelligent Customer Complaint Response Assistant

Internal decision-support tool for customer support teams to analyze incoming complaints, retrieve grounded company policy evidence, and assist agents in reviewing and resolving customer issues. Built with FastAPI, Supabase PostgreSQL with `pgvector`, hybrid search (semantic + full-text with Reciprocal Rank Fusion), and Google Gemini.

> **Human-in-the-Loop Guardrail:** The system is strictly a decision-support and drafting tool. It provides evidence mapping and recommendation analysis for human agents, and never automatically sends messages or commitments to customers.

---

## Core Capabilities

- **Complaint Issue Decomposition:** Multi-issue segmentation, extracting customer facts, requested resolutions, and identifying missing information.
- **Adversarial Safety & Input Sanitization:** Automatic PII masking (SSN, credit cards), system prompt injection neutralization, and untrusted input isolation.
- **Policy Ingestion Pipeline:** Multi-format parser (PDF, DOCX, TXT) with heading-aware chunking, stable UUID generation, and Supabase Storage archiving.
- **Hybrid Search & Evidence Retrieval:** Combines pgvector cosine similarity with PostgreSQL full-text search (`tsvector` + GIN indexing) fused via Reciprocal Rank Fusion ($RRF$, $k=60$).
- **Evidence-Based Policy Assessment:** Deterministic and evidence-grounded classification across 6 policy statuses: `covered`, `partially_covered`, `uncovered`, `prohibited`, `conflict`, and `needs_human_review`.
- **Review Decision & Audit Logging:** Immutable audit records of drafts, supervisor escalations, and human decisions (`approved`, `rejected`, `escalated`).

---

## Architecture Overview

- **Framework:** FastAPI with modular routing, dependency injection, and centralized error handling
- **Database & Storage:** Supabase PostgreSQL with `pgvector` extension and private Supabase Storage buckets
- **Embeddings & LLM:** Google Gemini hosted embeddings (`gemini-embedding-2`, 768 dimensions) and generation
- **ORM & Migrations:** SQLAlchemy 2.0 with Alembic version-controlled migrations
- **Validation:** Pydantic v2 schemas adhering to strict API contract envelopes
- **Security:** Zero secret leakage in logs, CORS origin controls, sensitive data logging filters

---

## Local Setup & Quickstart

### 1. Prerequisites
- Python 3.11+ (Python 3.13 supported)
- Git

### 2. Environment Setup
```bash
# Clone or navigate to the workspace
cd "AI-SupportSystem"

# Create a virtual environment (optional but recommended)
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your credentials in `.env`:
- `DATABASE_URL`: Supabase PostgreSQL connection string (`postgresql://postgres.[REF]:[PASS]@[HOST]:5432/postgres`)
- `SUPABASE_URL`: Supabase project URL (`https://[REF].supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role secret
- `GEMINI_API_KEY`: Google Gemini API key
- `GEMINI_GENERATION_MODEL`: `gemini-2.5-flash`
- `GEMINI_EMBEDDING_MODEL`: `gemini-embedding-2`
- `EMBEDDING_DIMENSIONS`: `768`

---

## Running the Application

### Option A: From Command Line
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Option B: From VS Code
Open the project root in VS Code and press **F5** (or open the **Run & Debug** tab and choose **FastAPI: Run Backend**).

---

## Database Migrations (Supabase PostgreSQL)

Apply the initial database schema (creates `vector` extension, tables, constraints, and GIN full-text indexes):

```bash
# Apply migrations online to configured database
python -m alembic upgrade head

# Generate offline SQL script for inspection or Supabase SQL Editor
python -m alembic upgrade 20261010_0001 --sql
```

---

## Diagnostics & Verification Scripts

Run the diagnostic smoke tests:

```bash
# 1. Verify Gemini models, embedding dimensions (768), and Supabase Storage
python backend/scripts/verify_providers.py

# 2. Verify Supabase PostgreSQL connectivity
python backend/scripts/verify_db.py
```

---

## Running the Test Suite

```bash
python -m pytest backend/tests -v
```

Automated tests (75 total test cases) cover:
- FastAPI startup and life-cycle events
- Health endpoints (`/health`, `/health/db`, `/health/providers`)
- Policy extraction, heading-aware chunking, and file validation
- Hybrid retrieval (pgvector + FTS) and Reciprocal Rank Fusion
- Complaint analysis, PII masking, and prompt injection defense
- Policy status classification (`covered`, `prohibited`, `conflict`, `needs_human_review`)
- Evidence-grounded response drafting and citation verification
- Deterministic response validation (commitment checking, monetary invention prevention, citation validation)
- Tone variation consistency (`professional`, `empathetic`, `concise`)
- Human review workflow (approve, reject, escalate, edit audit history, and customer dispatch invariant)
- API contracts and Pydantic schemas
- Database models, unique constraints, and cascade deletes
- Centralized error envelope formatting and traceback protection

---

## Evaluation & Dataset Validation

Run evaluation against standard benchmarks and adversarial test cases:

```bash
# Evaluate complaint decomposition, evidence mapping, and safety invariants
python backend/scripts/evaluate_complaint_analysis.py

# Validate policy datasets and raw complaints
python scripts/validate_data.py
```

---

## API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Basic process liveness check (`{"status": "ok"}`) |
| `GET` | `/health/db` | Database connectivity check (`SELECT 1`) |
| `GET` | `/health/providers` | External provider status (Gemini, Supabase) |
| `POST` | `/api/v1/policies` | Policy file upload (`.pdf`, `.docx`, `.txt`) with chunking & embedding |
| `GET` | `/api/v1/policies` | List active policy documents |
| `GET` | `/api/v1/policies/{id}` | Inspect policy document metadata and chunks |
| `POST` | `/api/v1/complaints` | Intake complaint, analyze issues, map evidence, and assess policy coverage |
| `GET` | `/api/v1/complaints/{id}` | Retrieve complaint, issues, mapped evidence, and assessment |
| `POST` | `/api/v1/complaints/{id}/review` | Human review decision (`approved`, `rejected`, `escalated`) |
| `GET` | `/api/v1/complaints/{id}/history` | Audit trail of drafts and review decisions |

> **Safety Notice:** Review decisions recorded via `/review` record the agent's audit decision only and never trigger automatic customer messages.
