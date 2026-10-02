from pathlib import Path

from agent.security.security_rules import (
    validate_relative_path,
    validate_project_boundary,
    scan_dangerous_code,
    scan_secrets,
    check_patch_size,
    security_scan,
)

from agent.security.patch_reviewer import (
    review_patch,
)


# ============================================================
# PATH TESTS
# ============================================================

def test_absolute_path_is_blocked():

    valid, message = validate_relative_path(
        "C:\\secret\\file.py"
    )

    assert valid is False


def test_path_traversal_is_blocked():

    valid, message = validate_relative_path(
        "../secret.py"
    )

    assert valid is False


def test_git_path_is_blocked():

    valid, message = validate_relative_path(
        ".git/config"
    )

    assert valid is False


def test_safe_path_is_allowed():

    valid, message = validate_relative_path(
        "calculator.py"
    )

    assert valid is True


# ============================================================
# PROJECT BOUNDARY
# ============================================================

def test_project_boundary(tmp_path):

    project = tmp_path / "project"

    project.mkdir()

    valid, message = validate_project_boundary(
        project,
        "calculator.py",
    )

    assert valid is True


# ============================================================
# DANGEROUS CODE
# ============================================================

def test_eval_is_detected():

    findings = scan_dangerous_code(
        "result = eval(user_input)"
    )

    assert len(findings) > 0


def test_exec_is_detected():

    findings = scan_dangerous_code(
        "exec(user_input)"
    )

    assert len(findings) > 0


def test_os_system_is_detected():

    findings = scan_dangerous_code(
        "os.system('rm -rf /')"
    )

    assert len(findings) > 0


# ============================================================
# SECRET DETECTION
# ============================================================

def test_api_key_detection():

    findings = scan_secrets(
        'api_key = "123456789abcdef"'
    )

    assert len(findings) > 0


def test_password_detection():

    findings = scan_secrets(
        'password = "mysecretpassword"'
    )

    assert len(findings) > 0


# ============================================================
# PATCH SIZE
# ============================================================

def test_small_patch_is_allowed():

    old_code = """
def add(a, b):
    return a - b
"""

    new_code = """
def add(a, b):
    return a + b
"""

    valid, message = check_patch_size(
        old_code,
        new_code,
    )

    assert valid is True


def test_large_patch_is_blocked():

    old_code = "\n".join(
        ["x = 1"] * 150
    )

    new_code = "\n".join(
        ["x = 2"] * 150
    )

    valid, message = check_patch_size(
        old_code,
        new_code,
    )

    assert valid is False


# ============================================================
# SECURITY SCAN
# ============================================================

def test_safe_patch():

    project = Path.cwd()

    patch = {
        "file": "calculator.py",
        "old_code": "return a - b",
        "new_code": "return a + b",
    }

    result = security_scan(
        project,
        patch,
    )

    assert result["risk_level"] in [
        "low",
        "high",
    ]


def test_dangerous_patch_is_blocked():

    project = Path.cwd()

    patch = {
        "file": "calculator.py",
        "old_code": "return a - b",
        "new_code": (
            "import os\n"
            "os.system('dangerous command')"
        ),
    }

    result = security_scan(
        project,
        patch,
    )

    assert result["safe"] is False

    assert result["risk_level"] == "critical"


# ============================================================
# PATCH REVIEW
# ============================================================

def test_patch_reviewer_blocks_dangerous_patch():

    project = Path.cwd()

    patch = {
        "file": "calculator.py",
        "old_code": "return a - b",
        "new_code": (
            "import os\n"
            "os.system('dangerous command')"
        ),
    }

    result = review_patch(
        project,
        patch,
    )

    assert result["risk_level"] == "critical"

    assert (
        result["approved_for_review"]
        is False
    )