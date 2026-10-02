
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.conf import settings

from .chroma_store import ChromaMemoryStore


class MemoryManager:
    """
    High-level interface for Phase 7 project memory.

    Responsible for:
    - creating memory documents
    - storing successful repairs
    - searching previous repairs
    - formatting retrieved memories for agents
    """

    def __init__(self):
        self.store = ChromaMemoryStore()

    def _create_memory_id(
        self,
        project_path: str,
        error_message: str,
        root_cause: str,
    ) -> str:
        """
        Generate a stable unique memory ID.
        """

        raw = (
            f"{project_path}|"
            f"{error_message}|"
            f"{root_cause}|"
            f"{datetime.now().isoformat()}"
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    def _build_document(
        self,
        state: Dict[str, Any],
    ) -> str:
        """
        Convert a successful repair into searchable text.
        """

        project = state.get(
            "project_path",
            ""
        )

        error = state.get(
            "error_message",
            ""
        )

        root_cause = state.get(
            "root_cause",
            ""
        )

        proposed_fix = state.get(
            "proposed_fix",
            ""
        )

        patch = state.get(
            "patch",
            ""
        )

        test_output = state.get(
            "test_output",
            ""
        )

        generated_test_reason = state.get(
            "generated_test_reason",
            ""
        )

        return f"""
PROJECT:
{project}

ERROR:
{error}

ROOT CAUSE:
{root_cause}

PROPOSED FIX:
{proposed_fix}

PATCH:
{patch}

GENERATED TEST REASON:
{generated_test_reason}

TEST RESULT:
{test_output}

This memory represents a previously analyzed developer error
and its successful repair.
""".strip()

    def save_successful_repair(
        self,
        state: Dict[str, Any],
    ) -> Optional[str]:
        """
        Save a successful repair to persistent memory.

        Only successful repairs are stored.
        """

        if not settings.MEMORY_ENABLED:
            return None

        if not state.get("test_passed", False):
            return None

        project_path = str(
            state.get("project_path", "")
        )

        error_message = str(
            state.get("error_message", "")
        )

        root_cause = str(
            state.get("root_cause", "")
        )

        document = self._build_document(
            state
        )

        memory_id = self._create_memory_id(
            project_path,
            error_message,
            root_cause,
        )

        metadata = {
            "project_path": project_path,
            "memory_type": "successful_repair",
            "status": "success",
            "iterations": state.get(
                "iteration",
                0,
            ),
        }

        self.store.add_memory(
            memory_id=memory_id,
            document=document,
            metadata=metadata,
        )

        return memory_id

    def search_similar_repairs(
        self,
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Search previous successful repairs
        related to the current error.
        """

        if not settings.MEMORY_ENABLED:
            return []

        error = str(
            state.get("error_message", "")
        )

        root_cause = str(
            state.get("root_cause", "")
        )

        relevant_files = state.get(
            "relevant_files",
            [],
        )

        query = f"""
ERROR:
{error}

ROOT CAUSE:
{root_cause}

RELEVANT FILES:
{relevant_files}
""".strip()

        return self.store.search(
            query=query,
            n_results=settings.MEMORY_TOP_K,
            project_path=state.get(
                "project_path"
            ),
        )

    def format_memories(
        self,
        memories: List[Dict[str, Any]],
    ) -> str:
        """
        Format retrieved memories so they can be
        passed into the agent context.
        """

        if not memories:
            return (
                "No previous repair memories were found."
            )

        output = [
            "PREVIOUS REPAIR MEMORIES",
            "=" * 50,
        ]

        max_chars = settings.MEMORY_MAX_CONTEXT_CHARS

        current_length = 0

        for index, memory in enumerate(
            memories,
            start=1,
        ):

            document = memory.get(
                "document",
                "",
            )

            block = (
                f"\nMEMORY {index}\n"
                f"{document}\n"
            )

            if (
                current_length + len(block)
                > max_chars
            ):
                break

            output.append(block)

            current_length += len(block)

        return "\n".join(output)
