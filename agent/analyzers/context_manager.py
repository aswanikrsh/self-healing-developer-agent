from agent.analyzers.project_analyzer import (
    analyze_project,
    read_project_files,
)


# ============================================================
# REFRESH PROJECT CONTEXT
# ============================================================

def refresh_project_context(
    state,
):
    """
    Re-analyze the project after a failed repair.

    This is important for Phase 2 + Phase 3 because
    the source code may have changed after a patch.
    """

    result = analyze_project(
        state["project_path"],
        state.get(
            "error_message",
            "",
        ),
    )

    state["project_structure"] = (
        result["structure"]
    )

    state["relevant_files"] = (
        result["files"]
    )

    state["project_files"] = (
        read_project_files(
            state["project_path"],
            result["files"],
        )
    )

    state["project_index"] = (
        result["metadata"]
    )

    state["dependency_map"] = (
        result["dependency_map"]
    )

    state["project_summary"] = (
        result["summary"]
    )

    return state