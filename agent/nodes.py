
from agent.analyzers.project_analyzer import (
    analyze_project,
    read_project_files,
)

from agent.analyzers.context_manager import (
    refresh_project_context,
)

from agent.analyzers.error_analyzer import (
    analyze_error,
)

from agent.analyzers.fix_planner import (
    create_fix_plan,
)

from agent.tools.git_tools import (
    create_checkpoint,
    rollback_to_checkpoint,
)

from agent.tools.patch_tools import (
    apply_patch,
)

from agent.tools.test_tools import (
    run_tests,
)

from agent.security.patch_reviewer import (
    review_patch,
    format_patch_review,
)

from agent.security.audit import (
    add_audit_event,
)

# ============================================================
# TEST GENERATION
# ============================================================

from agent.analyzers.test_generator import (
    generate_tests,
    run_generated_test,
)


# ============================================================
# PROJECT ANALYSIS
# ============================================================

def project_analysis_node(state):

    print("\n")
    print("=" * 60)
    print("PHASE 3 + PHASE 4 PROJECT INTELLIGENCE")
    print("=" * 60)

    result = analyze_project(
        state["project_path"],
        state.get("error_message", ""),
    )

    state["project_structure"] = result["structure"]

    state["relevant_files"] = result["files"]

    state["project_files"] = read_project_files(
        state["project_path"],
        result["files"],
    )

    state["project_index"] = result.get(
        "metadata",
        {},
    )

    state["dependency_map"] = result.get(
        "dependency_map",
        {},
    )

    state["project_summary"] = result.get(
        "summary",
        "",
    )

    state = add_audit_event(
        state,
        "project_analyzed",
        {
            "relevant_files": result["files"],
        },
    )

    print("\nRELEVANT FILES:")

    for file_name in result["files"]:
        print(f"  - {file_name}")

    print("\nDEPENDENCIES:")

    for source, dependencies in result.get(
        "dependency_map",
        {},
    ).items():

        print(f"  {source}")

        for dependency in dependencies:
            print(f"      -> {dependency}")

    return state


# ============================================================
# REFRESH CONTEXT
# ============================================================

def refresh_context_node(state):

    print("\n")
    print("=" * 60)
    print("PROJECT CONTEXT REFRESH")
    print("=" * 60)

    state = refresh_project_context(state)

    print("\nRELEVANT FILES:")

    for file_name in state.get(
        "relevant_files",
        [],
    ):

        print(f"  - {file_name}")

    state = add_audit_event(
        state,
        "project_context_refreshed",
        {
            "iteration": state.get(
                "iteration",
                1,
            ),
        },
    )

    return state


# ============================================================
# ERROR ANALYSIS
# ============================================================

def error_analysis_node(state):

    print("\n")
    print("=" * 60)
    print("ERROR ANALYSIS")
    print("=" * 60)

    analysis = analyze_error(
        error=state["error_message"],
        project_structure=state["project_structure"],
        project_files=state["project_files"],
        previous_test_output=state.get(
            "previous_test_output",
            "",
        ),
        previous_patch=state.get(
            "previous_patch",
            {},
        ),
    )

    state["error_analysis"] = analysis

    # --------------------------------------------------------
    # PROJECT SUMMARY
    # --------------------------------------------------------

    summary = state.get(
        "project_summary",
        "",
    )

    if summary:

        state["error_analysis"] += (
            "\n\nPROJECT SUMMARY:\n"
            + summary
        )

    state = add_audit_event(
        state,
        "error_analyzed",
        {
            "iteration": state.get(
                "iteration",
                1,
            ),
        },
    )

    print(analysis)

    return state


# ============================================================
# AUTOMATED TEST GENERATION
# ============================================================
#
# IMPORTANT:
#
# This function was renamed from:
#
#     test_generation_node
#
# to:
#
#     generate_tests_node
#
# because pytest automatically discovers functions whose names
# start with "test_". This function is an AGENT NODE, not a
# pytest test function.
#
# No Phase 5 functionality has been removed.
# ============================================================

def generate_tests_node(state):
    """
    Generate tests for the current failure.

    Generated tests are executed in a temporary directory.
    They do not modify the user's project.
    """

    print("\n")
    print("=" * 60)
    print(
        "AUTOMATED TEST GENERATION - ITERATION",
        state.get("iteration", 1),
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Reset previous generation state
    # --------------------------------------------------------

    state["generated_test_code"] = ""
    state["generated_test_filename"] = ""
    state["generated_test_reason"] = ""
    state["generated_test_output"] = ""
    state["generated_test_passed"] = False
    state["test_generation_error"] = ""

    try:

        # ----------------------------------------------------
        # Generate tests
        # ----------------------------------------------------

        generated = generate_tests(
            error=state["error_message"],
            root_cause=state.get(
                "root_cause",
                state.get(
                    "error_analysis",
                    "",
                ),
            ),
            project_files=state["project_files"],
            project_structure=state.get(
                "project_structure",
                "",
            ),
        )

        state["generated_test_code"] = (
            generated["test_code"]
        )

        state["generated_test_filename"] = (
            generated["filename"]
        )

        state["generated_test_reason"] = (
            generated["reason"]
        )

        print("\nGENERATED TEST FILE:")
        print(generated["filename"])

        print("\nGENERATED TEST REASON:")
        print(generated["reason"])

        print("\nGENERATED TEST CODE:")
        print(generated["test_code"])

        # ----------------------------------------------------
        # Execute generated test
        # ----------------------------------------------------

        result = run_generated_test(
            state["project_path"],
            generated["test_code"],
        )

        state["generated_test_output"] = (
            result.get(
                "output",
                "",
            )
        )

        state["generated_test_passed"] = bool(
            result.get(
                "passed",
                False,
            )
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        if state["generated_test_passed"]:

            state["test_generation_status"] = (
                "passed"
            )

            print("\nGENERATED TEST RESULT:")
            print("PASSED")

        else:

            state["test_generation_status"] = (
                "failed"
            )

            print("\nGENERATED TEST RESULT:")
            print("FAILED")

        print("\nGENERATED TEST OUTPUT:")
        print(state["generated_test_output"])

    except Exception as exc:

        state["test_generation_status"] = (
            "failed"
        )

        state["test_generation_error"] = (
            f"{type(exc).__name__}: {exc}"
        )

        print("\nTEST GENERATION FAILED:")
        print(type(exc).__name__)
        print(str(exc))

    # --------------------------------------------------------
    # Add generated-test information to repair context
    # --------------------------------------------------------

    generated_context = ""

    if state.get("generated_test_code"):

        generated_context = f"""
============================================================
AI GENERATED TEST
============================================================

{state["generated_test_code"]}

============================================================
GENERATED TEST EXECUTION
============================================================

{state.get("generated_test_output", "")}

============================================================
TEST GENERATION REASON
============================================================

{state.get("generated_test_reason", "")}
"""

    state["generated_test_context"] = (
        generated_context
    )

    state["status"] = "tests_generated"

    print("=" * 60)

    return state


# ============================================================
# FIX PLANNING
# ============================================================

def fix_planning_node(state):

    print("\n")
    print("=" * 60)
    print(
        "FIX PLANNING - ITERATION",
        state.get(
            "iteration",
            1,
        ),
    )
    print("=" * 60)

    try:

        # ====================================================
        # PREVIOUS TEST OUTPUT
        # ====================================================

        previous_test_output = state.get(
            "previous_test_output",
            "",
        )

        # ====================================================
        # PHASE 5
        # GENERATED TEST CONTEXT
        # ====================================================

        generated_test_context = state.get(
            "generated_test_context",
            "",
        )

        # ----------------------------------------------------
        # Add generated test information to planner context
        # ----------------------------------------------------

        if generated_test_context:

            previous_test_output = (
                previous_test_output
                + "\n\n"
                + "==================================================\n"
                + "PHASE 5 - GENERATED TEST CONTEXT\n"
                + "==================================================\n"
                + generated_test_context
            )

        # ====================================================
        # CREATE FIX PLAN
        # ====================================================

        patch = create_fix_plan(
            error=state["error_message"],
            root_cause=state.get(
                "error_analysis",
                "",
            ),
            project_files=state["project_files"],
            previous_test_output=previous_test_output,
            previous_patch=state.get(
                "previous_patch",
                {},
            ),
        )

        # ====================================================
        # VALIDATE RETURNED PATCH
        # ====================================================

        if not patch:

            raise ValueError(
                "Fix planner returned an empty patch."
            )

        if not isinstance(
            patch,
            dict,
        ):

            raise ValueError(
                "Fix planner did not return a patch dictionary."
            )

        # ----------------------------------------------------
        # Required patch fields
        # ----------------------------------------------------

        required_fields = [
            "file",
            "old_code",
            "new_code",
            "reason",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in patch
        ]

        if missing_fields:

            raise ValueError(
                "Generated patch is missing required "
                f"fields: {missing_fields}"
            )

        # ====================================================
        # BASIC PATCH CONTENT VALIDATION
        # ====================================================

        if not patch.get("file"):

            raise ValueError(
                "Generated patch does not specify a target file."
            )

        if not isinstance(
            patch.get("old_code"),
            str,
        ):

            raise ValueError(
                "Patch old_code must be a string."
            )

        if not isinstance(
            patch.get("new_code"),
            str,
        ):

            raise ValueError(
                "Patch new_code must be a string."
            )

        if not isinstance(
            patch.get("reason"),
            str,
        ):

            raise ValueError(
                "Patch reason must be a string."
            )

        # ====================================================
        # STORE FINAL PATCH
        # ====================================================

        state["patch"] = patch

        state["proposed_fix"] = patch.get(
            "reason",
            "",
        )

        state["patch_error"] = ""

        # ====================================================
        # PRINT PATCH
        # ====================================================

        print("\nNEW PATCH GENERATED:")
        print(patch)

        # ====================================================
        # PHASE 5 INFORMATION
        # ====================================================

        if generated_test_context:

            print("\nPHASE 5 TEST CONTEXT:")

            print(
                "Generated tests were provided "
                "to the Fix Planner."
            )

        # ====================================================
        # AUDIT EVENT
        # ====================================================

        state = add_audit_event(
            state,
            "patch_generated",
            {
                "file": patch.get("file"),
                "reason": patch.get("reason"),
                "generated_test_used": bool(
                    generated_test_context
                ),
            },
        )

        # ====================================================
        # SUCCESS STATUS
        # ====================================================

        state["status"] = "patch_generated"

    except Exception as exc:

        state["patch"] = {}

        state["patch_error"] = str(exc)

        state["proposed_fix"] = ""

        state["status"] = "patch_generation_failed"

        state = add_audit_event(
            state,
            "patch_generation_failed",
            {
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )

        print("\nPATCH GENERATION FAILED:")
        print(type(exc).__name__)
        print(str(exc))

    return state


# ============================================================
# PHASE 4 PATCH SECURITY REVIEW
# ============================================================

def patch_review_node(state):

    print("\n")
    print("=" * 60)
    print("PHASE 4 PATCH SECURITY REVIEW")
    print("=" * 60)

    patch = state.get(
        "patch",
        {},
    )

    # --------------------------------------------------------
    # EMPTY PATCH
    # --------------------------------------------------------

    if not patch:

        state["patch_review"] = {
            "approved_for_review": False,
            "risk_level": "critical",
            "summary": (
                "No patch available for review."
            ),
            "findings": [
                "Patch is empty."
            ],
            "warnings": [],
        }

        state["patch_risk_level"] = "critical"

        state["security_findings"] = [
            "Patch is empty."
        ]

        state["security_warnings"] = []

        state["patch_error"] = (
            "No patch was generated."
        )

        state = add_audit_event(
            state,
            "patch_security_review_blocked",
            {
                "reason": "Patch is empty.",
            },
        )

        print(
            "PATCH SECURITY REVIEW BLOCKED:"
        )

        print(
            "No patch was generated."
        )

        return state

    # --------------------------------------------------------
    # SECURITY REVIEW
    # --------------------------------------------------------

    try:

        review = review_patch(
            state["project_path"],
            patch,
        )

        state["patch_review"] = review

        state["patch_risk_level"] = review.get(
            "risk_level",
            "unknown",
        )

        state["security_findings"] = review.get(
            "findings",
            [],
        )

        state["security_warnings"] = review.get(
            "warnings",
            [],
        )

        state["patch_error"] = ""

        print(
            format_patch_review(
                review
            )
        )

        state = add_audit_event(
            state,
            "patch_security_reviewed",
            {
                "risk_level": review.get(
                    "risk_level"
                ),
                "findings": review.get(
                    "findings"
                ),
                "warnings": review.get(
                    "warnings"
                ),
            },
        )

        # ----------------------------------------------------
        # Critical security problems
        # ----------------------------------------------------

        if review.get(
            "risk_level"
        ) == "critical":

            state["patch_error"] = (
                "Patch blocked by Phase 4 "
                "security review."
            )

            state = add_audit_event(
                state,
                "patch_blocked_security",
                {
                    "risk_level": "critical",
                },
            )

            print(
                "PATCH BLOCKED BY SECURITY REVIEW"
            )

    except Exception as exc:

        state["patch_error"] = (
            "Patch security review failed: "
            + str(exc)
        )

        state["patch_review"] = {
            "approved_for_review": False,
            "risk_level": "critical",
            "summary": (
                "Security review could not be completed."
            ),
            "findings": [
                str(exc)
            ],
            "warnings": [],
        }

        state["patch_risk_level"] = "critical"

        state["security_findings"] = [
            str(exc)
        ]

        state["security_warnings"] = []

        state = add_audit_event(
            state,
            "patch_security_review_failed",
            {
                "error": str(exc),
            },
        )

        print(
            "PATCH SECURITY REVIEW FAILED:"
        )

        print(
            type(exc).__name__
        )

        print(
            str(exc)
        )

    return state


# ============================================================
# CHECKPOINT
# ============================================================

def checkpoint_node(state):

    print("\n")
    print("=" * 60)
    print("CREATING GIT CHECKPOINT")
    print("=" * 60)

    try:

        checkpoint = create_checkpoint(
            state["project_path"]
        )

        state["checkpoint"] = checkpoint

        state = add_audit_event(
            state,
            "git_checkpoint_created",
            {
                "checkpoint": checkpoint,
            },
        )

        print(
            "GIT CHECKPOINT CREATED:"
        )

        print(checkpoint)

    except Exception as exc:

        state["checkpoint"] = ""

        state["patch_error"] = (
            "Git checkpoint failed: "
            + str(exc)
        )

        state = add_audit_event(
            state,
            "git_checkpoint_failed",
            {
                "error": str(exc),
            },
        )

        print(
            "GIT CHECKPOINT FAILED:"
        )

        print(
            type(exc).__name__
        )

        print(
            str(exc)
        )

    return state


# ============================================================
# APPLY PATCH
# ============================================================

def apply_patch_node(state):

    print("\n")
    print("=" * 60)
    print(
        "PATCH APPLICATION - ITERATION",
        state.get(
            "iteration",
            1,
        ),
    )
    print("=" * 60)

    # ========================================================
    # HUMAN APPROVAL CHECK
    # ========================================================
    #
    # The approval view sets:
    #
    #     approved = True
    #     human_approved = True
    #     approval_required = False
    #
    # We accept the explicit human_approved flag as the
    # authoritative approval signal.
    #
    # We also support the older "approved" field so that
    # existing sessions/state remain compatible.
    #
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
            False,
        )
    )

    print("\nHUMAN APPROVAL STATE:")

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

    # --------------------------------------------------------
    # A patch is allowed only when explicit human approval
    # exists AND approval is no longer required.
    #
    # This prevents accidental execution when a state is
    # missing or malformed.
    # --------------------------------------------------------

    approval_confirmed = (
        (approved or human_approved)
        and not approval_required
    )

    if not approval_confirmed:

        state["patch_error"] = (
            "Patch application blocked: "
            "human approval is required."
        )

        state = add_audit_event(
            state,
            "patch_blocked_no_approval",
            {
                "approved": approved,
                "human_approved": human_approved,
                "approval_required": approval_required,
            },
        )

        print("PATCH BLOCKED:")

        print(
            "Human approval required."
        )

        return state

    print(
        "HUMAN APPROVAL CONFIRMED"
    )

    # --------------------------------------------------------
    # Preserve approval throughout the repair loop.
    # --------------------------------------------------------

    state["approved"] = True
    state["human_approved"] = True
    state["approval_required"] = False

    # --------------------------------------------------------
    # SECURITY CHECK
    # --------------------------------------------------------

    review = state.get(
        "patch_review",
        {},
    )

    if review.get(
        "risk_level"
    ) == "critical":

        state["patch_error"] = (
            "Patch application blocked "
            "because security review "
            "classified it as critical."
        )

        state = add_audit_event(
            state,
            "patch_blocked_security",
            {
                "risk_level": "critical",
            },
        )

        print("PATCH BLOCKED:")

        print(
            "Security review classified "
            "the patch as critical."
        )

        return state

    # --------------------------------------------------------
    # APPLY PATCH
    # --------------------------------------------------------

    try:

        result = apply_patch(
            state["project_path"],
            state["patch"],
        )

        state.setdefault(
            "changes",
            [],
        ).append(
            result["file"]
        )

        state["patch_error"] = ""

        state = add_audit_event(
            state,
            "patch_applied",
            {
                "file": result["file"],
            },
        )

        print(
            "PATCH APPLIED SUCCESSFULLY"
        )

    except Exception as exc:

        state["patch_error"] = str(exc)

        state = add_audit_event(
            state,
            "patch_application_failed",
            {
                "error": str(exc),
            },
        )

        print(
            "PATCH APPLICATION FAILED:"
        )

        print(
            type(exc).__name__
        )

        print(
            str(exc)
        )

    return state


# ============================================================
# TEST RUNNER
# ============================================================

def test_runner_node(state):

    print("\n")
    print("=" * 60)
    print(
        "TEST RUNNER - ITERATION",
        state.get(
            "iteration",
            1,
        ),
    )
    print("=" * 60)

    try:

        project_path = state["project_path"]

        result = run_tests(
            project_path
        )

        print("\nRAW TEST RESULT:")
        print(result)

        if not isinstance(
            result,
            dict,
        ):

            raise ValueError(
                "Test runner did not return a dictionary."
            )

        # ----------------------------------------------------
        # Read test output safely
        # ----------------------------------------------------

        output = (
            result.get("output")
            or result.get("stdout")
            or result.get("test_output")
            or result.get("message")
            or ""
        )

        stderr = result.get(
            "stderr"
        ) or ""

        if stderr:

            output = (
                f"{output}\n\n"
                f"ERROR OUTPUT:\n{stderr}"
            ).strip()

        # ----------------------------------------------------
        # Read test status safely
        # ----------------------------------------------------

        test_passed = result.get(
            "passed"
        )

        if test_passed is None:

            test_passed = result.get(
                "success"
            )

        if test_passed is None:

            test_passed = result.get(
                "test_passed"
            )

        if test_passed is None:

            return_code = result.get(
                "return_code"
            )

            if return_code is None:

                return_code = result.get(
                    "returncode"
                )

            if return_code is not None:

                test_passed = (
                    int(return_code) == 0
                )

        if test_passed is None:

            test_passed = False

        # ----------------------------------------------------
        # Read return code
        # ----------------------------------------------------

        return_code = result.get(
            "return_code"
        )

        if return_code is None:

            return_code = result.get(
                "returncode"
            )

        if return_code is None:

            return_code = (
                0
                if test_passed
                else 1
            )

        # ----------------------------------------------------
        # Save results
        # ----------------------------------------------------

        state["test_output"] = output

        state["test_passed"] = bool(
            test_passed
        )

        state["test_return_code"] = int(
            return_code
        )

        # ----------------------------------------------------
        # Audit log
        # ----------------------------------------------------

        state = add_audit_event(
            state,
            "tests_completed",
            {
                "passed": bool(
                    test_passed
                ),
                "return_code": int(
                    return_code
                ),
                "output": output[:5000],
            },
        )

        # ----------------------------------------------------
        # Console output
        # ----------------------------------------------------

        print(
            "\nTEST PASSED:",
            bool(test_passed),
        )

        print(
            "RETURN CODE:",
            int(return_code),
        )

        if output:

            print(
                "\nTEST OUTPUT:"
            )

            print(output)

        if test_passed:

            print(
                "\nTESTS PASSED"
            )

        else:

            print(
                "\nTESTS FAILED"
            )

    except Exception as exc:

        state["test_passed"] = False

        state["test_return_code"] = 1

        state["test_output"] = (
            f"Test runner error: "
            f"{type(exc).__name__}: {exc}"
        )

        state = add_audit_event(
            state,
            "test_runner_failed",
            {
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )

        print(
            "\nTEST RUNNER FAILED:"
        )

        print(
            type(exc).__name__
        )

        print(str(exc))

    return state


# ============================================================
# VALIDATION
# ============================================================

def validation_node(state):

    if state.get(
        "test_passed",
        False,
    ):

        state["validation_passed"] = True

        state["validation_error"] = ""

        state["status"] = "fixed"

        state = add_audit_event(
            state,
            "validation_passed",
        )

        print(
            "VALIDATION: PASSED"
        )

    else:

        state["validation_passed"] = False

        state["validation_error"] = (
            "Tests failed."
        )

        state = add_audit_event(
            state,
            "validation_failed",
        )

        print(
            "VALIDATION: FAILED"
        )

    return state


# ============================================================
# ITERATION
# ============================================================

def increment_iteration_node(state):

    state["iteration"] = (
        state.get(
            "iteration",
            1,
        ) + 1
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Human approval applies to the repair session, not only
    # the first iteration.
    #
    # Therefore preserve approval during retries.
    # --------------------------------------------------------

    state["approved"] = True

    state["human_approved"] = True

    state["approval_required"] = False

    state = add_audit_event(
        state,
        "retry_iteration_started",
        {
            "iteration": state["iteration"],
            "approved": True,
            "human_approved": True,
        },
    )

    print("\n")
    print("=" * 60)
    print(
        "STARTING RETRY ITERATION",
        state["iteration"],
    )
    print("=" * 60)

    print(
        "HUMAN APPROVAL PRESERVED:"
    )

    print("Approved: True")
    print("Human Approved: True")
    print("Approval Required: False")

    return state


# ============================================================
# ROLLBACK
# ============================================================

def rollback_node(state):

    print("\n")
    print("=" * 60)
    print("ROLLING BACK CHANGES")
    print("=" * 60)

    checkpoint = state.get(
        "checkpoint",
        "",
    )

    if checkpoint:

        try:

            rollback_to_checkpoint(
                state["project_path"],
                checkpoint,
            )

            state["status"] = "failed"

            state = add_audit_event(
                state,
                "rollback_completed",
                {
                    "checkpoint": checkpoint,
                },
            )

            print(
                "ROLLBACK SUCCESSFUL"
            )

        except Exception as exc:

            state["status"] = "failed"

            state = add_audit_event(
                state,
                "rollback_failed",
                {
                    "error": str(exc),
                },
            )

            print(
                "ROLLBACK FAILED:"
            )

            print(
                type(exc).__name__
            )

            print(str(exc))

    else:

        state["status"] = "failed"

        state = add_audit_event(
            state,
            "rollback_skipped",
            {
                "reason": (
                    "No checkpoint available."
                ),
            },
        )

        print(
            "NO CHECKPOINT AVAILABLE"
        )

    return state
