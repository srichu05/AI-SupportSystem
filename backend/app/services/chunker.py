import hashlib
import uuid
import re
import logging
from dataclasses import dataclass
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.services.extractor import ExtractedDocument, ExtractedSection

logger = logging.getLogger("complaint_assistant.chunker")


@dataclass
class PolicyChunkData:
    """A prepared, chunked segment of policy text ready for vectorization and storage."""
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    section_path: Optional[str]
    page_number: Optional[int]
    content: str
    content_hash: str


class PolicyChunker:
    """
    Splits extracted document sections into retrieval-ready passages.
    Preserves:
    - Heading and section hierarchy
    - Page numbers where available
    - Paragraph and sentence boundaries
    - Stable chunk UUIDs and SHA-256 content hashes
    """

    def __init__(
        self,
        chunk_size_chars: Optional[int] = None,
        chunk_overlap_chars: Optional[int] = None,
    ):
        self.chunk_size = chunk_size_chars or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap_chars or settings.CHUNK_OVERLAP

    def chunk_document(
        self,
        doc_id: uuid.UUID,
        extracted_doc: ExtractedDocument,
    ) -> List[PolicyChunkData]:
        """
        Produce ordered, structured chunks from an ExtractedDocument.
        """
        chunks: List[PolicyChunkData] = []
        global_chunk_index = 0

        for section in extracted_doc.sections:
            sec_text = section.text.strip()
            if not sec_text:
                continue

            sec_chunks = self._split_text(sec_text)
            for chunk_str in sec_chunks:
                clean_chunk = chunk_str.strip()
                if not clean_chunk:
                    continue

                # Compute content hash
                c_hash = hashlib.sha256(clean_chunk.encode("utf-8")).hexdigest()

                # Generate deterministic stable UUID for this chunk
                chunk_uuid = uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"policy:{doc_id}:{global_chunk_index}:{c_hash[:16]}"
                )

                chunk_obj = PolicyChunkData(
                    chunk_id=chunk_uuid,
                    document_id=doc_id,
                    chunk_index=global_chunk_index,
                    section_path=section.section_path,
                    page_number=section.page_number,
                    content=clean_chunk,
                    content_hash=c_hash,
                )
                chunks.append(chunk_obj)
                global_chunk_index += 1

        logger.info(
            "Chunked document '%s' (ID: %s) into %d chunks.",
            extracted_doc.filename,
            doc_id,
            len(chunks),
        )
        return chunks

    def _split_text(self, text: str) -> List[str]:
        """
        Splits text into chunks respecting paragraphs and sentences.
        """
        if len(text) <= self.chunk_size:
            return [text]

        # Split into natural paragraphs
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks: List[str] = []
        current_chunk = ""

        for p in paragraphs:
            # If paragraph itself is larger than chunk_size, split by sentences
            if len(p) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                sub_chunks = self._split_large_paragraph(p)
                chunks.extend(sub_chunks)
                continue

            candidate = f"{current_chunk}\n\n{p}" if current_chunk else p
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap if possible
                overlap_seed = self._extract_overlap(current_chunk)
                current_chunk = f"{overlap_seed}\n\n{p}" if overlap_seed else p

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """Split a large paragraph along sentence boundaries."""
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        chunks: List[str] = []
        current_chunk = ""

        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue

            candidate = f"{current_chunk} {s_clean}" if current_chunk else s_clean
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If a single sentence is longer than chunk_size, hard-wrap it
                if len(s_clean) > self.chunk_size:
                    for i in range(0, len(s_clean), self.chunk_size - self.chunk_overlap):
                        slice_end = min(i + self.chunk_size, len(s_clean))
                        chunks.append(s_clean[i:slice_end].strip())
                    current_chunk = ""
                else:
                    current_chunk = s_clean

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _extract_overlap(self, text: str) -> str:
        """Extract trailing characters up to overlap limit."""
        if not text or self.chunk_overlap <= 0:
            return ""
        if len(text) <= self.chunk_overlap:
            return text
        tail = text[-self.chunk_overlap:]
        # Try to break at a word boundary
        space_idx = tail.find(" ")
        if space_idx != -1 and space_idx < len(tail) - 5:
            return tail[space_idx + 1:]
        return tail


policy_chunker = PolicyChunker()
