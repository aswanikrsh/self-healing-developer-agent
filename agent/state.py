
from typing import TypedDict, List, Dict, Any


# ============================================================
# AGENT STATE
# ============================================================
#
# This is the shared state used by the LangGraph workflow.
#
# IMPORTANT:
# There must be only ONE AgentState definition in this file.
#
# The state contains:
#
# Phase 1  - Core repair
# Phase 2  - Self-healing retry loop
# Phase 3  - Project intelligence
# Phase 4  - Security + human approval
# Phase 5  - Automated test generation
#
# ============================================================


class AgentState(TypedDict, total=False):

    # ========================================================
    # PROJECT
    # ========================================================

    project_path: str

    project_structure: str

    project_files: Dict[str, str]

    relevant_files: List[str]

    project_summary: str

    project_index: Dict[str, Any]

    dependency_map: Dict[str, Any]


    # ========================================================
    # ERROR ANALYSIS
    # ========================================================

    error_message: str

    error_analysis: str

    root_cause: str


    # ========================================================
    # FIX
    # ========================================================

    proposed_fix: str

    patch: Dict[str, Any]

    patch_error: str

    changes: List[str]


    # ========================================================
    # PATCH SECURITY
    # ========================================================

    patch_review: Dict[str, Any]

    patch_risk_level: str

    security_findings: List[Any]

    security_warnings: List[Any]


    # ========================================================
    # TESTING
    # ========================================================

    test_output: str

    test_passed: bool

    test_return_code: int


    # ========================================================
    # VALIDATION
    # ========================================================

    validation_passed: bool

    validation_error: str


    # ========================================================
    # APPROVAL
    # ========================================================
    #
    # approval_required:
    #     True  -> human approval is still required
    #     False -> approval requirement has been satisfied
    #
    # approved:
    #     Backward-compatible approval flag.
    #
    # human_approved:
    #     Explicit human approval flag used by the repair engine.
    #
    # ========================================================

    approval_required: bool

    approved: bool

    human_approved: bool


    # ========================================================
    # GIT
    # ========================================================

    checkpoint: str


    # ========================================================
    # EXECUTION
    # ========================================================

    status: str

    iteration: int

    max_iterations: int


    # ========================================================
    # RETRY
    # ========================================================

    retry_history: List[Dict[str, Any]]

    previous_test_output: str

    previous_patch: Dict[str, Any]


    # ========================================================
    # PHASE 5
    # AUTOMATED TEST GENERATION
    # ========================================================
    #
    # Generated tests are created by the AI and executed
    # temporarily. They are not automatically added to the
    # user's project.
    #
    # ========================================================

    generated_test_code: str

    generated_test_filename: str

    generated_test_reason: str

    generated_test_output: str

    generated_test_passed: bool

    generated_test_status: str

    generated_test_context: str

    test_generation_error: str

    test_generation_status: str


    # ========================================================
    # AUDIT
    # ========================================================

    audit_log: List[Dict[str, Any]]


    # ========================================================
    # SESSION
    # ========================================================

    session_id: int


# ============================================================
# PHASE 6 - MULTI-AGENT ARCHITECTURE
# ============================================================

multi_agent_analysis_completed: bool
multi_agent_repair_completed: bool
current_agent: str
agent_history: list
agent_errors: list


# ========================================================
# PHASE 7 - MEMORY
# ========================================================
memory_context: str
retrieved_memories: list
memory_search_status: str
memory_error: str
memory_saved: bool
memory_id: str