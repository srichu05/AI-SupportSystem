# Deployment Guide

## Vercel + Render + Supabase

**Status:** Deployment plan. Exact account settings and provider model
availability must be verified during setup.

## 1. Deployment layout

-   Frontend: Vercel, built from the React + Vite + TypeScript
    application.
-   Backend: Render, running the FastAPI application.
-   Database: Supabase PostgreSQL with pgvector and full-text search.
-   Original policy documents: Supabase Storage.
-   Model services: hosted Gemini API for embeddings and generation.

No local PostgreSQL, local embedding model, or FAISS index is required
by the current design.

## 2. Supabase setup

1.  Create the project and keep project credentials private.
2.  Enable the `vector` extension using the supported Supabase setup.
3.  Apply the schema and search functions using the documented migration
    process.
4.  Create a private Storage bucket for policy documents.
5.  Configure the necessary access controls/RLS for the final
    authentication model.
6.  Test insertion and retrieval of a small policy chunk and its
    embedding.
7.  Confirm vector dimensions match the verified embedding model output.
8.  Use the appropriate Supabase connection or pooler settings for the
    Render runtime.

Do not assume a connection string works with every driver/pooler mode.
Test the exact configuration used by the application.

## 3. Render backend

1.  Connect the backend repository.
2.  Configure the Python runtime and dependency installation.
3.  Configure the start command to launch the FastAPI app through the
    selected ASGI server.
4.  Add environment variables in the Render dashboard.
5.  Configure CORS to allow the deployed frontend origin.
6.  Add a health endpoint and verify it after deployment.
7.  Test the complete complaint and policy-ingestion workflow against
    Supabase.

The exact build/start commands depend on the repository layout and must
be filled in once those paths are established.

## 4. Vercel frontend

1.  Connect the frontend repository or configure the frontend root
    directory in a monorepo.
2.  Configure the Vite build command and output directory based on the
    actual project.
3.  Set the public API base URL to the deployed Render API.
4.  Redeploy after changing environment variables.
5.  Verify that API requests use HTTPS and CORS is correctly configured.

Only non-secret values such as the backend base URL should be exposed to
browser code. Never put Gemini or Supabase service-role keys in frontend
environment variables.

## 5. Environment variable plan

Names below are proposed conventions. Keep values in host
dashboards/local ignored environment files, not in source control.

Backend: - `GEMINI_API_KEY` --- provider credential. -
`GEMINI_GENERATION_MODEL` --- verified generation model ID. -
`GEMINI_EMBEDDING_MODEL` --- verified embedding model ID. -
`EMBEDDING_DIMENSIONS` --- configured output dimension, initially 768
only after verification. - `SUPABASE_URL` --- project URL. -
`SUPABASE_SERVICE_ROLE_KEY` --- server-only key if the chosen
server-side access pattern requires it; never expose to the browser. -
`DATABASE_URL` --- database connection URL if using SQLAlchemy direct
PostgreSQL access. - Any required storage bucket name or configuration.

Choose one clear database access method and avoid maintaining
duplicate/conflicting connection configurations. If a Supabase client is
used for some operations and SQLAlchemy for others, document the reason
and credential boundaries.

Frontend: - `VITE_API_BASE_URL` --- deployed backend URL. Vite-prefixed
variables are public in the built client; never place secrets here.

## 6. Secrets and security

-   Add `.env`, `.env.*` local secret files, and key files to
    `.gitignore`, while retaining a safe `.env.example` with
    placeholders.
-   Rotate any credential accidentally committed.
-   Do not log provider keys, database URLs, or service-role
    credentials.
-   Do not rely on an unguessable URL as authorization.
-   Restrict upload file types and size.
-   Use private policy storage unless public access is explicitly
    required.
-   Define authentication and authorization before real customer data is
    used.

## 7. Free-tier and operational considerations

Free-tier quotas, resource limits, pausing/sleep behaviour, and API
quotas may change. Check the current account dashboard and provider
terms before the live demo. Keep a small test corpus and pre-ingest demo
policy documents to avoid first-request delays. Do not assume model
quotas are available without testing.

## 8. Pre-demo checklist

-   [ ] Supabase extension, tables, indexes and functions exist.
-   [ ] Test policy is stored and searchable through both retrieval
    paths.
-   [ ] Embedding model ID and dimensions have been verified.
-   [ ] Gemini generation request succeeds.
-   [ ] Render health endpoint responds.
-   [ ] Vercel can call Render.
-   [ ] CORS and environment variables are correct.
-   [ ] Complaint evidence citations resolve to stored chunks.
-   [ ] Review decisions persist.
-   [ ] No automatic customer messaging occurs.
-   [ ] At least one supported, one uncovered, and one multi-issue
    scenario have been tested.
-   [ ] No secrets are present in the repository.
