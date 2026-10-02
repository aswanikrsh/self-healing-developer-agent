from pathlib import Path
import re


# ============================================================
# PROTECTED PATHS
# ============================================================

PROTECTED_PATHS = {
    ".git",
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}


# ============================================================
# PROTECTED FILE NAMES
# ============================================================

PROTECTED_FILES = {
    "settings.py",
    "manage.py",
    "requirements.txt",
}


# ============================================================
# DANGEROUS PYTHON PATTERNS
# ============================================================

DANGEROUS_PATTERNS = [
    (
        r"\beval\s*\(",
        "Use of eval() detected."
    ),
    (
        r"\bexec\s*\(",
        "Use of exec() detected."
    ),
    (
        r"\bos\.system\s*\(",
        "Use of os.system() detected."
    ),
    (
        r"\bsubprocess\.(run|call|Popen|check_output)\s*\(",
        "Subprocess execution detected."
    ),
    (
        r"\bcommands\.getoutput\s*\(",
        "Shell command execution detected."
    ),
    (
        r"\b__import__\s*\(",
        "Dynamic import detected."
    ),
    (
        r"\bimportlib\.import_module\s*\(",
        "Dynamic module import detected."
    ),
]


# ============================================================
# SECRET PATTERNS
# ============================================================

SECRET_PATTERNS = [
    (
        r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)"
        r"\s*=\s*['\"][^'\"]{8,}['\"]",
        "Possible hard-coded API key or secret detected."
    ),
    (
        r"(?i)password\s*=\s*['\"][^'\"]+['\"]",
        "Possible hard-coded password detected."
    ),
    (
        r"(?i)token\s*=\s*['\"][^'\"]{8,}['\"]",
        "Possible hard-coded token detected."
    ),
]


# ============================================================
# PATH VALIDATION
# ============================================================

def validate_relative_path(file_name):
    """
    Ensure a patch only refers to a relative,
    project-internal path.
    """

    if not isinstance(file_name, str):
        return False, "Patch file path must be a string."

    file_name = file_name.strip()

    if not file_name:
        return False, "Patch file path cannot be empty."

    path = Path(file_name)

    if path.is_absolute():
        return False, "Absolute paths are not allowed."

    if ".." in path.parts:
        return False, "Path traversal '..' is not allowed."

    for part in path.parts:
        if part in PROTECTED_PATHS:
            return False, f"Protected directory cannot be modified: {part}"

    return True, "Path is safe."


# ============================================================
# PROJECT BOUNDARY
# ============================================================

def validate_project_boundary(project_path, file_name):
    """
    Ensure target file stays inside project root.
    """

    root = Path(project_path).resolve()

    try:
        target = (root / file_name).resolve()
        target.relative_to(root)
    except ValueError:
        return False, "Target file is outside the project directory."

    return True, "Target is inside project."


# ============================================================
# PROTECTED FILE CHECK
# ============================================================

def check_protected_file(file_name):
    """
    Certain project files should not be automatically modified.
    """

    path = Path(file_name)

    if path.name in PROTECTED_FILES:
        return False, (
            f"{path.name} is a protected project file. "
            "Manual review is required."
        )

    return True, "File is not protected."


# ============================================================
# DANGEROUS CODE CHECK
# ============================================================

def scan_dangerous_code(code):
    """
    Detect potentially dangerous Python operations.
    """

    findings = []

    if not isinstance(code, str):
        return findings

    for pattern, message in DANGEROUS_PATTERNS:

        if re.search(pattern, code):
            findings.append({
                "type": "dangerous_code",
                "message": message,
            })

    return findings


# ============================================================
# SECRET CHECK
# ============================================================

def scan_secrets(code):
    """
    Detect possible hard-coded credentials/secrets.
    """

    findings = []

    if not isinstance(code, str):
        return findings

    for pattern, message in SECRET_PATTERNS:

        if re.search(pattern, code):
            findings.append({
                "type": "secret",
                "message": message,
            })

    return findings


# ============================================================
# PATCH SIZE CHECK
# ============================================================

def check_patch_size(old_code, new_code):
    """
    Prevent unexpectedly large automatic modifications.
    """

    old_lines = len(old_code.splitlines())
    new_lines = len(new_code.splitlines())

    total_changed = old_lines + new_lines

    if total_changed > 200:
        return False, (
            f"Patch is too large: approximately "
            f"{total_changed} lines involved."
        )

    return True, "Patch size is acceptable."


# ============================================================
# FULL SECURITY SCAN
# ============================================================

def security_scan(project_path, patch):
    """
    Perform all Phase 4 security checks.
    """

    findings = []
    warnings = []

    file_name = patch.get("file", "")
    old_code = patch.get("old_code", "")
    new_code = patch.get("new_code", "")

    # --------------------------------------------------------
    # PATH
    # --------------------------------------------------------

    valid, message = validate_relative_path(file_name)

    if not valid:
        findings.append({
            "severity": "critical",
            "message": message,
        })

        return {
            "safe": False,
            "risk_level": "critical",
            "findings": findings,
            "warnings": warnings,
        }

    # --------------------------------------------------------
    # PROJECT BOUNDARY
    # --------------------------------------------------------

    valid, message = validate_project_boundary(
        project_path,
        file_name,
    )

    if not valid:

        findings.append({
            "severity": "critical",
            "message": message,
        })

        return {
            "safe": False,
            "risk_level": "critical",
            "findings": findings,
            "warnings": warnings,
        }

    # --------------------------------------------------------
    # PROTECTED FILE
    # --------------------------------------------------------

    valid, message = check_protected_file(file_name)

    if not valid:

        warnings.append({
            "severity": "high",
            "message": message,
        })

    # --------------------------------------------------------
    # DANGEROUS CODE
    # --------------------------------------------------------

    dangerous = scan_dangerous_code(new_code)

    for finding in dangerous:

        findings.append({
            "severity": "critical",
            "message": finding["message"],
        })

    # --------------------------------------------------------
    # SECRETS
    # --------------------------------------------------------

    secrets = scan_secrets(new_code)

    for finding in secrets:

        findings.append({
            "severity": "critical",
            "message": finding["message"],
        })

    # --------------------------------------------------------
    # PATCH SIZE
    # --------------------------------------------------------

    valid, message = check_patch_size(
        old_code,
        new_code,
    )

    if not valid:

        findings.append({
            "severity": "high",
            "message": message,
        })

    # --------------------------------------------------------
    # DETERMINE RISK
    # --------------------------------------------------------

    if any(
        item["severity"] == "critical"
        for item in findings
    ):
        risk_level = "critical"
        safe = False

    elif any(
        item["severity"] == "high"
        for item in findings
    ) or warnings:

        risk_level = "high"
        safe = True

    else:

        risk_level = "low"
        safe = True

    return {
        "safe": safe,
        "risk_level": risk_level,
        "findings": findings,
        "warnings": warnings,
    }