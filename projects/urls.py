from django.urls import path

from . import views


urlpatterns = [

    # Phase 9 Dashboard
    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    # Create a new project
    path(
        "new/",
        views.project_create,
        name="project_create"
    ),

    # Start debugging a project
    path(
        "<int:project_id>/debug/",
        views.debug_project,
        name="debug_project"
    ),

    # Human approval page
    path(
        "session/<int:session_id>/approval/",
        views.approval,
        name="approval"
    ),

    # Final repair report
    path(
        "session/<int:session_id>/report/",
        views.report,
        name="report"
    ),

    # Phase 9 live session status API
    path(
        "api/session/<int:session_id>/status/",
        views.session_status_api,
        name="session_status_api"
    ),
]