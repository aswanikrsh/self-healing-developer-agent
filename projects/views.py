import json
import ast
import traceback
import threading

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.http import JsonResponse

from django.utils import timezone

from django.conf import settings

from django.db.models import Count

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
# BACKGROUND REPAIR WORKER
# PHASE 9
# ============================================================

def run_repair_background(
    session_id,
    state,
    initial_patch,
    initial_review,
):
    """
    Run the self-healing repair engine in the background.

    The browser does NOT wait for repair_project() anymore.

    The approval page can immediately redirect to the report page
    while this function continues the repair process.

    Existing Phase 1-8 functionality remains inside repair_project().
    """

    print("\n")
    print("=" * 70)
    print("BACKGROUND SELF-HEALING REPAIR STARTED")
    print("=" * 70)
    print("Session ID:", session_id)
    print("=" * 70)

    try:

        # ========================================================
        # RUN SELF-HEALING LOOP
        # ========================================================

        print("\n")
        print("=" * 60)
        print("STARTING SELF-HEALING REPAIR")
        print("=" * 60)

        result = repair_project(
            state
        )

        # ========================================================
        # PROTECT AGAINST EMPTY RESULT
        # ========================================================

        if not result:

            raise ValueError(
                "The repair agent returned an empty result."
            )

        if not isinstance(
            result,
            dict,
        ):

            raise ValueError(
                "The repair agent returned an invalid "
                "result. Expected a dictionary."
            )

        print("\n")
        print("=" * 60)
        print("SELF-HEALING REPAIR COMPLETED")
        print("=" * 60)

        print(
            "Final test passed:",
            result.get(
                "test_passed",
                False,
            )
        )

        print(
            "Final iteration:",
            result.get(
                "iteration",
                0,
            )
        )

        print("=" * 60)

        # ========================================================
        # GET SESSION AGAIN
        # ========================================================

        session = get_object_or_404(
            DebugSession.objects.select_related(
                "project"
            ),
            id=session_id,
        )

        # ========================================================
        # SAVE ITERATION
        # ========================================================

        session.iterations = (
            result.get(
                "iteration",
                session.iterations,
            )
        )

        # ========================================================
        # FINAL PATCH
        # ========================================================

        final_patch = result.get(
            "patch",
            initial_patch,
        )

        if final_patch:

            if isinstance(
                final_patch,
                dict,
            ):

                session.patch = json.dumps(
                    final_patch,
                    indent=2,
                )

            else:

                session.patch = str(
                    final_patch
                )

        # ========================================================
        # TEST OUTPUT
        # ========================================================

        session.test_output = (
            result.get(
                "test_output",
                "",
            )
        )

        # ========================================================
        # PHASE 5 GENERATED TEST OUTPUT
        # ========================================================

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

        # ========================================================
        # SECURITY RESULT
        # ========================================================

        final_review = result.get(
            "patch_review",
            initial_review,
        )

        if not isinstance(
            final_review,
            dict,
        ):

            final_review = initial_review or {}

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

        # ========================================================
        # FINAL STATUS
        # ========================================================

        test_passed = bool(
            result.get(
                "test_passed",
                False,
            )
        )

        if test_passed:

            session.status = "fixed"

            session.test_output = (
                session.test_output
                + "\n\n"
                + "FINAL RESULT: TESTS PASSED"
            )

            print(
                "FINAL RESULT: TESTS PASSED"
            )

        else:

            session.status = "failed"

            session.test_output = (
                session.test_output
                + "\n\n"
                + "FINAL RESULT: TESTS FAILED"
            )

            print(
                "FINAL RESULT: TESTS FAILED"
            )

        # ========================================================
        # APPROVAL COMPLETED
        # ========================================================

        session.approval_required = False

        # ========================================================
        # SAVE EVERYTHING
        # ========================================================

        session.save()

        print("\n")
        print("=" * 60)
        print("BACKGROUND REPAIR SESSION FINALIZED")
        print("=" * 60)

        print(
            "Session ID:",
            session.id,
        )

        print(
            "Status:",
            session.status,
        )

        print(
            "Approval Required:",
            session.approval_required,
        )

        print("=" * 60)

    except Exception as exc:

        # ========================================================
        # COMPLETE BACKGROUND REPAIR EXCEPTION
        # ========================================================

        print("\n")
        print("=" * 70)
        print("BACKGROUND REPAIR PROJECT FAILED")
        print("=" * 70)

        print(
            type(exc).__name__
        )

        print(
            str(exc)
        )

        traceback.print_exc()

        print("=" * 70)

        try:

            session = get_object_or_404(
                DebugSession,
                id=session_id,
            )

            session.status = "failed"

            session.test_output = (
                "Repair failed:\n\n"
                f"{type(exc).__name__}: {exc}"
            )

            session.approval_required = False

            session.save()

            print(
                "Background failure saved to session."
            )

        except Exception as save_exc:

            print(
                "Could not save background failure:"
            )

            print(
                type(save_exc).__name__,
                str(save_exc),
            )


# ============================================================
# START BACKGROUND REPAIR
# ============================================================

def start_background_repair(
    session_id,
    state,
    patch,
    review,
):
    """
    Start the repair engine in a daemon background thread.

    The request does not wait for the repair to finish.
    """

    repair_thread = threading.Thread(
        target=run_repair_background,
        args=(
            session_id,
            state,
            patch,
            review,
        ),
        daemon=True,
    )

    repair_thread.start()

    print("\n")
    print("=" * 60)
    print("BACKGROUND REPAIR THREAD STARTED")
    print("=" * 60)
    print("Session ID:", session_id)
    print("Thread:", repair_thread.name)
    print("=" * 60)

    return repair_thread


# ============================================================
# DASHBOARD
# PHASE 9 - PROFESSIONAL DEVELOPER DASHBOARD
# ============================================================

def dashboard(request):
    """
    Phase 9 Professional Developer Dashboard.

    Provides:

    - Total projects
    - Total debugging sessions
    - Fixed sessions
    - Failed sessions
    - Running sessions
    - Pending sessions
    - Sessions waiting for approval
    - Success rate
    - Total repair iterations
    - Average repair iterations
    - Recent projects
    - Recent debugging sessions
    - Latest repair
    - Project debugging counts
    - Status distribution
    - System configuration
    - Recent activity

    Existing Phase 1-8 functionality is preserved.
    """

    # ========================================================
    # PROJECT QUERY
    # ========================================================

    projects = (
        Project.objects
        .all()
        .order_by("-created_at")
    )

    # ========================================================
    # SESSION QUERY
    # ========================================================

    sessions = (
        DebugSession.objects
        .select_related("project")
        .order_by("-updated_at")
    )

    # ========================================================
    # BASIC COUNTS
    # ========================================================

    total_projects = projects.count()

    total_sessions = sessions.count()

    fixed_sessions = sessions.filter(
        status="fixed"
    ).count()

    failed_sessions = sessions.filter(
        status="failed"
    ).count()

    running_sessions = sessions.filter(
        status="running"
    ).count()

    pending_sessions = sessions.filter(
        status="pending"
    ).count()

    approval_sessions = sessions.filter(
        status="awaiting_approval"
    ).count()

    # ========================================================
    # SUCCESS RATE
    # ========================================================

    completed_sessions = (
        fixed_sessions
        + failed_sessions
    )

    if completed_sessions > 0:

        success_rate = round(
            (
                fixed_sessions
                / completed_sessions
            )
            * 100,
            1,
        )

    else:

        success_rate = 0

    # ========================================================
    # TOTAL ITERATIONS
    # ========================================================

    total_iterations = 0

    for session in sessions:

        total_iterations += (
            session.iterations or 0
        )

    # ========================================================
    # AVERAGE ITERATIONS
    # ========================================================

    if total_sessions > 0:

        average_iterations = round(
            total_iterations
            / total_sessions,
            1,
        )

    else:

        average_iterations = 0

    # ========================================================
    # RECENT PROJECTS
    # ========================================================

    recent_projects = (
        projects[:8]
    )

    # ========================================================
    # PROJECT ROWS WITH DEBUG COUNT
    # ========================================================

    project_rows = (
        Project.objects
        .annotate(
            debug_count=Count(
                "debug_sessions"
            )
        )
        .order_by("-created_at")[:8]
    )

    # ========================================================
    # RECENT DEBUGGING SESSIONS
    # ========================================================

    recent_sessions = (
        sessions[:10]
    )

    # ========================================================
    # LATEST SESSION
    # ========================================================

    latest_session = (
        recent_sessions[0]
        if recent_sessions
        else None
    )

    # ========================================================
    # STATUS DISTRIBUTION
    # ========================================================

    status_distribution = {

        "pending": pending_sessions,

        "running": running_sessions,

        "awaiting_approval": (
            approval_sessions
        ),

        "fixed": fixed_sessions,

        "failed": failed_sessions,

    }

    # ========================================================
    # RECENT ACTIVITY
    # ========================================================

    recent_activity = []

    for session in recent_sessions:

        recent_activity.append(
            {
                "id": session.id,

                "project_name": (
                    session.project.name
                ),

                "status": session.status,

                "status_display": (
                    session.get_status_display()
                ),

                "iterations": (
                    session.iterations or 0
                ),

                "risk_level": (
                    session.patch_risk_level
                    or "unknown"
                ),

                "created_at": (
                    session.created_at
                ),

                "updated_at": (
                    session.updated_at
                ),
            }
        )

    # ========================================================
    # LATEST REPAIR INFORMATION
    # ========================================================

    latest_repair = None

    if latest_session:

        latest_repair = {

            "session_id": (
                latest_session.id
            ),

            "project_name": (
                latest_session.project.name
            ),

            "status": (
                latest_session.status
            ),

            "status_display": (
                latest_session.get_status_display()
            ),

            "root_cause": (
                latest_session.root_cause
                or "No root cause available."
            ),

            "proposed_fix": (
                latest_session.proposed_fix
                or "No proposed fix available."
            ),

            "risk_level": (
                latest_session.patch_risk_level
                or "unknown"
            ),

            "iterations": (
                latest_session.iterations or 0
            ),

            "test_output": (
                latest_session.test_output
                or ""
            ),

            "updated_at": (
                latest_session.updated_at
            ),
        }

    # ========================================================
    # SYSTEM CONFIGURATION
    # ========================================================

    ollama_model = getattr(
        settings,
        "OLLAMA_MODEL",
        "Not configured",
    )

    execution_mode = getattr(
        settings,
        "EXECUTION_MODE",
        "Local",
    )

    max_iterations = getattr(
        settings,
        "AGENT_MAX_ITERATIONS",
        5,
    )

    human_approval = getattr(
        settings,
        "AGENT_REQUIRE_HUMAN_APPROVAL",
        True,
    )

    memory_enabled = getattr(
        settings,
        "MEMORY_ENABLED",
        False,
    )

    docker_image = getattr(
        settings,
        "DOCKER_SANDBOX_IMAGE",
        "Not configured",
    )

    docker_network_disabled = getattr(
        settings,
        "DOCKER_SANDBOX_NETWORK_DISABLED",
        True,
    )

    # ========================================================
    # DASHBOARD CONTEXT
    # ========================================================

    context = {

        # ----------------------------------------------------
        # BACKWARD COMPATIBILITY
        # ----------------------------------------------------

        "projects": projects,

        "sessions": sessions,

        # ----------------------------------------------------
        # MAIN METRICS
        # ----------------------------------------------------

        "total_projects": total_projects,

        "total_sessions": total_sessions,

        "fixed_sessions": fixed_sessions,

        "failed_sessions": failed_sessions,

        "running_sessions": running_sessions,

        "pending_sessions": pending_sessions,

        "approval_sessions": approval_sessions,

        "success_rate": success_rate,

        "total_iterations": total_iterations,

        "average_iterations": average_iterations,

        # ----------------------------------------------------
        # DASHBOARD DATA
        # ----------------------------------------------------

        "status_distribution": (
            status_distribution
        ),

        "recent_projects": (
            recent_projects
        ),

        "project_rows": (
            project_rows
        ),

        "recent_sessions": (
            recent_sessions
        ),

        "recent_activity": (
            recent_activity
        ),

        "latest_session": (
            latest_session
        ),

        "latest_repair": (
            latest_repair
        ),

        # ----------------------------------------------------
        # SYSTEM CONFIGURATION
        # ----------------------------------------------------

        "ollama_model": (
            ollama_model
        ),

        "execution_mode": (
            execution_mode
        ),

        "max_iterations": (
            max_iterations
        ),

        "human_approval": (
            human_approval
        ),

        "memory_enabled": (
            memory_enabled
        ),

        "docker_image": (
            docker_image
        ),

        "docker_network_disabled": (
            docker_network_disabled
        ),

        # ----------------------------------------------------
        # DASHBOARD TIMESTAMP
        # ----------------------------------------------------

        "dashboard_generated_at": (
            timezone.now()
        ),
    }

    return render(
        request,
        "dashboard.html",
        context,
    )


# ============================================================
# DASHBOARD SESSION STATUS API
# PHASE 9
# ============================================================

def session_status_api(
    request,
    session_id,
):
    """
    Lightweight JSON endpoint for the Phase 9 dashboard.

    Can also be used by the report page to monitor
    background repair progress.
    """

    session = get_object_or_404(
        DebugSession.objects.select_related(
            "project"
        ),
        id=session_id,
    )

    max_iterations = getattr(
        settings,
        "AGENT_MAX_ITERATIONS",
        5,
    )

    return JsonResponse(
        {
            "success": True,

            "session_id": session.id,

            "project_id": (
                session.project.id
            ),

            "project_name": (
                session.project.name
            ),

            "status": (
                session.status
            ),

            "status_display": (
                session.get_status_display()
            ),

            "iterations": (
                session.iterations or 0
            ),

            "max_iterations": (
                max_iterations
            ),

            "approval_required": (
                session.approval_required
            ),

            "patch_risk_level": (
                session.patch_risk_level
                or "unknown"
            ),

            "test_output": (
                session.test_output
                or ""
            ),

            "created_at": (
                session.created_at.isoformat()
            ),

            "updated_at": (
                session.updated_at.isoformat()
            ),

            "approved_at": (
                session.approved_at.isoformat()
                if session.approved_at
                else None
            ),
        }
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
    """
    Human approval endpoint.

    IMPORTANT:
    This function accepts both:

        action=approve

    and:

        approval_button=approve

    This makes the approval workflow compatible with both
    the original approval.html and the updated approval.html.

    The repair engine itself continues to run through the
    existing background worker.
    """

    session = get_object_or_404(
        DebugSession.objects.select_related(
            "project"
        ),
        id=session_id,
    )

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return render(
            request,
            "approval.html",
            {
                "session": session,
            },
        )

    # ========================================================
    # ONLY POST SHOULD CONTINUE
    # ========================================================

    if request.method != "POST":

        return redirect(
            "approval",
            session_id=session.id,
        )

    # ========================================================
    # READ APPROVAL ACTION
    # ========================================================

    action = request.POST.get(
        "action"
    )

    approval_button = request.POST.get(
        "approval_button"
    )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not action:

        action = approval_button

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    if action:

        action = action.strip().lower()

    print("\n")
    print("=" * 60)
    print("PATCH APPROVAL REQUEST")
    print("=" * 60)
    print("Session ID:", session.id)
    print("POST DATA:", dict(request.POST))
    print("Action:", action)
    print("Approval Button:", approval_button)
    print("=" * 60)

    # ========================================================
    # INVALID ACTION
    # ========================================================

    if action not in (
        "approve",
        "reject",
    ):

        print(
            "INVALID APPROVAL ACTION"
        )

        session.test_output = (
            "Invalid approval action received.\n\n"
            f"Received action: {action!r}\n"
            f"POST fields: {dict(request.POST)}"
        )

        session.status = (
            "awaiting_approval"
        )

        session.approval_required = True

        session.save()

        return redirect(
            "approval",
            session_id=session.id,
        )

    # ========================================================
    # REJECT
    # ========================================================

    if action == "reject":

        session.status = "failed"

        session.approval_required = False

        session.test_output = (
            "Fix rejected by user."
        )

        session.save()

        print(
            "PATCH REJECTED BY USER"
        )

        print(
            "Redirecting to report..."
        )

        return redirect(
            "report",
            session_id=session.id,
        )

    # ========================================================
    # APPROVE
    # ========================================================

    if action == "approve":

        try:

            print("\n")
            print("=" * 60)
            print("HUMAN APPROVAL RECEIVED")
            print("=" * 60)
            print(
                "Session ID:",
                session.id,
            )
            print("=" * 60)

            # =================================================
            # VERIFY SESSION STATE
            # =================================================

            if session.status not in (
                "awaiting_approval",
                "pending",
                "running",
            ):

                raise ValueError(
                    "This debugging session is not "
                    "currently waiting for approval."
                )

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

                print(
                    "CRITICAL PATCH BLOCKED"
                )

                return redirect(
                    "report",
                    session_id=session.id,
                )

            # =================================================
            # HUMAN APPROVAL CONFIRMED
            # =================================================

            session.status = "running"

            session.approval_required = False

            session.approved_at = (
                timezone.now()
            )

            session.test_output = (
                "Human approval confirmed.\n\n"
                "Self-healing repair is running "
                "in the background..."
            )

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

                "max_iterations": getattr(
                    settings,
                    "AGENT_MAX_ITERATIONS",
                    5,
                ),

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
            # SAVE BEFORE STARTING BACKGROUND WORK
            # =================================================

            session.save()

            print("\n")
            print("=" * 60)
            print("APPROVAL SAVED")
            print("=" * 60)

            print(
                "Session ID:",
                session.id,
            )

            print(
                "Status:",
                session.status,
            )

            print(
                "Redirecting immediately to report..."
            )

            print("=" * 60)

            # =================================================
            # START BACKGROUND REPAIR
            # =================================================

            start_background_repair(
                session.id,
                state,
                patch,
                review,
            )

            # =================================================
            # IMMEDIATE REDIRECT
            # =================================================

            return redirect(
                "report",
                session_id=session.id,
            )

        except Exception as exc:

            # =================================================
            # APPROVAL / REPAIR START ERROR
            # =================================================

            print("\n")
            print("=" * 60)
            print("APPROVAL / REPAIR START FAILED")
            print("=" * 60)

            print(
                type(exc).__name__
            )

            print(
                str(exc)
            )

            traceback.print_exc()

            print("=" * 60)

            # =================================================
            # SAVE FAILURE
            # =================================================

            session.status = "failed"

            session.test_output = (
                f"Repair failed to start:\n\n"
                f"{type(exc).__name__}: {exc}"
            )

            session.approval_required = False

            session.save()

            print(
                "Repair failed to start."
            )

            print(
                "Redirecting to report..."
            )

            return redirect(
                "report",
                session_id=session.id,
            )

    # ========================================================
    # FALLBACK
    # ========================================================

    return redirect(
        "approval",
        session_id=session.id,
    )


# ============================================================
# REPORT
# ============================================================

def report(
    request,
    session_id,
):

    session = get_object_or_404(
        DebugSession.objects.select_related(
            "project"
        ),
        id=session_id,
    )

    return render(
        request,
        "report.html",
        {
            "session": session,
        },
    )