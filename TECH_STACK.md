# Technology Stack and Decision Record

## Intelligent Customer Complaint Response Assistant

**Status:** Current proposed stack. Items marked "verify" are not final
until tested.

## 1. Current stack

  --------------------------------------------------------------------------
  Layer                Technology        Purpose           Status
  -------------------- ----------------- ----------------- -----------------
  Frontend             React + Vite +    Interactive web   Proposed baseline
                       TypeScript        application       

  Styling/components   Tailwind CSS +    Consistent        Proposed baseline
                       shadcn/ui         responsive UI     

  Backend              Python + FastAPI  API and workflow  Selected
                                         orchestration     direction

  Generation           Gemini API        Issue extraction  Verify exact
                                         and response      model ID/access
                                         drafting          

  Embeddings           Hosted embedding  Convert text to   Verify API access
                       API; Gemini       vectors without   and output
                       Embedding 2       local model       dimension
                       candidate         loading           

  Relational database  Supabase          Complaints,       Selected
                       PostgreSQL        policy metadata,  
                                         chunks, review    
                                         history           

  Vector search        pgvector in       Semantic          Selected
                       Supabase          similarity search 

  Keyword search       PostgreSQL        Lexical retrieval Selected
                       full-text search                    

  Hybrid ranking       Reciprocal Rank   Combine keyword   Selected
                       Fusion (RRF)      and vector result 
                                         rankings          

  File storage         Supabase Storage  Original policy   Selected
                                         files             direction

  PDF parsing          PyMuPDF           Extract PDF text  Proposed
                                         and page-level    
                                         source data       

  DOCX parsing         python-docx       Extract           Proposed
                                         paragraphs,       
                                         headings and      
                                         tables where      
                                         possible          

  TXT parsing          Python built-ins  Read text files   Proposed

  Data                 SQLAlchemy +      Python database   Proposed
  access/migrations    Alembic           access and schema 
                                         migrations        

  Validation           Pydantic +        Validate          Selected
                       deterministic     structured model  direction
                       Python rules      output and        
                                         workflow          
                                         conditions        

  Frontend hosting     Vercel            Host built        Planned
                                         frontend          

  Backend hosting      Render            Host FastAPI      Planned
                                         service           
  --------------------------------------------------------------------------

## 2. Embeddings: hosted, not local

Do not download or load a Sentence Transformers model in the Render
backend. The team specifically wants a hosted provider to reduce
model-weight download, memory, and startup overhead.

Current candidate: - Provider/API: Gemini API - Embedding model ID:
`gemini-embedding-2` - Target dimension: 768

Before implementation is considered complete, perform a real API smoke
test to verify: 1. The model ID is accepted by the API. 2. The project's
key has access and quota. 3. The response dimension is exactly the
configured dimension. 4. The provider's data-use terms are acceptable
for the data being processed. 5. The Python client and request shape
match the current official documentation.

Keep the model ID and dimensions configurable. If the provider or model
changes, re-embed every policy chunk; embeddings from different model
spaces must not be mixed in one similarity search.

## 3. Retrieval design

Use: - pgvector for semantic vector search. - PostgreSQL full-text
search for lexical matching. - RRF for fusion of ranked result lists.

Important terminology: PostgreSQL full-text ranking (for example,
`ts_rank`) is not the BM25 algorithm. The first implementation is
intentionally PostgreSQL full-text search + pgvector, not strict BM25.

No FAISS index is planned. No local PostgreSQL dependency is planned.
Development and deployment will both use Supabase because the
developer's local PostgreSQL 18 installation does not have pgvector
installed.

## 4. Database and storage

Supabase PostgreSQL is the persistent source of truth. Supabase Storage
holds original policy files. PostgreSQL should store document metadata,
chunks, embeddings, complaints, extracted issues, drafts, review
outcomes, and any audit records required by the implemented workflow.

Use database migrations and avoid relying on manually created
production-only schema changes. Never place credentials in source
control.

## 5. Alternatives considered

### Frontend

-   **React + Vite + TypeScript:** Current baseline; suitable for a
    dashboard-style SPA.
-   **Next.js:** Useful for server rendering and integrated full-stack
    patterns, but these are not essential for a dashboard backed by
    FastAPI.
-   **Vue + Vite:** Technically viable, but switching offers no
    established project-specific advantage.

### Vector retrieval

-   **pgvector:** Selected because vectors persist in the cloud database
    alongside relational data.
-   **FAISS:** Not selected because it introduces a separately managed
    index artifact/lifecycle and is unnecessary for the current
    database-centred design.

### Keyword retrieval

-   **PostgreSQL full-text search:** Selected for fewer components and
    easier database-side filtering.
-   **Strict BM25 implementation:** Not included initially because it
    adds implementation/maintenance work without demonstrated accuracy
    gains for this project. Revisit only if evaluation shows a
    meaningful need.

### Database

-   **Supabase PostgreSQL:** Selected for managed cloud persistence,
    pgvector, and related storage capabilities.
-   **Local PostgreSQL 18:** Not used as the primary development
    database because local pgvector is not installed and the team chose
    to develop against Supabase directly.
-   **SQLite:** Not selected for the deployed multi-user application.
-   **MongoDB:** Not selected; the data has clear relational
    relationships among complaints, issues, policy chunks and review
    records.

## 6. Deployment constraints

-   Frontend: Vercel.
-   Backend: Render.
-   Database and original policy files: Supabase.
-   All keys and connection strings supplied through environment
    variables.
-   Configure CORS for the deployed frontend origin.
-   Use a connection method appropriate to the Supabase/Render
    environment and connection limits.
-   Do not assume that free-tier quotas, sleep/pause behaviour, model
    quota, or provider pricing will remain unchanged. Verify current
    account settings before the demo.

## 7. Dependency discipline

Pin or constrain dependency versions in the backend dependency file
after a working install/test. Do not add OCR, rerankers, extra LLM
providers, agent frameworks, or separate search services unless required
by a tested use case.
