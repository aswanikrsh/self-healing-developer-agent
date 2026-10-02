from typing import Any, Dict

from agent.agents.manager import AgentManager
from agent.memory import MemoryManager


# ============================================================
# PHASE 6 - AGENT MANAGER
# ============================================================

manager = AgentManager()


def get_memory_manager() -> MemoryManager:
    """
    Create the Phase 7 MemoryManager only when it is needed.

    This avoids accessing Django settings during module import.
    Django settings are therefore required only when a LangGraph
    node actually executes.
    """
    return MemoryManager()


# ============================================================
# PHASE 6 + PHASE 7
# MULTI-AGENT ANALYSIS
# ============================================================

def multi_agent_analysis_node(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    LangGraph node for Phase 6 multi-agent analysis.

    Phase 7 addition:
    Before running the specialist agents, search ChromaDB for
    previous successful repairs that are semantically similar
    to the current error.

    Previous memories are advisory context only.
    The Fix Agent must still inspect the current source code
    and generate a new safe patch.
    """

    state["current_agent"] = "AgentManager"

    state.setdefault("agent_history", [])
    state.setdefault("agent_errors", [])

    # --------------------------------------------------------
    # PHASE 7 - RETRIEVE PREVIOUS REPAIR MEMORIES
    # --------------------------------------------------------

    try:
        memory_manager = get_memory_manager()

        print("\n" + "=" * 60)
        print("PHASE 7 - PROJECT MEMORY")
        print("=" * 60)

        print("Searching previous repair memories...")

        memories = memory_manager.search_similar_repairs(
            state
        )

        state["retrieved_memories"] = memories

        state["memory_context"] = (
            memory_manager.format_memories(
                memories
            )
        )

        state["memory_search_status"] = "completed"
        state["memory_error"] = ""

        print(
            f"MEMORY SEARCH COMPLETE: "
            f"{len(memories)} memories found"
        )

        if memories:
            print("Previous repair context found.")
        else:
            print("No previous repair memories found.")

    except Exception as exc:
        # ----------------------------------------------------
        # MEMORY MUST NEVER BREAK THE REPAIR ENGINE
        # ----------------------------------------------------

        print(
            "MEMORY SEARCH WARNING: "
            f"{type(exc).__name__}: {exc}"
        )

        state["retrieved_memories"] = []
        state["memory_context"] = (
            "No previous repair memories are available."
        )
        state["memory_search_status"] = "failed"
        state["memory_error"] = str(exc)

    # --------------------------------------------------------
    # PHASE 6 - RUN MULTI-AGENT ANALYSIS
    # --------------------------------------------------------

    try:
        result = manager.run_analysis(state)

        state["agent_history"].extend(
            [
                "ProjectAgent",
                "ErrorAgent",
                "TestAgent",
                "FixAgent",
                "SecurityAgent",
            ]
        )

        state["current_agent"] = "completed"

        state["multi_agent_analysis_completed"] = True

        return result

    except Exception as exc:
        state["agent_errors"].append(
            {
                "agent": state.get(
                    "current_agent",
                    "unknown",
                ),
                "error": str(exc),
            }
        )

        state["status"] = "failed"

        raise


# ============================================================
# PHASE 6
# MULTI-AGENT REPAIR
# ============================================================

def multi_agent_repair_node(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    LangGraph node for Phase 6 repair and validation.

    This keeps the existing Phase 6 RepairAgent and
    ValidationAgent functionality.

    Phase 7 memory is NOT saved here because the repair has
    not necessarily passed tests yet.
    """

    state["current_agent"] = "AgentManager"

    state.setdefault("agent_history", [])
    state.setdefault("agent_errors", [])

    try:
        result = manager.run_repair(state)

        state["agent_history"].extend(
            [
                "RepairAgent",
                "ValidationAgent",
            ]
        )

        state["current_agent"] = "completed"

        state["multi_agent_repair_completed"] = True

        return result

    except Exception as exc:
        state["agent_errors"].append(
            {
                "agent": state.get(
                    "current_agent",
                    "unknown",
                ),
                "error": str(exc),
            }
        )

        state["status"] = "failed"

        raise


# ============================================================
# PHASE 7
# SAVE SUCCESSFUL REPAIR MEMORY
# ============================================================

def save_successful_memory_node(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Save the successful repair to ChromaDB.

    This node should run ONLY after:
    
    1. Patch generation
    2. Security review
    3. Human approval
    4. Git checkpoint
    5. Patch application
    6. Test execution
    7. Validation PASS

    Failed repairs are never stored as successful memories.
    """

    state.setdefault("memory_saved", False)
    state.setdefault("memory_id", "")
    state.setdefault("memory_error", "")

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if not state.get("test_passed", False):
        print(
            "MEMORY SAVE SKIPPED: "
            "Tests did not pass."
        )

        state["memory_saved"] = False

        return state

    try:
        memory_manager = get_memory_manager()

        print("\n" + "=" * 60)
        print("PHASE 7 - SAVING SUCCESSFUL REPAIR")
        print("=" * 60)

        memory_id = (
            memory_manager.save_successful_repair(
                state
            )
        )

        if memory_id:
            state["memory_saved"] = True
            state["memory_id"] = memory_id
            state["memory_error"] = ""

            print(
                "MEMORY SAVED SUCCESSFULLY"
            )
            print(
                f"Memory ID: {memory_id}"
            )

        else:
            state["memory_saved"] = False

            print(
                "MEMORY SAVE SKIPPED"
            )

        return state

    except Exception as exc:
        # ----------------------------------------------------
        # MEMORY IS AN ENHANCEMENT, NOT A HARD DEPENDENCY
        # ----------------------------------------------------

        print(
            "MEMORY SAVE WARNING: "
            f"{type(exc).__name__}: {exc}"
        )

        state["memory_saved"] = False
        state["memory_id"] = ""
        state["memory_error"] = str(exc)

        # Do NOT fail the repair because memory failed.

        return state
