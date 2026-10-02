
from typing import List

import ollama
from django.conf import settings


class OllamaEmbeddingService:
    """
    Generates local text embeddings using Ollama.

    This keeps Phase 7 completely local and avoids paid embedding APIs.
    """

    def __init__(self):
        self.model = settings.OLLAMA_EMBEDDING_MODEL

    def embed(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text string.
        """

        if not text or not text.strip():
            raise ValueError("Cannot generate an embedding for empty text.")

        response = ollama.embed(
            model=self.model,
            input=text,
        )

        # Current Ollama Python responses expose embeddings
        # in dictionary-like form. This also supports object-style
        # responses for compatibility.
        if isinstance(response, dict):
            embeddings = response.get("embeddings")
        else:
            embeddings = getattr(response, "embeddings", None)

        if not embeddings:
            raise RuntimeError(
                "Ollama returned no embeddings."
            )

        return embeddings[0]
