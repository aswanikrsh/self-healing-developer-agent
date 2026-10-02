from django.contrib import admin

from .models import (
    Project,
    DebugSession,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "project_path",
        "created_at",
    )


@admin.register(DebugSession)
class DebugSessionAdmin(admin.ModelAdmin):

    list_display = (
        "project",
        "status",
        "iterations",
        "created_at",
    )

    list_filter = (
        "status",
    )