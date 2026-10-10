import uuid
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
    """

    def ingest_document(
        self,
        doc_id: uuid.UUID,
        filename: str,
        content: bytes,
        version_label: Optional[str] = None,
        effective_from: Optional[date] = None,
        effective_to: Optional[date] = None,
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
                    version_label=version_label,
                    effective_from=effective_from,
                    effective_to=effective_to,
                )
        else:
            return self._execute_ingestion(
                session=db,
                doc_id=doc_id,
                filename=filename,
                content=content,
                version_label=version_label,
                effective_from=effective_from,
                effective_to=effective_to,
            )

    def _execute_ingestion(
        self,
        session: Session,
        doc_id: uuid.UUID,
        filename: str,
        content: bytes,
        version_label: Optional[str],
        effective_from: Optional[date],
        effective_to: Optional[date],
    ) -> PolicyDocument:
        ext = Path(filename).suffix.lower()
        doc_type = ext.lstrip(".").upper()

        # Step 1: Ensure PolicyDocument record exists with 'processing' status
        doc = session.query(PolicyDocument).filter(PolicyDocument.id == doc_id).first()
        if not doc:
            doc = PolicyDocument(
                id=doc_id,
                source_filename=filename,
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
            session.commit()

        storage_path: Optional[str] = None

        try:
            # Step 2: Upload original file to Supabase Storage
            storage_dest = f"policies/{doc_id}/{filename}"
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

            # Step 3: Extract structured document
            extracted_doc = document_extractor.extract(filename=filename, content=content)

            # Step 4: Chunk document
            chunks = policy_chunker.chunk_document(doc_id=doc_id, extracted_doc=extracted_doc)
            if not chunks:
                raise EmptyDocumentException(f"No valid chunks produced for document '{filename}'.")

            # Step 5: Compute embeddings
            chunk_texts = [c.content for c in chunks]
            embeddings = gemini_service.embed_texts(
                texts=chunk_texts,
                model_id=settings.GEMINI_EMBEDDING_MODEL,
                target_dim=settings.EMBEDDING_DIMENSIONS,
            )

            # Step 6: Persist chunks atomically in PostgreSQL
            # Remove any previous chunks for this document to prevent duplicates
            session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).delete(
                synchronize_session=False
            )

            for chunk_data, vector in zip(chunks, embeddings):
                db_chunk = PolicyChunk(
                    id=chunk_data.chunk_id,
                    document_id=doc_id,
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
            session.commit()
            session.refresh(doc)

            logger.info(
                "Successfully ingested '%s' (ID: %s) with %d chunks. Status: active",
                filename,
                doc_id,
                len(chunks),
            )
            return doc

        except Exception as exc:
            session.rollback()
            logger.error("Ingestion failed for document '%s' (ID: %s): %s", filename, doc_id, exc)
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
