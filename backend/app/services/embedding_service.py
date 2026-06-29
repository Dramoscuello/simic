import logging
import os
from typing import List, Optional

from openai import OpenAI


logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Error de embedding recuperable (para fail-open)."""


class EmbeddingService:
    DEFAULT_MODEL = "text-embedding-3-small"
    DEFAULT_BATCH_SIZE = 64

    _client: Optional[OpenAI] = None

    @classmethod
    def _get_client(cls) -> OpenAI:
        if cls._client is None:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise EmbeddingServiceError("OPENAI_API_KEY no configurada")
            cls._client = OpenAI(api_key=api_key)
        return cls._client

    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return " "
        normalized = " ".join(str(text).split())
        return normalized if normalized else " "

    @classmethod
    def embed_texts(
        cls,
        texts: List[str],
        model: str = DEFAULT_MODEL,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> List[List[float]]:
        if not texts:
            return []

        if batch_size <= 0:
            batch_size = cls.DEFAULT_BATCH_SIZE

        client = cls._get_client()
        normalized_texts = [cls.normalize_text(t) for t in texts]
        embeddings: List[List[float]] = []

        try:
            for i in range(0, len(normalized_texts), batch_size):
                batch = normalized_texts[i : i + batch_size]
                response = client.embeddings.create(model=model, input=batch)
                data_sorted = sorted(response.data, key=lambda item: item.index)
                embeddings.extend([item.embedding for item in data_sorted])
        except Exception as e:
            logger.exception("EmbeddingService error")
            raise EmbeddingServiceError(str(e)) from e

        if len(embeddings) != len(texts):
            raise EmbeddingServiceError(
                f"Cantidad de embeddings inesperada: {len(embeddings)} de {len(texts)}"
            )

        return embeddings
