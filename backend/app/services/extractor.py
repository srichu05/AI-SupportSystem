import io
import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from backend.app.core.config import settings
from backend.app.core.errors import (
    UnsupportedFileTypeException,
    EmptyDocumentException,
    DocumentSizeLimitExceededException,
    DocumentExtractionException,
)

logger = logging.getLogger("complaint_assistant.extractor")

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@dataclass
class ExtractedSection:
    """A logical extracted segment of a document (e.g., page, section, or paragraph block)."""
    text: str
    section_path: Optional[str] = None
    page_number: Optional[int] = None


@dataclass
class ExtractedDocument:
    """Structured representation of extracted document contents."""
    filename: str
    document_type: str  # PDF, DOCX, TXT
    raw_text: str
    sections: List[ExtractedSection]
    total_characters: int
    metadata: Optional[dict] = None


class DocumentExtractor:
    """
    Extracts text and structural metadata from PDF, DOCX, and TXT files.
    - PDF: Extracted via PyMuPDF (fitz), preserving page numbers (1-indexed).
    - DOCX: Extracted via python-docx, preserving heading hierarchy.
    - TXT: Extracted via standard Python string decoding and section detection.
    """

    def __init__(self, max_file_size_bytes: Optional[int] = None):
        self.max_file_size = max_file_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES

    def extract(self, filename: str, content: bytes) -> ExtractedDocument:
        """
        Validate file format and extract structured content from raw bytes.
        """
        if not filename:
            filename = "document.txt"

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeException(
                f"Unsupported file extension '{ext}'. Only .pdf, .docx, and .txt files are supported."
            )

        # 1. Validate file size
        if len(content) > self.max_file_size:
            raise DocumentSizeLimitExceededException(
                f"File size ({len(content)} bytes) exceeds the maximum allowed limit of {self.max_file_size} bytes."
            )

        # 2. Check for empty binary content
        if not content or len(content.strip()) == 0:
            raise EmptyDocumentException(f"Uploaded file '{filename}' is empty.")

        # 3. Route to format-specific parser
        doc_type = ext.lstrip(".").upper()
        if ext == ".pdf":
            return self._extract_pdf(filename, content)
        elif ext == ".docx":
            return self._extract_docx(filename, content)
        elif ext == ".txt":
            return self._extract_txt(filename, content)
        else:
            raise UnsupportedFileTypeException(f"No extractor handler configured for '{ext}'")

    def _extract_pdf(self, filename: str, content: bytes) -> ExtractedDocument:
        """Extract text page-by-page from PDF using PyMuPDF."""
        try:
            import pymupdf
        except ImportError:
            try:
                import fitz as pymupdf
            except ImportError:
                raise DocumentExtractionException("PyMuPDF library is not installed in the environment.")

        try:
            doc = pymupdf.open(stream=content, filetype="pdf")
        except Exception as exc:
            logger.warning("Failed to parse PDF binary for %s: %s", filename, exc)
            raise DocumentExtractionException(f"Invalid or corrupted PDF file: {exc}")

        sections: List[ExtractedSection] = []
        raw_parts: List[str] = []

        try:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_num = page_idx + 1
                page_text = page.get_text()

                clean_text = page_text.strip()
                if not clean_text:
                    continue

                raw_parts.append(clean_text)

                # Attempt to detect heading from first line of page or blocks
                first_line = clean_text.splitlines()[0].strip() if clean_text.splitlines() else None
                heading = first_line if first_line and len(first_line) < 80 else f"Page {page_num}"

                sections.append(
                    ExtractedSection(
                        text=clean_text,
                        section_path=heading,
                        page_number=page_num,
                    )
                )
        finally:
            doc.close()

        combined_raw = "\n\n".join(raw_parts).strip()
        if not combined_raw:
            raise EmptyDocumentException(
                f"Uploaded PDF '{filename}' contains no extractable text. Scanned documents without OCR are not supported."
            )

        return ExtractedDocument(
            filename=filename,
            document_type="PDF",
            raw_text=combined_raw,
            sections=sections,
            total_characters=len(combined_raw),
        )

    def _extract_docx(self, filename: str, content: bytes) -> ExtractedDocument:
        """Extract text and heading hierarchy from DOCX using python-docx."""
        try:
            import docx
        except ImportError:
            raise DocumentExtractionException("python-docx library is not installed in the environment.")

        try:
            doc = docx.Document(io.BytesIO(content))
        except Exception as exc:
            logger.warning("Failed to parse DOCX binary for %s: %s", filename, exc)
            raise DocumentExtractionException(f"Invalid or corrupted DOCX file: {exc}")

        sections: List[ExtractedSection] = []
        raw_parts: List[str] = []
        current_heading: Optional[str] = None
        current_section_paras: List[str] = []

        def flush_current_section():
            nonlocal current_section_paras
            if current_section_paras:
                sec_text = "\n\n".join(current_section_paras).strip()
                if sec_text:
                    sections.append(
                        ExtractedSection(
                            text=sec_text,
                            section_path=current_heading or "General",
                            page_number=None,  # DOCX does not have stable page numbers
                        )
                    )
                current_section_paras = []

        for p in doc.paragraphs:
            p_text = p.text.strip()
            if not p_text:
                continue

            raw_parts.append(p_text)
            style_name = getattr(p.style, "name", "") or ""

            if "heading" in style_name.lower():
                flush_current_section()
                current_heading = p_text
            else:
                current_section_paras.append(p_text)

        # Also extract table text if present
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    row_str = " | ".join(cells)
                    table_rows.append(row_str)
                    raw_parts.append(row_str)
            if table_rows:
                current_section_paras.append("\n".join(table_rows))

        flush_current_section()

        combined_raw = "\n\n".join(raw_parts).strip()
        if not combined_raw:
            raise EmptyDocumentException(f"Uploaded DOCX '{filename}' contains no extractable text.")

        return ExtractedDocument(
            filename=filename,
            document_type="DOCX",
            raw_text=combined_raw,
            sections=sections,
            total_characters=len(combined_raw),
        )

    def _extract_txt(self, filename: str, content: bytes) -> ExtractedDocument:
        """Extract text, metadata headers, and section boundaries from plain text files."""
        # Try UTF-8 first, fallback to Latin-1
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except Exception as exc:
                raise DocumentExtractionException(f"Could not decode text file: {exc}")

        clean_text = text.strip()
        if not clean_text:
            raise EmptyDocumentException(f"Uploaded text file '{filename}' contains no extractable text.")

        # Detect sections by markdown headers (e.g., # Header, ## Header) or ALL CAPS headings
        lines = text.splitlines()
        meta: dict = {}
        sections: List[ExtractedSection] = []
        current_heading: Optional[str] = None
        current_lines: List[str] = []
        in_header_meta = True

        num_heading_pattern = re.compile(r"^\d+[\.\)]+\s+[A-Za-z]")

        def flush_txt_section():
            nonlocal current_lines
            if current_lines:
                sec_text = "\n".join(current_lines).strip()
                if sec_text:
                    sections.append(
                        ExtractedSection(
                            text=sec_text,
                            section_path=current_heading or "Overview",
                            page_number=None,
                        )
                    )
                current_lines = []

        KNOWN_META_KEYS = {
            "source id", "source_id", "title", "url", "canonical url",
            "publisher", "retrieved date", "extraction status",
            "document type", "intended use"
        }

        for line in lines:
            stripped = line.strip()

            # Parse leading metadata headers if present (# Source ID: ..., # URL: ..., # ---)
            if in_header_meta:
                if stripped.startswith("# ---") or stripped.startswith("## ---"):
                    continue
                elif stripped.startswith("#") and ":" in stripped:
                    k, v = stripped.lstrip("#").split(":", 1)
                    k_clean = k.strip().lower()
                    if k_clean in KNOWN_META_KEYS:
                        meta[k_clean.replace(" ", "_")] = v.strip()
                        continue
                elif not stripped:
                    continue
                in_header_meta = False

            if not stripped:
                if current_lines:
                    current_lines.append("")
                continue

            # Check if this line looks like a header
            if stripped.startswith("#"):
                flush_txt_section()
                current_heading = stripped.lstrip("#").strip()
            elif stripped.isupper() and 4 <= len(stripped) <= 60 and not stripped.startswith("HTTP"):
                flush_txt_section()
                current_heading = stripped
            elif len(stripped) < 60 and stripped.endswith(":") and not stripped.startswith("http"):
                flush_txt_section()
                current_heading = stripped.rstrip(":")
            elif len(stripped) < 70 and num_heading_pattern.match(stripped):
                flush_txt_section()
                current_heading = stripped
            elif stripped in ["Price Matching Policy", "Price Guarantee Policy"]:
                flush_txt_section()
                current_heading = stripped
            else:
                current_lines.append(stripped)

        flush_txt_section()

        if not sections:
            sections.append(
                ExtractedSection(
                    text=clean_text,
                    section_path="Full Policy",
                    page_number=None,
                )
            )

        return ExtractedDocument(
            filename=filename,
            document_type="TXT",
            raw_text=clean_text,
            sections=sections,
            total_characters=len(clean_text),
            metadata=meta,
        )


document_extractor = DocumentExtractor()
