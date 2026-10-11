# PolicyPulse AI
> **Intelligent Customer Complaint Response Assistant Grounded in Enterprise Policy**  

[![Stack](https://img.shields.io/badge/Stack-React%20%7C%20Vite%20%7C%20TypeScript%20%7C%20TailwindCSS-blue)](#)
[![Backend](https://img.shields.io/badge/Backend-Python%20%7C%20FastAPI%20%7C%20Pydantic-green)](#)
[![Database](https://img.shields.io/badge/Data-Supabase%20%7C%20pgvector%20%7C%20Postgres%20FTS-emerald)](#)
[![Safety](https://img.shields.io/badge/Guardrails-Human--in--the--Loop%20%7C%20Zero%20Unauthorized%20Commitments-red)](#)

---

## 1. Executive Overview

Support teams lose critical hours manually cross-referencing customer complaints with fragmented enterprise policy manuals. When generic LLMs are deployed, they frequently hallucinate or make **unauthorized financial and contractual commitments** (e.g., unauthorized refunds, warranty waivers) that incur severe corporate liability.

**PolicyPulse AI** solves this with an enterprise-grade AI co-pilot designed for customer support teams:
1. **Multi-Concern Decomposition**: Breaks complex, emotionally charged grievances into atomic sub-issues.
2. **Hybrid Policy Retrieval (RRF)**: Merges dense vector embeddings (`pgvector`) with lexical full-text search (`tsvector`) via Reciprocal Rank Fusion ($k=60$).
3. **Transparent Evidence Citations**: Direct clause references (`Clause 3.2`, page numbers, exact excerpts) ground every response claim.
4. **Unsupported-Commitment Blocker**: Deterministic guardrails flag unauthorized monetary or exception promises before agent dispatch.
5. **Tone Customization Engine**: Switch seamlessly between *Empathetic*, *Concise*, and *Formal* styles without altering policy bounds.
6. **Human-in-the-Loop Studio**: Agents inspect evidence, edit drafts, verify guardrails, and authorize final dispatch.

---

## 2. Architecture & Technology Stack

```
Frontend (Vercel)                    Backend (Render)                    Database & Storage (Supabase)
┌───────────────────────────┐        ┌───────────────────────────┐       ┌───────────────────────────┐
│ React 18 + Vite + TS      │ ◄────► │ FastAPI (Python 3.11)     │ ◄───► │ Supabase PostgreSQL 15    │
│ Tailwind CSS + shadcn/ui  │  JSON  │ Pydantic v2 Models        │  SQL  │ pgvector (HNSW Index)     │
│ Lucide React Icons        │  REST  │ Hybrid RRF Retriever      │       │ PostgreSQL FTS (GIN Index)│
│ Landing Page + Workspace  │        │ Commitment Guardrails     │       │ Storage (Policy Documents)│
└───────────────────────────┘        └───────────────────────────┘       └───────────────────────────┘
```

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, Lucide React.
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2.
- **Database & Retrieval**: Supabase PostgreSQL 15, `pgvector` (HNSW indexing), PostgreSQL Full-Text Search, Reciprocal Rank Fusion.
- **Target Deployments**: Frontend on Vercel, Backend on Render, Database on Supabase.

---

## 3. Repository Structure

```
├── API_SPEC.md              # Formal REST API contract & schemas
├── ARCHITECTURE.md          # Multi-layer system design & topology
├── DATABASE_SCHEMA.md       # PostgreSQL DDL, pgvector indexes & RRF function
├── DEPLOYMENT.md            # Cloud runbook for Vercel, Render & Supabase
├── PRD.md                   # Product Requirements Document
├── RAG_PIPELINE.md          # Chunking, hybrid retrieval & generation rules
├── README.md                # Project documentation & local run guide
├── SAFETY_AND_VALIDATION.md # Guardrails, commitment blocker & audit trail
├── TESTING_AND_EVALUATION.md# Quality benchmarks & test scenarios
├── .env.example             # Environment variables template
│
├── backend/                 # FastAPI Python backend service
│   ├── main.py              # Application entrypoint & routes
│   ├── app/
│   │   ├── models/          # Pydantic schemas (synchronized with API_SPEC.md)
│   │   ├── services/        # Decomposer, Retriever, Guardrails, Generator
│   │   └── data/            # Active policy documents & sample complaints
│   └── requirements.txt     # Python backend dependencies
│
├── src/                     # React + Vite TypeScript frontend
│   ├── components/
│   │   ├── landing/         # Marketing landing page (MotionSites visual style)
│   │   │   ├── Navbar.tsx
│   │   │   ├── HeroSection.tsx
│   │   │   ├── InteractiveDemo.tsx
│   │   │   ├── CoreCapabilities.tsx
│   │   │   ├── ProcessSection.tsx
│   │   │   ├── EvidencePanelPreview.tsx
│   │   │   └── Footer.tsx
│   │   ├── workspace/       # Agent Review Studio
│   │   │   ├── WorkspaceLayout.tsx
│   │   │   ├── TicketSidebar.tsx
│   │   │   ├── ComplaintHeader.tsx
│   │   │   ├── DecomposedConcerns.tsx
│   │   │   ├── EvidenceViewer.tsx
│   │   │   ├── GuardrailBanner.tsx
│   │   │   ├── DraftEditor.tsx
│   │   │   └── DispatchModal.tsx
│   │   └── ui/              # shadcn/ui design primitives
│   ├── services/            # Typed API client with seamless demo fallback
│   ├── types/               # TypeScript interfaces matching API_SPEC.md
│   ├── App.tsx              # Root application router / view controller
│   ├── main.tsx             # React entrypoint
│   └── index.css            # Tailwind directives & design tokens
│
├── index.html               # HTML entrypoint
├── package.json             # Frontend dependencies & scripts
├── tailwind.config.js       # Tailwind theme & animation configuration
├── tsconfig.json            # TypeScript configuration
└── vite.config.ts           # Vite build configuration
```

---

## 4. Local Quickstart Guide

### Prerequisites
- **Node.js**: v18+ (tested on v22.20.0)
- **npm**: v9+ (tested on 10.9.3)
- **Python**: v3.10+ (for backend)

### Step 1: Clone & Configure
```bash
cd /Users/sandeshj/Downloads/Hackathon/AI_Assistant-customer_support-
cp .env.example .env
```

### Step 2: Start the Frontend (React + Vite)
```bash
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.  
The application automatically starts with the **SaaS Landing Page** and connects to the **Agent Review Studio** via the `Launch Agent Studio` CTA. If the backend is not running, the frontend gracefully falls back to the rich illustrative demo engine with zero broken states.

### Step 3: (Optional) Run the Backend API
In a separate terminal:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```
API Documentation (Swagger UI) is available at **`http://localhost:8000/docs`**.

---

## 5. Key Verification Flows

1. **Landing Page Experience**:
   - Inspect the editorial typography, dark luxury aesthetic, and floating navbar.
   - Interact with the **Live Complaint Analyzer** directly on the hero.
   - Click `Launch Agent Studio` or `Explore How It Works`.
2. **Review Studio & Ticket Navigation**:
   - Select different ticket scenarios from the sidebar (e.g. *Damaged Espresso Machine with $100 Demand*, *Delayed Package*, *Wrong Item*).
   - Inspect the **Multi-Concern Decomposition** cards with coverage status (`covered`, `partially_covered`, `prohibited`).
   - Click citations to open the **Evidence Viewer** showing exact policy clause excerpts and page numbers.
   - Observe the **Unsupported Commitment Blocker** flagging unauthorized promises.
   - Switch tones (*Empathetic*, *Concise*, *Formal*) and watch the response adapt without changing policy bounds.
   - Edit the draft and perform `Approve & Dispatch` to verify the human-in-the-loop audit recording.

---

## 6. Project Deliverable Status
- [x] Documentation complete (`PRD.md`, `ARCHITECTURE.md`, `API_SPEC.md`, `DATABASE_SCHEMA.md`, `RAG_PIPELINE.md`, `SAFETY_AND_VALIDATION.md`, `TESTING_AND_EVALUATION.md`, `DEPLOYMENT.md`).
- [x] Landing page reflecting MotionSites visual language and design reference.
- [x] Functional Agent Review Studio with multi-issue decomposition and side-by-side evidence inspection.
- [x] Commitment guardrail scanner blocking unauthorized promises.
- [x] Fully typed API contracts and synchronized schemas.
- [x] Clean zero-error build verified locally.
