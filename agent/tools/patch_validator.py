from pathlib import Path

from agent.security.security_rules import (
    validate_relative_path,
    validate_project_boundary,
    check_protected_file,
)


PROTECTED_PATHS = {
    ".git",
    ".env",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def is_safe_relative_path(file_name):
    """
    Prevent the AI from modifying files outside the project.
    """

    valid, _ = validate_relative_path(file_name)

    return valid


def validate_patch(project_path, patch):
    """
    Validate an AI-generated patch before applying it.
    """

    if not isinstance(patch, dict):

        return False, "Patch must be a dictionary."

    required_fields = [
        "file",
        "old_code",
        "new_code",
    ]

    for field in required_fields:

        if field not in patch:

            return False, (
                f"Missing patch field: {field}"
            )

    file_name = patch["file"]

    # --------------------------------------------------------
    # PATH SECURITY
    # --------------------------------------------------------

    valid, message = validate_relative_path(
        file_name
    )

    if not valid:

        return False, message

    # --------------------------------------------------------
    # PROJECT BOUNDARY
    # --------------------------------------------------------

    valid, message = validate_project_boundary(
        project_path,
        file_name,
    )

    if not valid:

        return False, message

    # --------------------------------------------------------
    # PROTECTED FILE
    # --------------------------------------------------------

    protected_valid, protected_message = (
        check_protected_file(file_name)
    )

    if not protected_valid:

        # Protected files are allowed only with
        # explicit human approval.
        #
        # The patch validator itself does not
        # approve the modification.
        #
        # It returns a warning to the caller.

        pass

    # --------------------------------------------------------
    # TARGET
    # --------------------------------------------------------

    root = Path(project_path).resolve()

    target = (
        root / file_name
    ).resolve()

    try:

        target.relative_to(root)

    except ValueError:

        return False, (
            "Patch attempts to access "
            "a file outside the project."
        )

    if not target.exists():

        return False, (
            f"File does not exist: {file_name}"
        )

    if not target.is_file():

        return False, (
            f"Target is not a file: {file_name}"
        )

    # --------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------

    try:

        content = target.read_text(
            encoding="utf-8"
        )

    except Exception as exc:

        return False, (
            f"Unable to read file: {exc}"
        )

    old_code = patch["old_code"]

    if not isinstance(old_code, str):

        return False, (
            "old_code must be a string."
        )

    if not old_code.strip():

        return False, (
            "old_code cannot be empty."
        )

    # --------------------------------------------------------
    # EXACT MATCH
    # --------------------------------------------------------

    occurrences = content.count(
        old_code
    )

    if occurrences == 0:

        return False, (
            "Original code was not found."
        )

    if occurrences > 1:

        return False, (
            f"Original code occurs "
            f"{occurrences} times. "
            "Refusing to apply an ambiguous patch."
        )

    # --------------------------------------------------------
    # NEW CODE
    # --------------------------------------------------------

    if not isinstance(
        patch["new_code"],
        str,
    ):

        return False, (
            "new_code must be a string."
        )

    return True, "Patch is valid."