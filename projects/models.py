from django.db import models


class Project(models.Model):

    name = models.CharField(
        max_length=200
    )

    project_path = models.CharField(
        max_length=500
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class DebugSession(models.Model):

    STATUS_CHOICES = [
        (
            "pending",
            "Pending",
        ),
        (
            "running",
            "Running",
        ),
        (
            "awaiting_approval",
            "Awaiting Approval",
        ),
        (
            "fixed",
            "Fixed",
        ),
        (
            "failed",
            "Failed",
        ),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="debug_sessions",
    )

    error_message = models.TextField()

    root_cause = models.TextField(
        blank=True,
    )

    proposed_fix = models.TextField(
        blank=True,
    )

    patch = models.TextField(
        blank=True,
    )

    # ========================================================
    # PHASE 4 - SECURITY
    # ========================================================

    patch_risk_level = models.CharField(
        max_length=30,
        blank=True,
    )

    security_review = models.TextField(
        blank=True,
    )

    security_findings = models.TextField(
        blank=True,
    )

    approval_required = models.BooleanField(
        default=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # ========================================================
    # TESTING
    # ========================================================

    test_output = models.TextField(
        blank=True,
    )

    # ========================================================
    # PHASE 5 - AUTOMATED TEST GENERATION
    # ========================================================

    generated_test_code = models.TextField(
        default="",
        blank=True,
    )

    generated_test_filename = models.CharField(
        max_length=255,
        default="",
        blank=True,
    )

    generated_test_reason = models.TextField(
        default="",
        blank=True,
    )

    generated_test_output = models.TextField(
        default="",
        blank=True,
    )

    generated_test_passed = models.BooleanField(
        default=False,
    )

    generated_test_status = models.CharField(
        max_length=30,
        default="",
        blank=True,
    )

    generated_test_context = models.TextField(
        default="",
        blank=True,
    )

    test_generation_error = models.TextField(
        default="",
        blank=True,
    )

    test_generation_status = models.CharField(
        max_length=30,
        default="",
        blank=True,
    )

    # ========================================================
    # STATUS
    # ========================================================

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
    )

    iterations = models.IntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):

        return (
            f"{self.project.name} - "
            f"{self.status}"
        )