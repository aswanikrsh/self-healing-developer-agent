from pathlib import Path

from agent.analyzers.ast_analyzer import (
    analyze_python_source,
)

from agent.analyzers.project_analyzer import (
    analyze_project,
    read_project_files,
)


# ============================================================
# AST TEST
# ============================================================

def test_ast_analysis():

    source = """
import math


class Calculator:

    def add(self, a, b):
        return a + b


def multiply(a, b):
    return a * b
"""

    result = analyze_python_source(
        source
    )

    assert result["valid"] is True

    assert "math" in result[
        "imports"
    ]

    function_names = {
        item["name"]
        for item in result[
            "functions"
        ]
    }

    assert "multiply" in function_names

    class_names = {
        item["name"]
        for item in result[
            "classes"
        ]
    }

    assert "Calculator" in class_names


# ============================================================
# PROJECT ANALYSIS TEST
# ============================================================

def test_project_analysis():

    project_path = (
        Path(__file__).resolve().parent.parent
        / "workspace"
        / "test_project"
    )

    result = analyze_project(
        str(project_path),
        """
        File "calculator.py", line 2
        test_add_numbers
        """,
    )

    assert "structure" in result

    assert "files" in result

    assert "metadata" in result

    assert "dependency_map" in result

    assert "summary" in result

    assert (
        "calculator.py"
        in result["files"]
    )


# ============================================================
# PROJECT FILE READING TEST
# ============================================================

def test_read_project_files():

    project_path = (
        Path(__file__).resolve().parent.parent
        / "workspace"
        / "test_project"
    )

    files = read_project_files(
        str(project_path),
        [
            "calculator.py",
        ],
    )

    assert "calculator.py" in files

    assert (
        "def add_numbers"
        in files["calculator.py"]
    )


# ============================================================
# GENERATED DIRECTORY FILTER TEST
# ============================================================

def test_generated_directories_are_ignored(
    tmp_path,
):

    project = (
        tmp_path
        / "sample_project"
    )

    project.mkdir()

    (project / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    cache = (
        project
        / "__pycache__"
    )

    cache.mkdir()

    (
        cache / "bad.py"
    ).write_text(
        "this should not be included",
        encoding="utf-8",
    )

    pytest_cache = (
        project
        / ".pytest_cache"
    )

    pytest_cache.mkdir()

    (
        pytest_cache / "cache.py"
    ).write_text(
        "this should not be included",
        encoding="utf-8",
    )

    result = analyze_project(
        str(project)
    )

    assert "main.py" in result[
        "files"
    ]

    assert (
        "__pycache__/bad.py"
        not in result["files"]
    )

    assert (
        ".pytest_cache/cache.py"
        not in result["files"]
    )