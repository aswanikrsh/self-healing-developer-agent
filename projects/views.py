import json
import ast
import traceback

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.utils import timezone

from .models import (
    Project,
    DebugSession,
)

from .forms import (
    ProjectForm,
    DebugForm,
)

from agent.service import (
    analyze_project,
    repair_project,
)

from agent.security.patch_reviewer import (
    review_patch,
    format_patch_review,
)


# ============================================================
# PROJECT CREATE
# ============================================================

def project_create(request):

    if request.method == "POST":

        form = ProjectForm(
            request.POST
        )

        if form.is_valid():

            project = Project.objects.create(
                name=form.cleaned_data["name"],
                project_path=form.cleaned_data[
                    "project_path"
                ],
            )

            return redirect(
                "debug_project",
                project_id=project.id,
            )

    else:

        form = ProjectForm()

    return render(
        request,
        "project_upload.html",
        {
            "form": form,
        },
    )


# ============================================================
# DEBUG PROJECT
# ============================================================

def debug_project(
    request,
    project_id,
):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    if request.method == "POST":

        form = DebugForm(
            request.POST
        )

        if form.is_valid():

            session = DebugSession.objects.create(
                project=project,
                error_message=form.cleaned_data[
                    "error_message"
                ],
                status="running",
                approval_required=True,
            )

            try:

                # =================================================
                # PHASE 3 PROJECT INTELLIGENCE
                # =================================================

                result = analyze_project(
                    project.project_path,
                    session.error_message,
                )

                # -------------------------------------------------
                # Root cause
                # -------------------------------------------------

                session.root_cause = (
                    result.get(
                        "root_cause",
                        "",
                    )
                )

                # -------------------------------------------------
                # Proposed fix
                # -------------------------------------------------

                session.proposed_fix = (
                    result.get(
                        "proposed_fix",
                        "",
                    )
                )

                # -------------------------------------------------
                # Generated patch
                # -------------------------------------------------

                patch = result.get(
                    "patch",
                    {},
                )

                # -------------------------------------------------
                # IMPORTANT:
                # Never continue with an empty patch.
                # -------------------------------------------------

                if not patch:

                    raise ValueError(
                        "The AI analysis completed, but no valid "
                        "code patch was generated."
                    )

                if not isinstance(
                    patch,
                    dict,
                ):

                    raise ValueError(
                        "The generated patch is not a valid "
                        "patch dictionary."
                    )

                required_patch_fields = [
                    "file",
                    "old_code",
                    "new_code",
                    "reason",
                ]

                missing_fields = [
                    field
                    for field in required_patch_fields
                    if field not in patch
                ]

                if missing_fields:

                    raise ValueError(
                        "Generated patch is missing required "
                        f"fields: {missing_fields}"
                    )

                # -------------------------------------------------
                # Store patch
                # -------------------------------------------------

                session.patch = json.dumps(
                    patch,
                    indent=2,
                )

                session.iterations = (
                    result.get(
                        "iteration",
                        1,
                    )
                )

                # =================================================
                # PHASE 4 SECURITY REVIEW
                # =================================================

                print("\n")
                print("=" * 60)
                print("PHASE 4 PATCH SECURITY REVIEW")
                print("=" * 60)

                review = review_patch(
                    project.project_path,
                    patch,
                )

                print(
                    format_patch_review(
                        review
                    )
                )

                # -------------------------------------------------
                # Save security information
                # -------------------------------------------------

                session.patch_risk_level = (
                    review.get(
                        "risk_level",
                        "unknown",
                    )
                )

                session.security_review = (
                    format_patch_review(
                        review
                    )
                )

                session.security_findings = (
                    json.dumps(
                        review.get(
                            "findings",
                            [],
                        ),
                        indent=2,
                    )
                )

                # =================================================
                # CRITICAL SECURITY PATCH
                # =================================================

                if (
                    review.get(
                        "risk_level"
                    )
                    == "critical"
                ):

                    session.status = "failed"

                    session.approval_required = True

                    session.test_output = (
                        "Patch blocked by Phase 4 "
                        "security review.\n\n"
                        + format_patch_review(
                            review
                        )
                    )

                    session.save()

                    return redirect(
                        "report",
                        session_id=session.id,
                    )

                # =================================================
                # WAIT FOR HUMAN APPROVAL
                # =================================================

                session.status = (
                    "awaiting_approval"
                )

                session.approval_required = True

                session.save()

                return redirect(
                    "approval",
                    session_id=session.id,
                )

            except Exception as exc:

                # -------------------------------------------------
                # Print full exception to terminal
                # -------------------------------------------------

                print("\n")
                print("=" * 60)
                print("ANALYZE PROJECT FAILED")
                print("=" * 60)
                print(
                    type(exc).__name__
                )
                print(
                    str(exc)
                )
                traceback.print_exc()
                print("=" * 60)

                session.status = "failed"

                session.test_output = (
                    f"{type(exc).__name__}: {exc}"
                )

                session.approval_required = False

                session.save()

                return redirect(
                    "report",
                    session_id=session.id,
                )

    else:

        form = DebugForm()

    return render(
        request,
        "debugging.html",
        {
            "project": project,
            "form": form,
        },
    )


# ============================================================
# PATCH PARSER
# ============================================================

def parse_patch(value):
    """
    Read patches stored by:
    - Phase 1
    - Phase 2
    - Phase 3
    - Phase 4
    - Phase 5
    """

    if not value:

        return {}

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    try:

        result = json.loads(
            value
        )

        if isinstance(
            result,
            dict,
        ):

            return result

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        pass

    # --------------------------------------------------------
    # Backward compatibility
    # --------------------------------------------------------

    try:

        result = ast.literal_eval(
            value
        )

        if isinstance(
            result,
            dict,
        ):

            return result

    except (
        ValueError,
        SyntaxError,
    ):

        pass

    return {}


# ============================================================
# APPROVAL
# ============================================================

def approval(
    request,
    session_id,
):

    session = get_object_or_404(
        DebugSession,
        id=session_id,
    )

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        action = request.POST.get(
            "action"
        )

        # ====================================================
        # REJECT
        # ====================================================

        if action == "reject":

            session.status = "failed"

            session.approval_required = False

            session.test_output = (
                "Fix rejected by user."
            )

            session.save()

            return redirect(
                "report",
                session_id=session.id,
            )

        # ====================================================
        # APPROVE
        # ====================================================

        if action == "approve":

            try:

                # =================================================
                # PARSE PATCH
                # =================================================

                patch = parse_patch(
                    session.patch
                )

                if not patch:

                    raise ValueError(
                        "No valid patch was found."
                    )

                # =================================================
                # BASIC PATCH VALIDATION
                # =================================================

                required_patch_fields = [
                    "file",
                    "old_code",
                    "new_code",
                    "reason",
                ]

                missing_fields = [
                    field
                    for field in required_patch_fields
                    if field not in patch
                ]

                if missing_fields:

                    raise ValueError(
                        "Patch is missing required fields: "
                        f"{missing_fields}"
                    )

                # =================================================
                # PHASE 4 SECURITY REVIEW
                # =================================================

                print("\n")
                print("=" * 60)
                print(
                    "PHASE 4 APPROVAL SECURITY RECHECK"
                )
                print("=" * 60)

                review = review_patch(
                    session.project.project_path,
                    patch,
                )

                print(
                    format_patch_review(
                        review
                    )
                )

                # -------------------------------------------------
                # Save latest review
                # -------------------------------------------------

                session.patch_risk_level = (
                    review.get(
                        "risk_level",
                        "unknown",
                    )
                )

                session.security_review = (
                    format_patch_review(
                        review
                    )
                )

                session.security_findings = (
                    json.dumps(
                        review.get(
                            "findings",
                            [],
                        ),
                        indent=2,
                    )
                )

                # =================================================
                # CRITICAL PATCH
                # =================================================

                if (
                    review.get(
                        "risk_level"
                    )
                    == "critical"
                ):

                    session.status = "failed"

                    session.approval_required = True

                    session.test_output = (
                        "Repair blocked by Phase 4 "
                        "security review.\n\n"
                        + format_patch_review(
                            review
                        )
                    )

                    session.save()

                    return redirect(
                        "report",
                        session_id=session.id,
                    )

                # =================================================
                # HUMAN APPROVAL
                # =================================================
                #
                # IMPORTANT:
                # The browser approval must be explicitly
                # transferred into the LangGraph repair state.
                #
                # We therefore set BOTH:
                #
                #     approved = True
                #
                # and:
                #
                #     human_approved = True
                #
                # This keeps compatibility with nodes that use
                # either approval key.
                #
                # =================================================

                session.status = "running"

                session.approval_required = False

                session.approved_at = (
                    timezone.now()
                )

                session.save()

                # =================================================
                # BUILD REPAIR STATE
                # =================================================

                state = {

                    # --------------------------------------------
                    # PROJECT
                    # --------------------------------------------

                    "project_path": (
                        session.project.project_path
                    ),

                    "error_message": (
                        session.error_message
                    ),

                    # --------------------------------------------
                    # PROJECT INTELLIGENCE
                    # --------------------------------------------

                    "project_structure": "",

                    "project_files": {},

                    "relevant_files": [],

                    "project_summary": "",

                    "project_index": {},

                    "dependency_map": {},

                    # --------------------------------------------
                    # ERROR ANALYSIS
                    # --------------------------------------------

                    "error_analysis": (
                        session.root_cause
                    ),

                    "root_cause": (
                        session.root_cause
                    ),

                    # --------------------------------------------
                    # FIX
                    # --------------------------------------------

                    "proposed_fix": (
                        session.proposed_fix
                    ),

                    "patch": patch,

                    "patch_error": "",

                    # --------------------------------------------
                    # CHANGES
                    # --------------------------------------------

                    "changes": [],

                    # --------------------------------------------
                    # SECURITY
                    # --------------------------------------------

                    "patch_review": review,

                    "patch_risk_level": (
                        review.get(
                            "risk_level",
                            "unknown",
                        )
                    ),

                    "security_findings": (
                        review.get(
                            "findings",
                            [],
                        )
                    ),

                    "security_warnings": (
                        review.get(
                            "warnings",
                            [],
                        )
                    ),

                    # --------------------------------------------
                    # TESTING
                    # --------------------------------------------

                    "test_output": "",

                    "test_passed": False,

                    "test_return_code": -1,

                    # --------------------------------------------
                    # PHASE 5
                    # --------------------------------------------

                    "generated_test": {},

                    "generated_test_code": "",

                    "generated_test_context": "",

                    "generated_test_result": {},

                    "generated_test_passed": False,

                    "generated_test_output": "",

                    # --------------------------------------------
                    # VALIDATION
                    # --------------------------------------------

                    "validation_passed": False,

                    "validation_error": "",

                    # --------------------------------------------
                    # APPROVAL
                    # --------------------------------------------

                    "approval_required": False,

                    # IMPORTANT:
                    # Both keys are intentionally provided.

                    "approved": True,

                    "human_approved": True,

                    # --------------------------------------------
                    # GIT
                    # --------------------------------------------

                    "checkpoint": "",

                    # --------------------------------------------
                    # AGENT CONTROL
                    # --------------------------------------------

                    "status": "approved",

                    "iteration": (
                        session.iterations or 1
                    ),

                    "max_iterations": 5,

                    # --------------------------------------------
                    # RETRY CONTEXT
                    # --------------------------------------------

                    "retry_history": [],

                    "previous_test_output": "",

                    "previous_patch": {},

                    # --------------------------------------------
                    # AUDIT
                    # --------------------------------------------

                    "audit_log": [],

                    # --------------------------------------------
                    # SESSION
                    # --------------------------------------------

                    "session_id": session.id,
                }

                # =================================================
                # EXPLICIT APPROVAL DEBUGGING
                # =================================================

                print("\n")
                print("=" * 60)
                print("HUMAN APPROVAL CONFIRMED")
                print("=" * 60)

                print(
                    "Session ID:",
                    session.id,
                )

                print(
                    "Approved:",
                    state["approved"],
                )

                print(
                    "Human Approved:",
                    state["human_approved"],
                )

                print(
                    "Approval Required:",
                    state["approval_required"],
                )

                print(
                    "Status:",
                    state["status"],
                )

                print("=" * 60)

                # =================================================
                # RUN SELF-HEALING LOOP
                # =================================================

                print("\n")
                print("=" * 60)
                print("STARTING SELF-HEALING REPAIR")
                print("=" * 60)

                result = repair_project(
                    state
                )

                # =================================================
                # SAVE RESULT
                # =================================================

                session.iterations = (
                    result.get(
                        "iteration",
                        session.iterations,
                    )
                )

                # -------------------------------------------------
                # FINAL PATCH
                # -------------------------------------------------

                final_patch = result.get(
                    "patch",
                    patch,
                )

                session.patch = json.dumps(
                    final_patch,
                    indent=2,
                )

                # -------------------------------------------------
                # TEST OUTPUT
                # -------------------------------------------------

                session.test_output = (
                    result.get(
                        "test_output",
                        "",
                    )
                )

                # -------------------------------------------------
                # PHASE 5 GENERATED TEST OUTPUT
                # -------------------------------------------------

                generated_test_output = (
                    result.get(
                        "generated_test_output",
                        "",
                    )
                )

                generated_test_result = (
                    result.get(
                        "generated_test_result",
                        {},
                    )
                )

                if generated_test_output:

                    session.test_output = (
                        session.test_output
                        + "\n\n"
                        + "==================================================\n"
                        + "PHASE 5 GENERATED TEST OUTPUT\n"
                        + "==================================================\n"
                        + generated_test_output
                    )

                elif generated_test_result:

                    session.test_output = (
                        session.test_output
                        + "\n\n"
                        + "==================================================\n"
                        + "PHASE 5 GENERATED TEST RESULT\n"
                        + "==================================================\n"
                        + json.dumps(
                            generated_test_result,
                            indent=2,
                        )
                    )

                # -------------------------------------------------
                # SECURITY RESULT
                # -------------------------------------------------

                final_review = result.get(
                    "patch_review",
                    review,
                )

                session.patch_risk_level = (
                    result.get(
                        "patch_risk_level",
                        final_review.get(
                            "risk_level",
                            session.patch_risk_level,
                        ),
                    )
                )

                session.security_findings = (
                    json.dumps(
                        result.get(
                            "security_findings",
                            final_review.get(
                                "findings",
                                [],
                            ),
                        ),
                        indent=2,
                    )
                )

                session.security_review = (
                    format_patch_review(
                        final_review
                    )
                )

                # =================================================
                # FINAL STATUS
                # =================================================

                if result.get(
                    "test_passed",
                    False,
                ):

                    session.status = "fixed"

                    session.test_output = (
                        session.test_output
                        + "\n\n"
                        + "FINAL RESULT: TESTS PASSED"
                    )

                else:

                    session.status = "failed"

                    session.test_output = (
                        session.test_output
                        + "\n\n"
                        + "FINAL RESULT: TESTS FAILED"
                    )

                session.approval_required = False

                session.save()

                return redirect(
                    "report",
                    session_id=session.id,
                )

            except Exception as exc:

                # -------------------------------------------------
                # Print complete repair exception
                # -------------------------------------------------

                print("\n")
                print("=" * 60)
                print("REPAIR PROJECT FAILED")
                print("=" * 60)
                print(
                    type(exc).__name__
                )
                print(
                    str(exc)
                )
                traceback.print_exc()
                print("=" * 60)

                session.status = "failed"

                session.test_output = (
                    f"Repair failed:\n\n"
                    f"{type(exc).__name__}: {exc}"
                )

                session.approval_required = False

                session.save()

                return redirect(
                    "report",
                    session_id=session.id,
                )

    # ========================================================
    # GET — APPROVAL PAGE
    # ========================================================

    return render(
        request,
        "approval.html",
        {
            "session": session,
        },
    )


# ============================================================
# REPORT
# ============================================================

def report(
    request,
    session_id,
):

    session = get_object_or_404(
        DebugSession,
        id=session_id,
    )

    return render(
        request,
        "report.html",
        {
            "session": session,
        },
    )