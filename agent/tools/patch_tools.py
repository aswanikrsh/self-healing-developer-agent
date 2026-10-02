from pathlib import Path

from agent.tools.patch_validator import (
    validate_patch,
)

from agent.analyzers.code_validator import (
    validate_python_code,
)


def create_patch(
    file_path,
    old_code,
    new_code,
    reason="",
):
    return {
        "file": str(file_path),
        "old_code": old_code,
        "new_code": new_code,
        "reason": reason,
    }


def apply_patch(project_path, patch):
    """
    Validate and safely apply a patch.
    """

    valid, message = validate_patch(
        project_path,
        patch,
    )

    if not valid:

        raise ValueError(message)

    root = Path(
        project_path
    ).resolve()

    file_path = (
        root / patch["file"]
    ).resolve()

    # --------------------------------------------------------
    # READ CURRENT SOURCE
    # --------------------------------------------------------

    content = file_path.read_text(
        encoding="utf-8"
    )

    old_code = patch["old_code"]
    new_code = patch["new_code"]

    # --------------------------------------------------------
    # ENSURE EXACT CURRENT MATCH
    # --------------------------------------------------------

    occurrences = content.count(
        old_code
    )

    if occurrences != 1:

        raise ValueError(
            "Patch source changed before "
            "application. Refusing to modify file."
        )

    # --------------------------------------------------------
    # CREATE NEW CONTENT
    # --------------------------------------------------------

    new_content = content.replace(
        old_code,
        new_code,
        1,
    )

    # --------------------------------------------------------
    # PYTHON SYNTAX VALIDATION
    # --------------------------------------------------------

    if file_path.suffix == ".py":

        validation = validate_python_code(
            new_content
        )

        if not validation["valid"]:

            raise ValueError(
                "Generated code failed syntax "
                "validation: "
                + validation["error"]
            )

    # --------------------------------------------------------
    # WRITE
    # --------------------------------------------------------

    file_path.write_text(
        new_content,
        encoding="utf-8",
    )

    return {
        "file": str(file_path),
        "status": "updated",
        "old_code": old_code,
        "new_code": new_code,
    }