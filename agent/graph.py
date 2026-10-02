from langgraph.graph import (
    StateGraph,
    END,
)


from agent.multi_agent import (
    multi_agent_analysis_node,
    save_successful_memory_node,
)

from agent.state import AgentState

# ============================================================
# PHASE 6
# MULTI-AGENT ORCHESTRATION
# ============================================================

from agent.multi_agent import (
    multi_agent_analysis_node,
)


# ============================================================
# EXISTING CORE NODES
# ============================================================

from agent.nodes import (
    patch_review_node,
    checkpoint_node,
    apply_patch_node,
    test_runner_node,
    validation_node,
    increment_iteration_node,
    refresh_context_node,
    rollback_node,
)


def build_repair_graph():
    graph = StateGraph(AgentState)

    graph.add_node(
        "patch_review",
        patch_review_node,
    )

    graph.add_node(
        "checkpoint",
        checkpoint_node,
    )

    graph.add_node(
        "apply_patch",
        apply_patch_node,
    )

    graph.add_node(
        "test_runner",
        test_runner_node,
    )

    graph.add_node(
        "validation",
        validation_node,
    )

    graph.add_node(
        "increment_iteration",
        increment_iteration_node,
    )

    graph.add_node(
        "refresh_context",
        refresh_context_node,
    )

    graph.add_node(
        "multi_agent_analysis",
        multi_agent_analysis_node,
    )

    graph.add_node(
        "rollback",
        rollback_node,
    )

    # ========================================================
    # PHASE 7
    # ========================================================

    graph.add_node(
        "save_successful_memory",
        save_successful_memory_node,
    )

    # ========================================================
    # ENTRY
    # ========================================================

    graph.set_entry_point(
        "patch_review"
    )

    # ========================================================
    # PATCH REVIEW ROUTING
    # ========================================================

    def route_after_review(state):
        if state.get("patch_error"):

            if (
                state.get("iteration", 1)
                >= state.get(
                    "max_iterations",
                    5,
                )
            ):
                return "rollback"

            return "retry"

        return "checkpoint"

    graph.add_conditional_edges(
        "patch_review",
        route_after_review,
        {
            "checkpoint": "checkpoint",
            "retry": "increment_iteration",
            "rollback": "rollback",
        },
    )

    # ========================================================
    # CHECKPOINT
    # ========================================================

    graph.add_edge(
        "checkpoint",
        "apply_patch",
    )

    # ========================================================
    # PATCH APPLICATION ROUTING
    # ========================================================

    def route_after_patch(state):

        if state.get("patch_error"):

            if (
                state.get("iteration", 1)
                >= state.get(
                    "max_iterations",
                    5,
                )
            ):
                return "rollback"

            return "retry"

        return "test"

    graph.add_conditional_edges(
        "apply_patch",
        route_after_patch,
        {
            "test": "test_runner",
            "retry": "increment_iteration",
            "rollback": "rollback",
        },
    )

    # ========================================================
    # TEST RUNNER
    # ========================================================

    graph.add_edge(
        "test_runner",
        "validation",
    )

    # ========================================================
    # VALIDATION ROUTING
    # ========================================================

    def route_after_validation(state):

        if state.get(
            "test_passed",
            False,
        ):
            return "success"

        if (
            state.get("iteration", 1)
            >= state.get(
                "max_iterations",
                5,
            )
        ):
            return "rollback"

        return "retry"

    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "success": "save_successful_memory",
            "retry": "increment_iteration",
            "rollback": "rollback",
        },
    )

    # ========================================================
    # PHASE 7 MEMORY SAVE
    # ========================================================

    graph.add_edge(
        "save_successful_memory",
        END,
    )

    # ========================================================
    # RETRY LOOP
    # ========================================================

    graph.add_edge(
        "increment_iteration",
        "refresh_context",
    )

    graph.add_edge(
        "refresh_context",
        "multi_agent_analysis",
    )

    graph.add_edge(
        "multi_agent_analysis",
        "patch_review",
    )

    # ========================================================
    # ROLLBACK
    # ========================================================

    graph.add_edge(
        "rollback",
        END,
    )

    return graph.compile()



# ============================================================
# ANALYSIS GRAPH
# ============================================================

def build_graph():
    """
    Build the initial analysis graph.

    Phase 6 changes the architecture from a direct sequence of
    individual nodes into a multi-agent analysis system.

    Previous architecture:

        Project Analysis
              ↓
        Error Analysis
              ↓
        Test Generation
              ↓
        Fix Planning
              ↓
        Security Review

    Phase 6 architecture:

        Agent Manager
              ↓
        Project Agent
              ↓
        Error Agent
              ↓
        Test Agent
              ↓
        Fix Agent
              ↓
        Security Agent
              ↓
        Human Approval

    IMPORTANT:
    The underlying Phase 1-5 functionality is NOT removed.

    The specialist agents reuse the existing nodes:

        project_analysis_node
        error_analysis_node
        test_generation_node
        fix_planning_node
        patch_review_node
    """

    graph = StateGraph(
        AgentState
    )

    # ========================================================
    # PHASE 6
    # MULTI-AGENT ANALYSIS
    # ========================================================

    graph.add_node(
        "multi_agent_analysis",
        multi_agent_analysis_node,
    )

    # ========================================================
    # SECURITY REVIEW
    # ========================================================

    graph.add_node(
        "patch_review",
        patch_review_node,
    )

    # ========================================================
    # ENTRY POINT
    # ========================================================

    graph.set_entry_point(
        "multi_agent_analysis"
    )

    # ========================================================
    # MULTI-AGENT ANALYSIS
    # ========================================================
    #
    # The Agent Manager coordinates:
    #
    # ProjectAgent
    # ErrorAgent
    # TestAgent
    # FixAgent
    # SecurityAgent
    #
    # The manager returns a state containing all Phase 1-5
    # analysis information.
    # ========================================================

    graph.add_edge(
        "multi_agent_analysis",
        "patch_review",
    )

    # ========================================================
    # PATCH REVIEW
    # ========================================================
    #
    # Initial analysis must stop here.
    #
    # The user must review and approve the proposed patch
    # before repair_project() is allowed to continue.
    # ========================================================

    graph.add_edge(
        "patch_review",
        END,
    )

    # ========================================================
    # COMPILE
    # ========================================================

    return graph.compile()


# ============================================================
# REPAIR GRAPH
# ============================================================

def build_repair_graph():
    """
    Build the approved self-healing repair graph.

    Existing features preserved:

    1. Human approval
    2. Patch security review
    3. Git checkpoint
    4. Safe patch application
    5. Test execution
    6. Validation
    7. Retry loop
    8. Context refresh
    9. Error re-analysis
    10. Phase 5 automated test generation
    11. Fix planning
    12. Patch re-review
    13. Maximum iteration limit
    14. Rollback

    Phase 6 change:

    On retry, the refreshed project is sent through the
    multi-agent analysis coordinator instead of directly
    calling error_analysis_node.
    """

    graph = StateGraph(
        AgentState
    )

    # ========================================================
    # PATCH REVIEW
    # ========================================================

    graph.add_node(
        "patch_review",
        patch_review_node,
    )

    # ========================================================
    # GIT CHECKPOINT
    # ========================================================

    graph.add_node(
        "checkpoint",
        checkpoint_node,
    )

    # ========================================================
    # PATCH APPLICATION
    # ========================================================

    graph.add_node(
        "apply_patch",
        apply_patch_node,
    )

    # ========================================================
    # TEST RUNNER
    # ========================================================

    graph.add_node(
        "test_runner",
        test_runner_node,
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    graph.add_node(
        "validation",
        validation_node,
    )

    # ========================================================
    # RETRY ITERATION
    # ========================================================

    graph.add_node(
        "increment_iteration",
        increment_iteration_node,
    )

    # ========================================================
    # PROJECT CONTEXT REFRESH
    # ========================================================

    graph.add_node(
        "refresh_context",
        refresh_context_node,
    )

    # ========================================================
    # PHASE 6
    # MULTI-AGENT ANALYSIS
    # ========================================================

    graph.add_node(
        "multi_agent_analysis",
        multi_agent_analysis_node,
    )

    # ========================================================
    # ROLLBACK
    # ========================================================

    graph.add_node(
        "rollback",
        rollback_node,
    )

    # ========================================================
    # ENTRY POINT
    # ========================================================

    graph.set_entry_point(
        "patch_review"
    )

    # ========================================================
    # SECURITY REVIEW ROUTING
    # ========================================================

    def route_after_review(
        state
    ):
        """
        Decide what happens after patch/security review.
        """

        # ----------------------------------------------------
        # PATCH REVIEW FAILED
        # ----------------------------------------------------

        if state.get(
            "patch_error"
        ):

            # ------------------------------------------------
            # MAXIMUM ITERATIONS
            # ------------------------------------------------

            if state.get(
                "iteration",
                1,
            ) >= state.get(
                "max_iterations",
                5,
            ):

                return "rollback"

            # ------------------------------------------------
            # RETRY
            # ------------------------------------------------

            return "retry"

        # ----------------------------------------------------
        # PATCH REVIEW PASSED
        # ----------------------------------------------------

        return "checkpoint"

    graph.add_conditional_edges(
        "patch_review",
        route_after_review,
        {
            "checkpoint": "checkpoint",
            "retry": "increment_iteration",
            "rollback": "rollback",
        },
    )

    # ========================================================
    # CHECKPOINT
    # ========================================================

    graph.add_edge(
        "checkpoint",
        "apply_patch",
    )

    # ========================================================
    # PATCH APPLICATION ROUTING
    # ========================================================

    def route_after_patch(
        state
    ):
        """
        Decide what happens after patch application.
        """

        # ----------------------------------------------------
        # PATCH APPLICATION FAILED
        # ----------------------------------------------------

        if state.get(
            "patch_error"
        ):

            # ------------------------------------------------
            # MAXIMUM ITERATIONS
            # ------------------------------------------------

            if state.get(
                "iteration",
                1,
            ) >= state.get(
                "max_iterations",
                5,
            ):

                return "rollback"

            # ------------------------------------------------
            # RETRY
            # ------------------------------------------------

            return "retry"

        # ----------------------------------------------------
        # PATCH APPLIED
        # ----------------------------------------------------

        return "test"

    graph.add_conditional_edges(
        "apply_patch",
        route_after_patch,
        {
            "test": "test_runner",
            "retry": "increment_iteration",
            "rollback": "rollback",
        },
    )

    # ========================================================
    # TEST RUNNER
    # ========================================================

    graph.add_edge(
        "test_runner",
        "validation",
    )

    # ========================================================
    # VALIDATION ROUTING
    # ========================================================

    def route_after_validation(
        state
    ):
        """
        Decide whether the repair succeeded or another
        self-healing iteration is required.
        """

        # ----------------------------------------------------
        # TESTS PASSED
        # ----------------------------------------------------

        if state.get(
            "test_passed",
            False,
        ):

            return "success"

        # ----------------------------------------------------
        # MAXIMUM ITERATIONS REACHED
        # ----------------------------------------------------

        if state.get(
            "iteration",
            1,
        ) >= state.get(
            "max_iterations",
            5,
        ):

            return "rollback"

        # ----------------------------------------------------
        # TESTS FAILED
        # ----------------------------------------------------
        #
        # Start another self-healing iteration.
        # ----------------------------------------------------

        return "retry"

    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "success": END,
            "retry": "increment_iteration",
            "rollback": "rollback",
        },
    )

    # ========================================================
    # RETRY ITERATION
    # ========================================================

    graph.add_edge(
        "increment_iteration",
        "refresh_context",
    )

    # ========================================================
    # REFRESH PROJECT CONTEXT
    # ========================================================
    #
    # The project may have changed during the previous
    # iteration, so the context must be refreshed before
    # another analysis.
    # ========================================================

    graph.add_edge(
        "refresh_context",
        "multi_agent_analysis",
    )

    # ========================================================
    # PHASE 6 MULTI-AGENT ANALYSIS
    # ========================================================
    #
    # On every retry, the complete specialist-agent analysis
    # runs again:
    #
    # Project Agent
    #       ↓
    # Error Agent
    #       ↓
    # Test Agent
    #       ↓
    # Fix Agent
    #       ↓
    # Security Agent
    #
    # This replaces the old direct:
    #
    # refresh_context → error_analysis → test_generation
    #
    # chain while preserving all underlying functionality.
    # ========================================================

    graph.add_edge(
        "multi_agent_analysis",
        "patch_review",
    )

    # ========================================================
    # ROLLBACK
    # ========================================================

    graph.add_edge(
        "rollback",
        END,
    )

    # ========================================================
    # COMPILE GRAPH
    # ========================================================

    return graph.compile()