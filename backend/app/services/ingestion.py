import uuid
import hashlib
import logging
from datetime import date
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_session_factory
from backend.app.core.errors import (
    AppException,
    EmptyDocumentException,
    UnsupportedFileTypeException,
    DocumentExtractionException,
    ProviderUnavailableException,
)
from backend.app.models.policy import PolicyDocument, PolicyChunk
from backend.app.services.extractor import document_extractor, ExtractedDocument
from backend.app.services.chunker import policy_chunker, PolicyChunkData
from backend.app.services.gemini import gemini_service
from backend.app.services.supabase import supabase_service

logger = logging.getLogger("complaint_assistant.ingestion")


class PolicyIngestionService:
    """
    Orchestrates the full policy document ingestion lifecycle:
    1. Uploads original binary to Supabase Storage ('policy-documents' bucket)
    2. Extracts clean text and layout metadata (PyMuPDF / python-docx / txt)
    3. Generates heading-aware policy chunks with stable IDs and content hashes
    4. Computes 768-dimensional embeddings via Gemini Embedding 2
    5. Persists chunks, vectors, and status idempotently in Supabase PostgreSQL
    6. Tracks status lifecycle ('processing' -> 'active' / 'failed')
    7. Skips unchanged documents if already indexed with matching content hash
    """

    def ingest_document(
        self,
        doc_id: uuid.UUID,
        filename: str,
        content: bytes,
        source_id: Optional[str] = None,
        canonical_url: Optional[str] = None,
        version_label: Optional[str] = None,
        effective_from: Optional[date] = None,
        effective_to: Optional[date] = None,
        force_reingest: bool = False,
        db: Optional[Session] = None,
    ) -> PolicyDocument:
        """
        Synchronously ingest a policy document. If db session is not provided,
        manages its own session from the factory.
        """
        factory = get_session_factory()
        if db is None:
            if factory is None:
                raise RuntimeError("Database session factory is not available.")
            with factory() as session:
                return self._execute_ingestion(
                    session=session,
                    doc_id=doc_id,
                    filename=filename,
                    content=content,
                    source_id=source_id,
                    canonical_url=canonical_url,
                    version_label=version_label,
                    effective_from=effective_from,
                    effective_to=effective_to,
                    force_reingest=force_reingest,
                )
        else:
            return self._execute_ingestion(
                session=db,
                doc_id=doc_id,
                filename=filename,
                content=content,
                source_id=source_id,
                canonical_url=canonical_url,
                version_label=version_label,
                effective_from=effective_from,
                effective_to=effective_to,
                force_reingest=force_reingest,
            )

    def _execute_ingestion(
        self,
        session: Session,
        doc_id: uuid.UUID,
        filename: str,
        content: bytes,
        source_id: Optional[str],
        canonical_url: Optional[str],
        version_label: Optional[str],
        effective_from: Optional[date],
        effective_to: Optional[date],
        force_reingest: bool = False,
    ) -> PolicyDocument:
        ext = Path(filename).suffix.lower()
        doc_type = ext.lstrip(".").upper()
        doc_content_hash = hashlib.sha256(content).hexdigest()

        # Step 0: Check existing document record
        doc = session.query(PolicyDocument).filter(PolicyDocument.id == doc_id).first()
        if not doc:
            if source_id:
                doc = session.query(PolicyDocument).filter(PolicyDocument.source_id == source_id).first()
            if not doc:
                doc = session.query(PolicyDocument).filter(PolicyDocument.source_filename == filename).first()

        # Idempotency check: Skip if already active, has chunks, and content hash matches
        if doc and not force_reingest and doc.status == "active":
            chunk_count = session.query(PolicyChunk).filter(PolicyChunk.document_id == doc.id).count()
            if chunk_count > 0 and (doc.content_hash == doc_content_hash or (not doc.content_hash and doc.source_filename == filename)):
                logger.info(
                    "Document '%s' (ID: %s, Source: %s) unchanged (%d chunks, hash: %s). Skipping re-ingestion.",
                    filename,
                    doc.id,
                    source_id or doc.source_id,
                    chunk_count,
                    doc_content_hash[:12],
                )
                # Backfill missing provenance if needed
                updated = False
                if not doc.content_hash:
                    doc.content_hash = doc_content_hash
                    updated = True
                if source_id and not doc.source_id:
                    doc.source_id = source_id
                    updated = True
                if canonical_url and not doc.canonical_url:
                    doc.canonical_url = canonical_url
                    updated = True
                if updated:
                    session.commit()
                    session.refresh(doc)
                return doc

        # Ensure document record exists with 'processing' status
        if not doc:
            doc = PolicyDocument(
                id=doc_id,
                source_id=source_id,
                source_filename=filename,
                canonical_url=canonical_url,
                content_hash=doc_content_hash,
                document_type=doc_type,
                version_label=version_label,
                effective_from=effective_from,
                effective_to=effective_to,
                status="processing",
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)
        else:
            doc.status = "processing"
            doc.source_id = source_id or doc.source_id
            doc.canonical_url = canonical_url or doc.canonical_url
            doc.content_hash = doc_content_hash
            session.commit()

        storage_path: Optional[str] = None

        try:
            # Step 1: Extract structured document
            extracted_doc = document_extractor.extract(filename=filename, content=content)
            if extracted_doc.metadata:
                if not doc.source_id and extracted_doc.metadata.get("source_id"):
                    doc.source_id = extracted_doc.metadata.get("source_id")
                if not doc.canonical_url and extracted_doc.metadata.get("url"):
                    doc.canonical_url = extracted_doc.metadata.get("url")

            # Step 2: Upload original file to Supabase Storage
            storage_dest = f"policies/{doc.id}/{filename}"
            content_type = self._get_content_type(ext)
            try:
                storage_path = supabase_service.upload_file(
                    destination_path=storage_dest,
                    content=content,
                    content_type=content_type,
                )
            except Exception as storage_err:
                logger.warning(
                    "Supabase Storage upload failed for %s (%s); recording fallback path.",
                    filename,
                    storage_err,
                )
                storage_path = f"fallback://{settings.SUPABASE_STORAGE_BUCKET}/{storage_dest}"

            # Step 3: Chunk document
            chunks = policy_chunker.chunk_document(doc_id=doc.id, extracted_doc=extracted_doc)
            if not chunks:
                raise EmptyDocumentException(f"No valid chunks produced for document '{filename}'.")

            # Step 4: Compute embeddings
            chunk_texts = [c.content for c in chunks]
            embeddings = gemini_service.embed_texts(
                texts=chunk_texts,
                model_id=settings.GEMINI_EMBEDDING_MODEL,
                target_dim=settings.EMBEDDING_DIMENSIONS,
            )

            # Step 5: Persist chunks atomically in PostgreSQL
            # Remove any previous chunks for this document to prevent duplicates
            session.query(PolicyChunk).filter(PolicyChunk.document_id == doc.id).delete(
                synchronize_session=False
            )

            for chunk_data, vector in zip(chunks, embeddings):
                db_chunk = PolicyChunk(
                    id=chunk_data.chunk_id,
                    document_id=doc.id,
                    chunk_index=chunk_data.chunk_index,
                    section_path=chunk_data.section_path,
                    page_number=chunk_data.page_number,
                    content=chunk_data.content,
                    embedding=vector,
                    embedding_model=settings.GEMINI_EMBEDDING_MODEL,
                    content_hash=chunk_data.content_hash,
                )
                session.add(db_chunk)

            # Update document status to 'active'
            doc.status = "active"
            doc.storage_path = storage_path
            doc.source_id = source_id or doc.source_id
            doc.canonical_url = canonical_url or doc.canonical_url
            doc.content_hash = doc_content_hash
            session.commit()
            session.refresh(doc)

            logger.info(
                "Successfully ingested '%s' (ID: %s, Source: %s) with %d chunks. Status: active",
                filename,
                doc.id,
                doc.source_id,
                len(chunks),
            )
            return doc

        except Exception as exc:
            session.rollback()
            logger.error("Ingestion failed for document '%s' (ID: %s): %s", filename, doc.id, exc)
            # Mark document as failed
            try:
                doc.status = "failed"
                session.commit()
            except Exception:
                session.rollback()
            raise

    def _get_content_type(self, ext: str) -> str:
        if ext == ".pdf":
            return "application/pdf"
        elif ext == ".docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif ext == ".txt":
            return "text/plain"
        return "application/octet-stream"


policy_ingestion_service = PolicyIngestionService()
