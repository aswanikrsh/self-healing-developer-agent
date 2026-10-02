import re
from pathlib import Path
from typing import Any

from agent.analyzers.ast_analyzer import (
    analyze_python_file,
    format_python_metadata,
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FILE_SIZE = 200_000

MAX_RELEVANT_FILES = 20

ALLOWED_EXTENSIONS = {
    ".py",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".md",
}

IMPORTANT_FILENAMES = {
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "manage.py",
    "pytest.ini",
    "README.md",
}

SKIP_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize_path(value: str) -> str:
    return value.replace(
        "\\",
        "/",
    ).strip()


def _normalize_text(value: str) -> str:
    value = value.lower()

    value = value.replace(
        "\\",
        "/",
    )

    return value


# ============================================================
# DISCOVER FILES
# ============================================================

def discover_project_files(
    project_path: str,
) -> list[Path]:
    """
    Discover useful project files while ignoring
    generated/cache/environment directories.
    """

    root = Path(
        project_path
    ).resolve()

    if not root.exists():

        raise FileNotFoundError(
            f"Project path does not exist: {root}"
        )

    if not root.is_dir():

        raise ValueError(
            f"Project path is not a directory: {root}"
        )

    files = []

    for path in root.rglob("*"):

        if not path.is_file():
            continue

        relative_parts = path.relative_to(
            root
        ).parts

        # ----------------------------------------------------
        # Skip protected/generated directories
        # ----------------------------------------------------

        if any(
            part in SKIP_DIRECTORIES
            for part in relative_parts
        ):
            continue

        # ----------------------------------------------------
        # Skip hidden files
        # ----------------------------------------------------

        if any(
            part.startswith(".")
            and part not in {".github"}
            for part in relative_parts
        ):
            continue

        # ----------------------------------------------------
        # Size protection
        # ----------------------------------------------------

        try:

            if path.stat().st_size > MAX_FILE_SIZE:
                continue

        except OSError:
            continue

        suffix = path.suffix.lower()

        filename = path.name

        if (
            suffix in ALLOWED_EXTENSIONS
            or filename in IMPORTANT_FILENAMES
        ):

            files.append(path)

    return sorted(
        files,
        key=lambda p: str(p).lower(),
    )


# ============================================================
# BUILD PROJECT STRUCTURE
# ============================================================

def build_project_structure(
    root: Path,
    files: list[Path],
) -> str:
    """
    Build a readable project tree.
    """

    lines = []

    lines.append(
        root.name + "/"
    )

    for file_path in files:

        relative = file_path.relative_to(
            root
        )

        depth = len(
            relative.parts
        ) - 1

        indent = "    " * depth

        lines.append(
            f"{indent}└── {relative.as_posix()}"
        )

    return "\n".join(lines)


# ============================================================
# ERROR TOKENS
# ============================================================

def _extract_error_tokens(
    error_message: str,
) -> list[str]:
    """
    Extract useful names from traceback/error text.

    Examples:
        calculator.py
        add_numbers
        views.py
        MyClass
    """

    if not error_message:
        return []

    tokens = set()

    # --------------------------------------------------------
    # File paths
    # --------------------------------------------------------

    traceback_matches = re.findall(
        r'File ["\']([^"\']+)["\']',
        error_message,
    )

    for value in traceback_matches:

        value = _normalize_path(
            value
        )

        tokens.add(
            Path(value).name.lower()
        )

        tokens.add(
            value.lower()
        )

    # --------------------------------------------------------
    # Python identifiers
    # --------------------------------------------------------

    identifiers = re.findall(
        r"\b[A-Za-z_][A-Za-z0-9_]*\b",
        error_message,
    )

    for identifier in identifiers:

        if len(identifier) >= 3:

            tokens.add(
                identifier.lower()
            )

    return sorted(tokens)


# ============================================================
# MODULE NAME
# ============================================================

def _python_module_name(
    relative_path: str,
) -> str:
    """
    Convert:

        app/views.py

    into:

        app.views
    """

    path = Path(
        relative_path
    )

    parts = list(
        path.parts
    )

    if parts and parts[-1] == "__init__.py":

        parts = parts[:-1]

    elif parts:

        parts[-1] = path.stem

    return ".".join(parts)


# ============================================================
# BUILD DEPENDENCY MAP
# ============================================================

def build_dependency_map(
    metadata: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    """
    Build a lightweight internal dependency graph
    from Python imports.
    """

    module_to_file = {}

    for filename in metadata:

        module_name = _python_module_name(
            filename
        )

        if module_name:

            module_to_file[
                module_name
            ] = filename

    dependency_map = {}

    for filename, info in metadata.items():

        dependencies = []

        imports = info.get(
            "imports",
            [],
        )

        for imported in imports:

            # Exact module
            if imported in module_to_file:

                dependencies.append(
                    module_to_file[imported]
                )

                continue

            # Parent module
            current = imported

            while "." in current:

                current = current.rsplit(
                    ".",
                    1,
                )[0]

                if current in module_to_file:

                    dependencies.append(
                        module_to_file[current]
                    )

                    break

        dependency_map[filename] = sorted(
            set(dependencies)
        )

    return dependency_map


# ============================================================
# RELEVANT FILE SCORING
# ============================================================

def _score_file(
    filename: str,
    metadata: dict[str, Any],
    error_tokens: list[str],
) -> int:
    """
    Score a file according to its relationship
    to the current error.
    """

    normalized_filename = _normalize_text(
        filename
    )

    path_object = Path(
        filename
    )

    basename = path_object.name.lower()

    stem = path_object.stem.lower()

    score = 0

    # --------------------------------------------------------
    # Direct filename match
    # --------------------------------------------------------

    for token in error_tokens:

        if token == basename:

            score += 100

        if token == normalized_filename:

            score += 100

        if token == stem:

            score += 50

    # --------------------------------------------------------
    # Function names
    # --------------------------------------------------------

    functions = metadata.get(
        "functions",
        [],
    )

    for function in functions:

        name = function["name"].lower()

        if name in error_tokens:

            score += 80

    # --------------------------------------------------------
    # Class names
    # --------------------------------------------------------

    classes = metadata.get(
        "classes",
        [],
    )

    for class_info in classes:

        name = class_info["name"].lower()

        if name in error_tokens:

            score += 80

    # --------------------------------------------------------
    # Python files get priority
    # --------------------------------------------------------

    if path_object.suffix.lower() == ".py":

        score += 20

    # --------------------------------------------------------
    # Tests get moderate priority
    # --------------------------------------------------------

    if (
        "test" in basename
        or basename.startswith("test_")
    ):

        score += 10

    # --------------------------------------------------------
    # Important configuration
    # --------------------------------------------------------

    if basename in {
        "manage.py",
        "settings.py",
        "urls.py",
        "requirements.txt",
        "pyproject.toml",
    }:

        score += 5

    return score


# ============================================================
# SELECT RELEVANT FILES
# ============================================================

def select_relevant_files(
    files: list[Path],
    root: Path,
    metadata: dict[str, dict[str, Any]],
    error_message: str = "",
) -> list[str]:
    """
    Select the most useful files for the LLM.

    This prevents unnecessary files from being sent
    to the model.
    """

    error_tokens = _extract_error_tokens(
        error_message
    )

    scored_files = []

    for file_path in files:

        relative = file_path.relative_to(
            root
        ).as_posix()

        score = _score_file(
            relative,
            metadata.get(
                relative,
                {},
            ),
            error_tokens,
        )

        scored_files.append(
            (
                score,
                relative,
            )
        )

    # Highest score first.
    scored_files.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    selected = []

    for score, filename in scored_files:

        if len(selected) >= MAX_RELEVANT_FILES:
            break

        selected.append(
            filename
        )

    # --------------------------------------------------------
    # Always keep at least one file when possible.
    # --------------------------------------------------------

    if not selected and files:

        selected.append(
            files[0]
            .relative_to(root)
            .as_posix()
        )

    return selected


# ============================================================
# READ PROJECT FILES
# ============================================================

def read_project_files(
    project_path: str,
    filenames: list[str],
) -> dict[str, str]:
    """
    Read only the selected relevant files.

    File names remain relative to the project root.
    """

    root = Path(
        project_path
    ).resolve()

    result = {}

    for filename in filenames:

        if not filename:
            continue

        relative = Path(
            filename
        )

        # Prevent path traversal.
        if relative.is_absolute():
            continue

        if ".." in relative.parts:
            continue

        target = (
            root / relative
        ).resolve()

        try:

            target.relative_to(
                root
            )

        except ValueError:

            continue

        if not target.exists():
            continue

        if not target.is_file():
            continue

        try:

            if target.stat().st_size > MAX_FILE_SIZE:
                continue

            content = target.read_text(
                encoding="utf-8"
            )

        except (
            UnicodeDecodeError,
            OSError,
        ):

            continue

        result[
            relative.as_posix()
        ] = content

    return result


# ============================================================
# BUILD PROJECT SUMMARY
# ============================================================

def build_project_summary(
    files: list[Path],
    root: Path,
    metadata: dict[str, dict[str, Any]],
    dependency_map: dict[str, list[str]],
    relevant_files: list[str],
) -> str:
    """
    Build a compact project intelligence summary.
    """

    python_count = 0
    function_count = 0
    class_count = 0

    for filename, info in metadata.items():

        if filename.endswith(".py"):

            python_count += 1

        function_count += len(
            info.get(
                "functions",
                [],
            )
        )

        class_count += len(
            info.get(
                "classes",
                [],
            )
        )

    lines = []

    lines.append(
        "PROJECT INTELLIGENCE"
    )

    lines.append(
        "===================="
    )

    lines.append(
        f"Project root: {root}"
    )

    lines.append(
        f"Total useful files: {len(files)}"
    )

    lines.append(
        f"Python files: {python_count}"
    )

    lines.append(
        f"Functions discovered: {function_count}"
    )

    lines.append(
        f"Classes discovered: {class_count}"
    )

    lines.append(
        ""
    )

    lines.append(
        "RELEVANT FILES:"
    )

    for filename in relevant_files:

        lines.append(
            f"  - {filename}"
        )

    lines.append(
        ""
    )

    lines.append(
        "PYTHON STRUCTURE:"
    )

    for filename, info in metadata.items():

        if not filename.endswith(".py"):
            continue

        lines.append(
            f"\nFILE: {filename}"
        )

        formatted = format_python_metadata(
            info
        )

        for line in formatted.splitlines():

            lines.append(
                f"  {line}"
            )

    lines.append(
        ""
    )

    lines.append(
        "INTERNAL DEPENDENCIES:"
    )

    dependency_found = False

    for filename, dependencies in dependency_map.items():

        if not dependencies:
            continue

        dependency_found = True

        lines.append(
            f"  {filename}"
        )

        for dependency in dependencies:

            lines.append(
                f"    -> {dependency}"
            )

    if not dependency_found:

        lines.append(
            "  No internal Python dependencies detected."
        )

    return "\n".join(
        lines
    )


# ============================================================
# MAIN PROJECT ANALYSIS
# ============================================================

def analyze_project(
    project_path: str,
    error_message: str = "",
) -> dict[str, Any]:
    """
    Complete Phase 3 project analysis.

    Returns:

        structure
        files
        metadata
        dependency_map
        summary
    """

    root = Path(
        project_path
    ).resolve()

    files = discover_project_files(
        project_path
    )

    metadata = {}

    # --------------------------------------------------------
    # AST analyze Python files
    # --------------------------------------------------------

    for file_path in files:

        relative = file_path.relative_to(
            root
        ).as_posix()

        if file_path.suffix.lower() == ".py":

            metadata[
                relative
            ] = analyze_python_file(
                file_path
            )

    # --------------------------------------------------------
    # Dependency graph
    # --------------------------------------------------------

    dependency_map = build_dependency_map(
        metadata
    )

    # --------------------------------------------------------
    # Relevant file selection
    # --------------------------------------------------------

    relevant_files = select_relevant_files(
        files,
        root,
        metadata,
        error_message,
    )

    # --------------------------------------------------------
    # Project tree
    # --------------------------------------------------------

    structure = build_project_structure(
        root,
        files,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = build_project_summary(
        files,
        root,
        metadata,
        dependency_map,
        relevant_files,
    )

    return {
        "structure": structure,
        "files": relevant_files,
        "metadata": metadata,
        "dependency_map": dependency_map,
        "summary": summary,
    }