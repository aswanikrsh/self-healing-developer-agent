from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def home(request):
    return redirect("project_create")


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", home, name="home"),

    path("", include("projects.urls")),
]