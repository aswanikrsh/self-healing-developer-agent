
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from django.conf import settings

from .embeddings import OllamaEmbeddingService


class ChromaMemoryStore:
    """
    Persistent ChromaDB storage for developer-agent memories.

    Each memory contains:
    - project information
    - error information
    - root cause
    - proposed fix
    - patch
    - test result
    """

    def __init__(self):
        persist_directory = Path(
            settings.CHROMA_PERSIST_DIRECTORY
        )

        persist_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(
            path=str(persist_directory)
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine"
            },
        )

        self.embedding_service = OllamaEmbeddingService()

    def add_memory(
        self,
        memory_id: str,
        document: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Store a developer memory in ChromaDB.
        """

        if not document.strip():
            raise ValueError(
                "Memory document cannot be empty."
            )

        embedding = self.embedding_service.embed(
            document
        )

        safe_metadata = {
            key: str(value)
            for key, value in metadata.items()
            if value is not None
        }

        self.collection.upsert(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[safe_metadata],
        )

    def search(
        self,
        query: str,
        n_results: Optional[int] = None,
        project_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar memories.
        """

        if not query or not query.strip():
            return []

        if n_results is None:
            n_results = settings.MEMORY_TOP_K

        query_embedding = self.embedding_service.embed(
            query
        )

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
        }

        if project_path:
            kwargs["where"] = {
                "project_path": str(project_path)
            }

        results = self.collection.query(
            **kwargs
        )

        memories = []

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for index, memory_id in enumerate(ids):

            memories.append(
                {
                    "id": memory_id,
                    "document": (
                        documents[index]
                        if index < len(documents)
                        else ""
                    ),
                    "metadata": (
                        metadatas[index]
                        if index < len(metadatas)
                        else {}
                    ),
                    "distance": (
                        distances[index]
                        if index < len(distances)
                        else None
                    ),
                }
            )

        return memories

    def count(self) -> int:
        """
        Return the total number of stored memories.
        """

        return self.collection.count()
