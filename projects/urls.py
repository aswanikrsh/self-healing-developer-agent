from django.urls import path

from . import views


urlpatterns = [

    path(
        "new/",
        views.project_create,
        name="project_create"
    ),

    path(
        "<int:project_id>/debug/",
        views.debug_project,
        name="debug_project"
    ),

    path(
        "session/<int:session_id>/approval/",
        views.approval,
        name="approval"
    ),

    path(
        "session/<int:session_id>/report/",
        views.report,
        name="report"
    ),
]