from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def home(request):
    return redirect("dashboard")


urlpatterns = [
    path("admin/", admin.site.urls),

    # Root URL
    path("", home, name="home"),

    # Projects application
    path("projects/", include("projects.urls")),
]