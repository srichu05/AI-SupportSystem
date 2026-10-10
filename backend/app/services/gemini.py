import logging
from typing import Dict, Any, Optional, List
from backend.app.core.config import settings
from backend.app.core.errors import ProviderUnavailableException, ProviderRateLimitException

logger = logging.getLogger("complaint_assistant.gemini")


class GeminiService:
    """Service to interact with Gemini API and verify models/embeddings."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_client(self):
        """Lazily initialize Google GenAI client."""
        if not self.is_configured:
            return None
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error("Failed to initialize Google GenAI client: %s", e)
                raise
        return self._client

    def verify_generation(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Smoke test generation model access without fabricating results.
        Returns a structured diagnostic dict.
        """
        target_model = model_id or settings.GEMINI_GENERATION_MODEL
        if not self.is_configured:
            return {
                "success": False,
                "model_id": target_model,
                "status": "unconfigured",
                "message": "GEMINI_API_KEY is not configured in .env or environment.",
            }

        client = self.get_client()
        try:
            logger.info("Executing Gemini generation smoke test with model: %s", target_model)
            response = client.models.generate_content(
                model=target_model,
                contents="Ping. Respond with 'PONG' only."
            )
            text_result = getattr(response, "text", "") or ""
            return {
                "success": True,
                "model_id": target_model,
                "status": "verified",
                "message": "Generation model verified successfully.",
                "sample_output": text_result.strip()[:100],
            }
        except Exception as exc:
            logger.warning("Gemini generation smoke test failed for %s: %s", target_model, exc)
            return {
                "success": False,
                "model_id": target_model,
                "status": "failed",
                "error_type": type(exc).__name__,
                "message": str(exc).splitlines()[0],
            }

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.2,
        max_retries: int = 2,
    ) -> str:
        """
        Generate grounded text completion using hosted Gemini model.
        Applies exponential backoff on retryable provider errors (429, 503).
        """
        if not self.is_configured:
            raise ProviderUnavailableException(
                provider="Gemini Generation",
                message="GEMINI_API_KEY is not configured.",
            )

        target_model = model_id or settings.GEMINI_GENERATION_MODEL
        client = self.get_client()

        kwargs = {}
        try:
            from google.genai import types
            config_kwargs = {"temperature": temperature}
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
            kwargs["config"] = types.GenerateContentConfig(**config_kwargs)
        except Exception as exc:
            logger.debug("GenerateContentConfig setup fallback: %s", exc)

        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    **kwargs,
                )
                text = getattr(response, "text", "") or ""
                return text.strip()
            except Exception as exc:
                last_exc = exc
                err_msg = str(exc)
                logger.warning(
                    "Gemini generate_text attempt %d/%d failed: %s",
                    attempt,
                    max_retries,
                    err_msg,
                )
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "503" in err_msg or "UNAVAILABLE" in err_msg:
                    import time
                    time.sleep(2 ** attempt)
                else:
                    break

        if "429" in str(last_exc) or "RESOURCE_EXHAUSTED" in str(last_exc):
            raise ProviderRateLimitException(
                provider="Gemini Generation",
                message=f"Gemini generation rate limit exceeded: {last_exc}",
            )
        raise ProviderUnavailableException(
            provider="Gemini Generation",
            message=f"Gemini generation failed: {last_exc}",
        )

    def verify_embedding(
        self,
        model_id: Optional[str] = None,
        expected_dim: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Smoke test hosted embedding model access, output dimensions, and quota.
        Does NOT assume model is available until verified.
        """
        target_model = model_id or settings.GEMINI_EMBEDDING_MODEL
        target_dim = expected_dim or settings.EMBEDDING_DIMENSIONS

        if not self.is_configured:
            return {
                "success": False,
                "model_id": target_model,
                "status": "unconfigured",
                "message": "GEMINI_API_KEY is not configured in .env or environment.",
            }

        client = self.get_client()
        try:
            logger.info("Executing Gemini embedding smoke test with model: %s", target_model)
            kwargs = {}
            if target_dim:
                try:
                    from google.genai import types
                    kwargs["config"] = types.EmbedContentConfig(output_dimensionality=target_dim)
                except Exception:
                    pass

            response = client.models.embed_content(
                model=target_model,
                contents="Smoke test policy embedding text.",
                **kwargs
            )
            
            # Extract embedding vector
            values = []
            if hasattr(response, "embedding") and response.embedding and hasattr(response.embedding, "values"):
                values = response.embedding.values
            elif hasattr(response, "embeddings") and response.embeddings:
                values = response.embeddings[0].values
            
            actual_dim = len(values) if values else 0
            dim_matched = (actual_dim == target_dim)

            if not dim_matched:
                msg = f"Dimension mismatch: expected {target_dim}, got {actual_dim}"
                logger.warning(msg)
                return {
                    "success": False,
                    "model_id": target_model,
                    "status": "dimension_mismatch",
                    "expected_dimensions": target_dim,
                    "actual_dimensions": actual_dim,
                    "message": msg,
                }

            return {
                "success": True,
                "model_id": target_model,
                "status": "verified",
                "expected_dimensions": target_dim,
                "actual_dimensions": actual_dim,
                "message": f"Embedding verified with exact {actual_dim} dimensions.",
            }
        except Exception as exc:
            logger.warning("Gemini embedding smoke test failed for %s: %s", target_model, exc)
            return {
                "success": False,
                "model_id": target_model,
                "status": "failed",
                "expected_dimensions": target_dim,
                "actual_dimensions": None,
                "error_type": type(exc).__name__,
                "message": str(exc).splitlines()[0],
            }

    def verify_error_handling(self) -> Dict[str, Any]:
        """
        Verify that invalid model requests trigger clean provider exceptions.
        """
        if not self.is_configured:
            return {
                "success": False,
                "status": "unconfigured",
                "message": "GEMINI_API_KEY not configured. Cannot test live error handling."
            }

        client = self.get_client()
        try:
            # Deliberately request a non-existent model
            client.models.generate_content(
                model="non-existent-gemini-model-xyz-12345",
                contents="test"
            )
            return {
                "success": False,
                "status": "unexpected_success",
                "message": "Invalid model request unexpectedly succeeded."
            }
        except Exception as exc:
            return {
                "success": True,
                "status": "error_handling_verified",
                "caught_exception": type(exc).__name__,
                "message": "Provider cleanly raised expected exception on invalid model.",
            }

    def embed_texts(
        self,
        texts: List[str],
        model_id: Optional[str] = None,
        target_dim: Optional[int] = None,
        batch_size: int = 10,
        max_retries: int = 3,
    ) -> List[List[float]]:
        """
        Generate vector embeddings for a list of texts using hosted Gemini embedding model.
        Batches requests and applies bounded exponential backoff on retries.
        """
        if not texts:
            return []

        if not self.is_configured:
            logger.warning("Gemini API not configured. Generating zero vector mocks.")
            dim = target_dim or settings.EMBEDDING_DIMENSIONS
            return [[0.0] * dim for _ in texts]

        target_model = model_id or settings.GEMINI_EMBEDDING_MODEL
        expected_dim = target_dim or settings.EMBEDDING_DIMENSIONS
        client = self.get_client()

        try:
            from google.genai import types
            config = types.EmbedContentConfig(output_dimensionality=expected_dim)
        except Exception as e:
            logger.error("Failed to configure EmbedContentConfig: %s", e)
            config = None

        all_embeddings: List[List[float]] = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            items = [
                types.Content(parts=[types.Part.from_text(text=t)])
                for t in batch
            ]

            last_exc = None
            batch_success = False

            for attempt in range(1, max_retries + 1):
                try:
                    kwargs = {}
                    if config:
                        kwargs["config"] = config

                    response = client.models.embed_content(
                        model=target_model,
                        contents=items,
                        **kwargs,
                    )

                    batch_vectors: List[List[float]] = []
                    if hasattr(response, "embeddings") and response.embeddings:
                        for emb in response.embeddings:
                            vals = list(emb.values) if hasattr(emb, "values") else []
                            batch_vectors.append(vals)

                    if len(batch_vectors) != len(batch):
                        raise RuntimeError(
                            f"Expected {len(batch)} embeddings from batch, got {len(batch_vectors)}"
                        )

                    # Validate vector dimensions
                    for v in batch_vectors:
                        if len(v) != expected_dim:
                            raise ValueError(
                                f"Dimension mismatch: expected {expected_dim}, got {len(v)}"
                            )

                    all_embeddings.extend(batch_vectors)
                    batch_success = True
                    break

                except Exception as exc:
                    last_exc = exc
                    err_msg = str(exc)
                    logger.warning(
                        "Gemini embed_content attempt %d/%d failed: %s",
                        attempt,
                        max_retries,
                        err_msg,
                    )
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "503" in err_msg or "UNAVAILABLE" in err_msg:
                        # Exponential backoff
                        import time
                        time.sleep(2 ** attempt)
                    else:
                        break

            if not batch_success:
                logger.error("Failed to generate embeddings for batch after retries: %s", last_exc)
                raise ProviderUnavailableException(
                    provider="Gemini Embedding",
                    message=f"Gemini embedding failed for batch: {last_exc}",
                )

        return all_embeddings

    def embed_query(
        self,
        query: str,
        model_id: Optional[str] = None,
        target_dim: Optional[int] = None,
    ) -> List[float]:
        """Generate embedding vector for a single query text."""
        results = self.embed_texts([query], model_id=model_id, target_dim=target_dim)
        if not results:
            raise ProviderUnavailableException(
                provider="Gemini Embedding",
                message="Failed to generate query embedding.",
            )
        return results[0]

    def run_all_smoke_tests(self) -> Dict[str, Any]:
        """Run complete provider verification suite."""
        gen_result = self.verify_generation()
        emb_result = self.verify_embedding()
        err_result = self.verify_error_handling()

        overall_success = gen_result["success"] and emb_result["success"]
        return {
            "gemini_api_configured": self.is_configured,
            "overall_provider_verified": overall_success,
            "generation": gen_result,
            "embedding": emb_result,
            "error_handling": err_result,
        }


gemini_service = GeminiService()

