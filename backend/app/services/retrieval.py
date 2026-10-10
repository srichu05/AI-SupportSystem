import math
import uuid
import re
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.services.gemini import gemini_service
from backend.app.models.policy import PolicyChunk, PolicyDocument

logger = logging.getLogger("complaint_assistant.retrieval")

STOP_WORDS = {
    "what", "is", "the", "and", "in", "of", "to", "a", "an", "that", "this",
    "for", "on", "with", "as", "by", "at", "from", "are", "be", "or", "was",
    "must", "have", "has", "can", "could", "should", "would", "will", "my", "your"
}


@dataclass
class RetrievedChunk:
    """A policy passage retrieved via hybrid search with traceability metadata."""
    chunk_id: str
    document_id: str
    source_filename: str
    section_path: Optional[str]
    page_number: Optional[int]
    content: str
    semantic_rank: Optional[int]
    semantic_score: Optional[float]
    keyword_rank: Optional[int]
    keyword_score: Optional[float]
    rrf_score: float
    source_id: Optional[str] = None
    canonical_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "source_id": self.source_id,
            "canonical_url": self.canonical_url,
            "source_filename": self.source_filename,
            "section_path": self.section_path,
            "page_number": self.page_number,
            "content": self.content,
            "semantic_rank": self.semantic_rank,
            "semantic_score": self.semantic_score,
            "keyword_rank": self.keyword_rank,
            "keyword_score": self.keyword_score,
            "rrf_score": self.rrf_score,
        }


class HybridRetrievalService:
    """
    Performs hybrid retrieval combining pgvector semantic search
    and PostgreSQL full-text keyword search via Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        top_k_vector: Optional[int] = None,
        top_k_keyword: Optional[int] = None,
        final_top_k: Optional[int] = None,
        rrf_k: Optional[int] = None,
    ):
        self.top_k_vector = top_k_vector or settings.RETRIEVAL_TOP_K_VECTOR
        self.top_k_keyword = top_k_keyword or settings.RETRIEVAL_TOP_K_KEYWORD
        self.final_top_k = final_top_k or settings.RETRIEVAL_FINAL_TOP_K
        self.rrf_k = rrf_k or settings.RETRIEVAL_RRF_K

    def retrieve(
        self,
        query: str,
        db: Session,
        top_k_vector: Optional[int] = None,
        top_k_keyword: Optional[int] = None,
        final_top_k: Optional[int] = None,
        rrf_k: Optional[int] = None,
        filter_active_only: bool = True,
    ) -> List[RetrievedChunk]:
        """
        Execute hybrid search and return fused, deduplicated candidate passages.
        """
        if not query or not query.strip():
            return []

        k_vec = top_k_vector or self.top_k_vector
        k_kw = top_k_keyword or self.top_k_keyword
        k_final = final_top_k or self.final_top_k
        k_rrf = rrf_k or self.rrf_k

        # Step 1: Generate query embedding vector
        query_vector = gemini_service.embed_query(query)

        # Step 2: Retrieve semantic candidates (pgvector or dialect fallback)
        semantic_results = self._search_vector(
            db=db,
            query_vector=query_vector,
            top_k=k_vec,
            filter_active_only=filter_active_only,
        )

        # Step 3: Retrieve keyword candidates (PostgreSQL full-text or dialect fallback)
        keyword_results = self._search_keyword(
            db=db,
            query=query,
            top_k=k_kw,
            filter_active_only=filter_active_only,
        )

        # Step 4: Reciprocal Rank Fusion (RRF)
        fused = self._reciprocal_rank_fusion(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            rrf_k=k_rrf,
            final_top_k=k_final,
        )

        logger.info(
            "Hybrid retrieval for query '%s' retrieved %d semantic, %d keyword, fused to top %d.",
            query[:50],
            len(semantic_results),
            len(keyword_results),
            len(fused),
        )
        return fused

    def _search_vector(
        self,
        db: Session,
        query_vector: List[float],
        top_k: int,
        filter_active_only: bool,
    ) -> List[Dict[str, Any]]:
        """Semantic search via pgvector on PostgreSQL, or in-memory cosine fallback for SQLite test environments."""
        dialect = db.bind.dialect.name if db.bind else "postgresql"

        if dialect == "postgresql":
            # Native pgvector cosine distance query using CAST(:query_vec AS vector)
            vec_literal = "[" + ",".join(str(f) for f in query_vector) + "]"
            status_clause = "AND d.status = 'active'" if filter_active_only else ""

            sql = text(f"""
                SELECT 
                    c.id AS chunk_id,
                    c.document_id AS document_id,
                    d.source_filename AS source_filename,
                    d.source_id AS source_id,
                    d.canonical_url AS canonical_url,
                    c.section_path AS section_path,
                    c.page_number AS page_number,
                    c.content AS content,
                    (1.0 - (c.embedding <=> CAST(:query_vec AS vector))) AS similarity_score
                FROM policy_chunks c
                JOIN policy_documents d ON c.document_id = d.id
                WHERE c.embedding IS NOT NULL {status_clause}
                ORDER BY c.embedding <=> CAST(:query_vec AS vector) ASC
                LIMIT :top_k;
            """)
            try:
                rows = db.execute(sql, {"query_vec": vec_literal, "top_k": top_k}).mappings().all()
                results = []
                for idx, r in enumerate(rows, 1):
                    results.append({
                        "chunk_id": str(r["chunk_id"]),
                        "document_id": str(r["document_id"]),
                        "source_filename": r["source_filename"],
                        "source_id": r.get("source_id"),
                        "canonical_url": r.get("canonical_url"),
                        "section_path": r["section_path"],
                        "page_number": r["page_number"],
                        "content": r["content"],
                        "rank": idx,
                        "score": float(r["similarity_score"]) if r["similarity_score"] is not None else 0.0,
                    })
                return results
            except Exception as e:
                logger.warning("PostgreSQL pgvector query failed, rolling back and falling back: %s", e)
                db.rollback()

        # Dialect fallback (e.g. SQLite test engine)
        query_chunks = (
            db.query(PolicyChunk, PolicyDocument)
            .join(PolicyDocument, PolicyChunk.document_id == PolicyDocument.id)
        )
        if filter_active_only:
            query_chunks = query_chunks.filter(PolicyDocument.status == "active")

        items = query_chunks.all()
        scored = []
        for chunk, doc in items:
            if not chunk.embedding:
                continue
            sim = self._cosine_similarity(query_vector, chunk.embedding)
            scored.append((chunk, doc, sim))

        scored.sort(key=lambda x: x[2], reverse=True)
        results = []
        for idx, (chunk, doc, score) in enumerate(scored[:top_k], 1):
            results.append({
                "chunk_id": str(chunk.id),
                "document_id": str(doc.id),
                "source_filename": doc.source_filename,
                "source_id": getattr(doc, "source_id", None),
                "canonical_url": getattr(doc, "canonical_url", None),
                "section_path": chunk.section_path,
                "page_number": chunk.page_number,
                "content": chunk.content,
                "rank": idx,
                "score": float(score),
            })
        return results

    def _search_keyword(
        self,
        db: Session,
        query: str,
        top_k: int,
        filter_active_only: bool,
    ) -> List[Dict[str, Any]]:
        """Full-text search via PostgreSQL tsvector or keyword match fallback for SQLite."""
        dialect = db.bind.dialect.name if db.bind else "postgresql"

        if dialect == "postgresql":
            status_clause = "AND d.status = 'active'" if filter_active_only else ""

            # Attempt 1: plainto_tsquery (AND matching)
            sql_plain = text(f"""
                SELECT 
                    c.id AS chunk_id,
                    c.document_id AS document_id,
                    d.source_filename AS source_filename,
                    d.source_id AS source_id,
                    d.canonical_url AS canonical_url,
                    c.section_path AS section_path,
                    c.page_number AS page_number,
                    c.content AS content,
                    ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', :query)) AS rank_score
                FROM policy_chunks c
                JOIN policy_documents d ON c.document_id = d.id
                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
                {status_clause}
                ORDER BY rank_score DESC
                LIMIT :top_k;
            """)
            try:
                rows = db.execute(sql_plain, {"query": query, "top_k": top_k}).mappings().all()
                if rows:
                    return [
                        {
                            "chunk_id": str(r["chunk_id"]),
                            "document_id": str(r["document_id"]),
                            "source_filename": r["source_filename"],
                            "source_id": r.get("source_id"),
                            "canonical_url": r.get("canonical_url"),
                            "section_path": r["section_path"],
                            "page_number": r["page_number"],
                            "content": r["content"],
                            "rank": idx,
                            "score": float(r["rank_score"]),
                        }
                        for idx, r in enumerate(rows, 1)
                    ]
            except Exception as e:
                logger.warning("PostgreSQL plainto_tsquery query failed: %s", e)
                db.rollback()

            # Attempt 2: to_tsquery with OR operator across meaningful terms
            words = re.findall(r"\b[A-Za-z]{3,}\b", query)
            keywords = [w.lower() for w in words if w.lower() not in STOP_WORDS]
            if keywords:
                or_query = " | ".join(keywords)
                sql_or = text(f"""
                    SELECT 
                        c.id AS chunk_id,
                        c.document_id AS document_id,
                        d.source_filename AS source_filename,
                        d.source_id AS source_id,
                        d.canonical_url AS canonical_url,
                        c.section_path AS section_path,
                        c.page_number AS page_number,
                        c.content AS content,
                        ts_rank_cd(to_tsvector('english', c.content), to_tsquery('english', :or_query)) AS rank_score
                    FROM policy_chunks c
                    JOIN policy_documents d ON c.document_id = d.id
                    WHERE to_tsvector('english', c.content) @@ to_tsquery('english', :or_query)
                    {status_clause}
                    ORDER BY rank_score DESC
                    LIMIT :top_k;
                """)
                try:
                    rows_or = db.execute(sql_or, {"or_query": or_query, "top_k": top_k}).mappings().all()
                    if rows_or:
                        return [
                            {
                                "chunk_id": str(r["chunk_id"]),
                                "document_id": str(r["document_id"]),
                                "source_filename": r["source_filename"],
                                "source_id": r.get("source_id"),
                                "canonical_url": r.get("canonical_url"),
                                "section_path": r["section_path"],
                                "page_number": r["page_number"],
                                "content": r["content"],
                                "rank": idx,
                                "score": float(r["rank_score"]),
                            }
                            for idx, r in enumerate(rows_or, 1)
                        ]
                except Exception as e:
                    logger.warning("PostgreSQL OR tsquery failed: %s", e)
                    db.rollback()

        # Keyword matching fallback
        query_terms = [t.lower() for t in query.split() if len(t) > 2 and t.lower() not in STOP_WORDS]
        query_chunks = (
            db.query(PolicyChunk, PolicyDocument)
            .join(PolicyDocument, PolicyChunk.document_id == PolicyDocument.id)
        )
        if filter_active_only:
            query_chunks = query_chunks.filter(PolicyDocument.status == "active")

        items = query_chunks.all()
        scored = []
        for chunk, doc in items:
            c_lower = chunk.content.lower()
            match_count = sum(1 for term in query_terms if term in c_lower)
            if match_count > 0:
                score = match_count / max(len(query_terms), 1)
                scored.append((chunk, doc, score))

        scored.sort(key=lambda x: x[2], reverse=True)
        results = []
        for idx, (chunk, doc, score) in enumerate(scored[:top_k], 1):
            results.append({
                "chunk_id": str(chunk.id),
                "document_id": str(doc.id),
                "source_filename": doc.source_filename,
                "source_id": getattr(doc, "source_id", None),
                "canonical_url": getattr(doc, "canonical_url", None),
                "section_path": chunk.section_path,
                "page_number": chunk.page_number,
                "content": chunk.content,
                "rank": idx,
                "score": float(score),
            })
        return results

    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        rrf_k: int,
        final_top_k: int,
    ) -> List[RetrievedChunk]:
        """
        Combine two ranked lists using standard Reciprocal Rank Fusion:
        RRF(d) = sum(1 / (k + rank(d)))
        """
        fused_scores: Dict[str, float] = {}
        chunk_metadata: Dict[str, Dict[str, Any]] = {}
        sem_ranks: Dict[str, int] = {}
        sem_scores: Dict[str, float] = {}
        kw_ranks: Dict[str, int] = {}
        kw_scores: Dict[str, float] = {}

        # 1. Process semantic ranks
        for item in semantic_results:
            cid = item["chunk_id"]
            rank = item["rank"]
            score = item["score"]
            rrf_contrib = 1.0 / (rrf_k + rank)
            fused_scores[cid] = fused_scores.get(cid, 0.0) + rrf_contrib
            sem_ranks[cid] = rank
            sem_scores[cid] = score
            chunk_metadata[cid] = item

        # 2. Process keyword ranks
        for item in keyword_results:
            cid = item["chunk_id"]
            rank = item["rank"]
            score = item["score"]
            rrf_contrib = 1.0 / (rrf_k + rank)
            fused_scores[cid] = fused_scores.get(cid, 0.0) + rrf_contrib
            kw_ranks[cid] = rank
            kw_scores[cid] = score
            if cid not in chunk_metadata:
                chunk_metadata[cid] = item

        # 3. Sort by fused score descending
        sorted_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)

        # 4. Construct final RetrievedChunk list
        results: List[RetrievedChunk] = []
        for cid in sorted_ids[:final_top_k]:
            meta = chunk_metadata[cid]
            results.append(
                RetrievedChunk(
                    chunk_id=cid,
                    document_id=meta["document_id"],
                    source_filename=meta["source_filename"],
                    section_path=meta.get("section_path"),
                    page_number=meta.get("page_number"),
                    content=meta["content"],
                    semantic_rank=sem_ranks.get(cid),
                    semantic_score=sem_scores.get(cid),
                    keyword_rank=kw_ranks.get(cid),
                    keyword_score=kw_scores.get(cid),
                    rrf_score=fused_scores[cid],
                    source_id=meta.get("source_id"),
                    canonical_url=meta.get("canonical_url"),
                )
            )

        return results

        return results

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vector lists."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


hybrid_retrieval_service = HybridRetrievalService()
