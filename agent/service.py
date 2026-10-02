from agent.graph import (
    build_graph,
    build_repair_graph,
)


# ============================================================
# INITIAL PROJECT ANALYSIS
# ============================================================

def analyze_project(
    project_path,
    error_message,
):
    """
    Run the initial multi-agent analysis workflow.

    Phase 1-5 functionality preserved:

    1. Project structure analysis
    2. Relevant file discovery
    3. Dependency analysis
    4. Error analysis
    5. Root-cause analysis
    6. Automated test generation
    7. Generated test validation
    8. Generated test execution
    9. Fix planning
    10. Patch generation
    11. Patch security review
    12. Human approval

    Phase 6:

    The above responsibilities are coordinated by the
    multi-agent architecture.

    The workflow stops before applying any patch.
    """

    # ========================================================
    # BUILD PHASE 6 ANALYSIS GRAPH
    # ========================================================

    graph = build_graph()

    # ========================================================
    # INITIAL STATE
    # ========================================================

    initial_state = {

        # ----------------------------------------------------
        # PROJECT
        # ----------------------------------------------------

        "project_path": project_path,

        "error_message": error_message,

        "project_structure": "",

        "project_files": {},

        "relevant_files": [],

        "project_summary": "",

        "project_index": {},

        "dependency_map": {},

        # ----------------------------------------------------
        # ERROR ANALYSIS
        # ----------------------------------------------------

        "error_analysis": "",

        "root_cause": "",

        # ----------------------------------------------------
        # FIX PLANNING
        # ----------------------------------------------------

        "proposed_fix": "",

        "patch": {},

        "patch_error": "",

        "changes": [],

        # ----------------------------------------------------
        # SECURITY
        # ----------------------------------------------------

        "patch_review": {},

        "patch_risk_level": "",

        "security_findings": [],

        "security_warnings": [],

        # ----------------------------------------------------
        # TEST EXECUTION
        # ----------------------------------------------------

        "test_output": "",

        "test_passed": False,

        "test_return_code": -1,

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        "validation_passed": False,

        "validation_error": "",

        # ----------------------------------------------------
        # HUMAN APPROVAL
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # Initial analysis must NEVER automatically approve
        # the generated patch.
        # ----------------------------------------------------

        "approval_required": True,

        "approved": False,

        "human_approved": False,

        # ----------------------------------------------------
        # PHASE 5
        # AUTOMATED TEST GENERATION
        # ----------------------------------------------------

        "generated_test_code": "",

        "generated_test_filename": "",

        "generated_test_reason": "",

        "generated_test_output": "",

        "generated_test_passed": False,

        "generated_test_status": "",

        "generated_test_context": "",

        "test_generation_error": "",

        "test_generation_status": "",

        # ----------------------------------------------------
        # GIT
        # ----------------------------------------------------

        "checkpoint": "",

        # ----------------------------------------------------
        # EXECUTION STATUS
        # ----------------------------------------------------

        "status": "starting",

        "iteration": 1,

        "max_iterations": 5,

        # ----------------------------------------------------
        # RETRY
        # ----------------------------------------------------

        "retry_history": [],

        "previous_test_output": "",

        "previous_patch": {},

        # ----------------------------------------------------
        # AUDIT
        # ----------------------------------------------------

        "audit_log": [],

        # ====================================================
        # PHASE 6
        # MULTI-AGENT STATE
        # ====================================================

        "multi_agent_analysis_completed": False,

        "multi_agent_repair_completed": False,

        "current_agent": "",

        "agent_history": [],

        "agent_errors": [],
    }

    # ========================================================
    # RUN GRAPH
    # ========================================================

    result = graph.invoke(
        initial_state
    )

    return result


# ============================================================
# APPROVED SELF-HEALING REPAIR
# ============================================================

def repair_project(
    state,
):
    """
    Run the approved self-healing repair workflow.

    This function can ONLY continue after explicit human
    approval.

    Existing workflow preserved:

        Patch Review
              ↓
        Git Checkpoint
              ↓
        Apply Patch
              ↓
        Run Tests
              ↓
        Validation
              ↓
        PASS

    OR:

        Tests Failed
              ↓
        Increment Iteration
              ↓
        Refresh Context
              ↓
        Phase 6 Multi-Agent Analysis
              ↓
        Patch Review
              ↓
        Checkpoint
              ↓
        Apply
              ↓
        Test
              ↓
        Validation

    Maximum iterations are controlled by max_iterations.

    If the maximum number of iterations is reached and the
    repair is unsuccessful, the existing rollback mechanism
    is used.
    """

    # ========================================================
    # HUMAN APPROVAL CHECK
    # ========================================================

    approved = bool(
        state.get(
            "approved",
            False,
        )
    )

    human_approved = bool(
        state.get(
            "human_approved",
            False,
        )
    )

    approval_required = bool(
        state.get(
            "approval_required",
            True,
        )
    )

    # ========================================================
    # DISPLAY APPROVAL STATE
    # ========================================================

    print()

    print(
        "=" * 60
    )

    print(
        "REPAIR PROJECT - HUMAN APPROVAL CHECK"
    )

    print(
        "=" * 60
    )

    print(
        "Approved:",
        approved,
    )

    print(
        "Human Approved:",
        human_approved,
    )

    print(
        "Approval Required:",
        approval_required,
    )

    print(
        "=" * 60
    )

    # ========================================================
    # APPROVAL LOGIC
    # ========================================================
    #
    # Repair is allowed only when:
    #
    #     approved OR human_approved
    #
    # AND:
    #
    #     approval_required == False
    #
    # This keeps the human approval gate intact.
    # ========================================================

    approval_confirmed = (
        (
            approved
            or human_approved
        )
        and not approval_required
    )

    if not approval_confirmed:

        raise PermissionError(
            "Repair cannot start without "
            "human approval."
        )

    # ========================================================
    # NORMALIZE APPROVAL STATE
    # ========================================================
    #
    # Keep all approval flags synchronized for the complete
    # repair workflow.
    # ========================================================

    state["approved"] = True

    state["human_approved"] = True

    state["approval_required"] = False

    # ========================================================
    # DEFAULT RETRY STATE
    # ========================================================

    state.setdefault(
        "retry_history",
        [],
    )

    state.setdefault(
        "previous_test_output",
        "",
    )

    state.setdefault(
        "previous_patch",
        {},
    )

    state.setdefault(
        "iteration",
        1,
    )

    state.setdefault(
        "max_iterations",
        5,
    )

    state.setdefault(
        "changes",
        [],
    )

    state.setdefault(
        "checkpoint",
        "",
    )

    state.setdefault(
        "audit_log",
        [],
    )

    # ========================================================
    # PHASE 5 GENERATED TEST DEFAULTS
    # ========================================================

    state.setdefault(
        "generated_test_code",
        "",
    )

    state.setdefault(
        "generated_test_filename",
        "",
    )

    state.setdefault(
        "generated_test_reason",
        "",
    )

    state.setdefault(
        "generated_test_output",
        "",
    )

    state.setdefault(
        "generated_test_passed",
        False,
    )

    state.setdefault(
        "generated_test_status",
        "",
    )

    state.setdefault(
        "generated_test_context",
        "",
    )

    state.setdefault(
        "test_generation_error",
        "",
    )

    state.setdefault(
        "test_generation_status",
        "",
    )

    # ========================================================
    # PHASE 6 MULTI-AGENT DEFAULTS
    # ========================================================

    state.setdefault(
        "multi_agent_analysis_completed",
        False,
    )

    state.setdefault(
        "multi_agent_repair_completed",
        False,
    )

    state.setdefault(
        "current_agent",
        "",
    )

    state.setdefault(
        "agent_history",
        [],
    )

    state.setdefault(
        "agent_errors",
        [],
    )

    # ========================================================
    # SECURITY / APPROVAL STATE
    # ========================================================
    #
    # Explicitly preserve these values before passing the
    # state into LangGraph.
    # ========================================================

    state["approved"] = True

    state["human_approved"] = True

    state["approval_required"] = False

    # ========================================================
    # START REPAIR GRAPH
    # ========================================================

    graph = build_repair_graph()

    result = graph.invoke(
        state
    )

    return result