import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from agent.llm import llm
from execution.runner import run_generated_test as run_generated_test_in_docker


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(text):
    """
    Extract JSON from an LLM response.

    Handles:
    - Direct JSON
    - Markdown JSON blocks
    - JSON surrounded by explanatory text
    - JSON containing braces inside strings
    """

    if not isinstance(
        text,
        str,
    ):
        text = str(text)

    text = text.strip()

    if not text:
        return None

    # --------------------------------------------------------
    # Direct JSON
    # --------------------------------------------------------

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Remove Markdown code fences
    # --------------------------------------------------------

    cleaned = re.sub(
        r"^\s*```(?:json|JSON)?\s*",
        "",
        text,
    )

    cleaned = re.sub(
        r"\s*```\s*$",
        "",
        cleaned,
    )

    cleaned = cleaned.strip()

    # --------------------------------------------------------
    # Try cleaned JSON
    # --------------------------------------------------------

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Markdown JSON block
    # --------------------------------------------------------

    markdown_matches = re.findall(
        r"```(?:json|JSON)?\s*(.*?)\s*```",
        text,
        re.DOTALL,
    )

    for candidate in markdown_matches:

        candidate = candidate.strip()

        try:
            return json.loads(candidate)

        except json.JSONDecodeError:
            continue

    # --------------------------------------------------------
    # Robust embedded JSON extraction
    # --------------------------------------------------------
    #
    # json.JSONDecoder().raw_decode() is safer than using
    # text.find("{") and text.rfind("}") because generated
    # Python code may itself contain braces.
    #
    # --------------------------------------------------------

    decoder = json.JSONDecoder()

    start_positions = [
        match.start()
        for match in re.finditer(
            r"\{",
            text,
        )
    ]

    for start in start_positions:

        candidate = text[start:]

        try:

            result, _ = decoder.raw_decode(
                candidate
            )

            return result

        except json.JSONDecodeError:

            continue

    # --------------------------------------------------------
    # Nothing could be parsed
    # --------------------------------------------------------

    return None


# ============================================================
# SOURCE FORMATTING
# ============================================================

def _format_project_files(project_files):
    """
    Convert project source into LLM-readable context.
    """

    files_text = ""

    if not isinstance(
        project_files,
        dict,
    ):
        return files_text

    for filename, content in project_files.items():

        files_text += f"""
============================================================
FILE: {filename}
============================================================

{content}

"""

    return files_text


# ============================================================
# TEST CODE VALIDATION
# ============================================================

def validate_generated_test(test_code):
    """
    Validate generated Python test syntax.

    This does NOT execute the test.
    """

    if not isinstance(
        test_code,
        str,
    ):
        return (
            False,
            "Generated test must be a string.",
        )

    if not test_code.strip():
        return (
            False,
            "Generated test is empty.",
        )

    if len(
        test_code.splitlines()
    ) > 300:
        return (
            False,
            "Generated test is too large.",
        )

    # --------------------------------------------------------
    # Python syntax validation
    # --------------------------------------------------------

    try:

        ast.parse(
            test_code
        )

    except SyntaxError as exc:

        return (
            False,
            "Generated test contains invalid Python syntax: "
            f"{exc}",
        )

    # --------------------------------------------------------
    # Basic safety checks
    # --------------------------------------------------------

    dangerous_patterns = [
        "os.system(",
        "subprocess.",
        "eval(",
        "exec(",
        "__import__(",
        "shutil.rmtree(",
    ]

    lowered = test_code.lower()

    for pattern in dangerous_patterns:

        if pattern.lower() in lowered:

            return (
                False,
                "Generated test contains a blocked "
                f"operation: {pattern}",
            )

    return (
        True,
        "Generated test passed syntax and safety validation.",
    )


# ============================================================
# TEST GENERATION
# ============================================================

def generate_tests(
    error,
    root_cause,
    project_files,
    project_structure="",
):
    """
    Generate a pytest test module for the current problem.

    The generated test is NOT written into the user's project.
    """

    # ========================================================
    # FORMAT PROJECT SOURCE
    # ========================================================

    files_text = _format_project_files(
        project_files
    )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are an expert Python test-generation agent.

Your task is to generate useful pytest tests for the
CURRENT project and CURRENT failure.

The tests will be executed against the project BEFORE
the repair is applied.

============================================================
CURRENT ERROR
============================================================

{error}

============================================================
ROOT CAUSE ANALYSIS
============================================================

{root_cause}

============================================================
PROJECT STRUCTURE
============================================================

{project_structure}

============================================================
CURRENT PROJECT SOURCE
============================================================

{files_text}

============================================================
TEST GENERATION GOAL
============================================================

Generate focused pytest tests that verify the expected
behavior of the code related to the current failure.

The tests should:

1. Test the affected functionality.
2. Verify the expected behavior.
3. Include useful normal cases.
4. Include reasonable edge cases where appropriate.
5. Be deterministic.
6. Use pytest.
7. Import only modules that exist in the supplied project.
8. Avoid external network calls.
9. Avoid modifying files.
10. Avoid modifying databases.
11. Avoid shell commands.
12. Avoid subprocess.
13. Avoid eval or exec.
14. Do not install dependencies.
15. Do not modify the project.
16. Do not use mocking unless it is clearly necessary.
17. Prefer simple direct assertions.
18. Do not invent APIs or functions that do not exist.
19. Do not test unrelated functionality.

============================================================
IMPORTANT
============================================================

The current project may contain broken code.

That is acceptable.

The generated test should describe the EXPECTED correct
behavior, not merely reproduce the current incorrect
implementation.

For example, if:

def add_numbers(a, b):
    return a - b

the generated test should verify:

add_numbers(10, 20) == 30

Do NOT change the source code.

============================================================
CRITICAL JSON RULES
============================================================

Your response MUST be valid JSON that can be parsed directly
using Python:

json.loads(response)

The entire response must contain exactly ONE JSON object.

IMPORTANT:

- Do NOT use Python triple quotes.
- Do NOT use triple-quoted strings.
- Do NOT use single-quoted Python strings.
- Do NOT use Markdown.
- Do NOT use ```json.
- Do NOT add explanations before the JSON.
- Do NOT add explanations after the JSON.
- Do NOT add comments outside the JSON.
- The value of "test_code" MUST be a normal JSON string.
- Escape newline characters inside "test_code" using \\n.
- Escape double quotes inside "test_code" using \\".
- Escape backslashes when required by JSON.
- The output must be directly parseable by json.loads().

============================================================
CORRECT JSON EXAMPLE
============================================================

{{
    "filename": "test_generated_agent.py",
    "test_code": "import pytest\\nfrom calculator import add_numbers\\n\\ndef test_add_numbers():\\n    assert add_numbers(10, 20) == 30",
    "reason": "Tests that add_numbers correctly adds two numbers."
}}

============================================================
INCORRECT JSON EXAMPLE
============================================================

DO NOT generate output like this:

{{
    "filename": "test_calculator.py",
    "test_code": \"\"\"
import pytest
from calculator import add_numbers

def test_add_numbers():
    assert add_numbers(10, 20) == 30
\"\"\",
    "reason": "Tests add_numbers."
}}

The incorrect example above is Python-style formatting and is
NOT valid JSON.

============================================================
FINAL OUTPUT FORMAT
============================================================

Return ONLY a single valid JSON object using exactly these
three fields:

{{
    "filename": "test_generated_agent.py",
    "test_code": "complete pytest source code encoded as a JSON string",
    "reason": "short explanation of what the tests verify"
}}
"""

    # ========================================================
    # CALL LLM
    # ========================================================

    try:

        response = llm.invoke(
            prompt
        )

    except Exception as exc:

        raise RuntimeError(
            "Failed to call the LLM for test generation: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    # ========================================================
    # EXTRACT RAW RESPONSE
    # ========================================================

    raw = getattr(
        response,
        "content",
        response,
    )

    if not isinstance(
        raw,
        str,
    ):
        raw = str(
            raw
        )

    raw = raw.strip()

    # ========================================================
    # DEBUG INFORMATION
    # ========================================================

    print(
        "\n"
        + "=" * 60
    )

    print(
        "PHASE 5 - RAW LLM TEST RESPONSE"
    )

    print(
        "=" * 60
    )

    print(
        raw
    )

    print(
        "=" * 60
    )

    # ========================================================
    # JSON EXTRACTION
    # ========================================================

    result = _extract_json(
        raw
    )

    if result is None:

        raise ValueError(
            "LLM did not return valid JSON test data.\n\n"
            "RAW LLM RESPONSE:\n"
            f"{raw[:10000]}"
        )

    # ========================================================
    # STRUCTURE VALIDATION
    # ========================================================

    if not isinstance(
        result,
        dict,
    ):

        raise ValueError(
            "Generated test result must be a dictionary."
        )

    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    required_fields = [
        "filename",
        "test_code",
        "reason",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in result
    ]

    if missing_fields:

        raise ValueError(
            "Generated test is missing required fields: "
            f"{missing_fields}"
        )

    # ========================================================
    # EXTRACT GENERATED DATA
    # ========================================================

    filename = result[
        "filename"
    ]

    test_code = result[
        "test_code"
    ]

    reason = result[
        "reason"
    ]

    # ========================================================
    # TYPE VALIDATION
    # ========================================================

    if not isinstance(
        filename,
        str,
    ):

        raise ValueError(
            "Generated test filename must be a string."
        )

    if not isinstance(
        test_code,
        str,
    ):

        raise ValueError(
            "Generated test_code must be a string."
        )

    if not isinstance(
        reason,
        str,
    ):

        raise ValueError(
            "Generated test reason must be a string."
        )

    # ========================================================
    # EMPTY VALUE VALIDATION
    # ========================================================

    if not filename.strip():

        raise ValueError(
            "Generated test filename cannot be empty."
        )

    if not test_code.strip():

        raise ValueError(
            "Generated test_code cannot be empty."
        )

    if not reason.strip():

        raise ValueError(
            "Generated test reason cannot be empty."
        )

    # ========================================================
    # FORCE SAFE TEMPORARY FILENAME
    # ========================================================
    #
    # Never trust the filename supplied by the LLM.
    #
    # The generated test will always use this controlled
    # filename.
    #
    # ========================================================

    filename = (
        "test_generated_agent.py"
    )

    # ========================================================
    # LOCAL TEST VALIDATION
    # ========================================================

    valid, message = validate_generated_test(
        test_code
    )

    if not valid:

        raise ValueError(
            message
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "\nPHASE 5 TEST GENERATION:"
    )

    print(
        f"Filename: {filename}"
    )

    print(
        f"Reason: {reason}"
    )

    print(
        "Test validation: PASSED"
    )

    return {
        "filename": filename,
        "test_code": test_code,
        "reason": reason,
    }


# ============================================================
# RUN GENERATED TEST
# ============================================================

def run_generated_test(
    project_path,
    test_code,
    timeout=60,
):
    """
    Execute the generated test inside the Docker sandbox.

    The user's project is NOT modified.

    The Docker runner:
    - validates the project path
    - creates a temporary copy of the project
    - writes the generated test into the temporary copy
    - executes pytest inside Docker
    - disables network access
    - applies resource limits
    - removes the container and temporary copy afterward
    """

    # ========================================================
    # PROJECT VALIDATION
    # ========================================================

    project_path = Path(
        project_path
    ).resolve()

    if not project_path.exists():

        raise ValueError(
            "Project path does not exist."
        )

    if not project_path.is_dir():

        raise ValueError(
            "Project path is not a directory."
        )

    # ========================================================
    # TEST VALIDATION
    # ========================================================

    valid, message = validate_generated_test(
        test_code
    )

    if not valid:

        raise ValueError(
            message
        )

    # ========================================================
    # DOCKER EXECUTION
    # ========================================================

    print(
        "\n"
        + "=" * 60
    )

    print(
        "PHASE 8 - RUNNING GENERATED TEST IN DOCKER SANDBOX"
    )

    print(
        "=" * 60
    )

    print(
        "Project:",
        str(project_path)
    )

    print(
        "Test file:",
        "test_generated_agent.py"
    )

    try:

        docker_result = run_generated_test_in_docker(
            project_path=str(project_path),
            filename="test_generated_agent.py",
            test_code=test_code,
            timeout=timeout,
        )

    except TypeError:

        # Backward-compatible fallback if the runner does not
        # expose timeout yet.
        try:

            docker_result = run_generated_test_in_docker(
                project_path=str(project_path),
                filename="test_generated_agent.py",
                test_code=test_code,
            )

        except Exception as exc:

            return {
                "passed": False,
                "return_code": 1,
                "stdout": "",
                "stderr": (
                    "Failed to execute generated test in Docker: "
                    f"{type(exc).__name__}: {exc}"
                ),
                "output": (
                    "Failed to execute generated test in Docker: "
                    f"{type(exc).__name__}: {exc}"
                ),
                "timed_out": False,
                "docker": True,
            }

    except Exception as exc:

        return {
            "passed": False,
            "return_code": 1,
            "stdout": "",
            "stderr": (
                "Failed to execute generated test in Docker: "
                f"{type(exc).__name__}: {exc}"
            ),
            "output": (
                "Failed to execute generated test in Docker: "
                f"{type(exc).__name__}: {exc}"
            ),
            "timed_out": False,
            "docker": True,
        }

    # ========================================================
    # CAPTURE OUTPUT
    # ========================================================

    stdout = (
        docker_result.get(
            "stdout",
            "",
        )
        or ""
    )

    stderr = (
        docker_result.get(
            "stderr",
            "",
        )
        or ""
    )

    output = (
        docker_result.get(
            "output",
            stdout + "\n" + stderr,
        )
        or ""
    ).strip()

    passed = bool(
        docker_result.get(
            "passed",
            False,
        )
    )

    return_code = docker_result.get(
        "return_code",
        -1,
    )

    timed_out = bool(
        docker_result.get(
            "timed_out",
            False,
        )
    )

    # ========================================================
    # RESULT
    # ========================================================

    result = {
        "passed": passed,
        "return_code": return_code,
        "stdout": stdout,
        "stderr": stderr,
        "output": output,
        "timed_out": timed_out,
        "docker": True,
    }

    # ========================================================
    # CONSOLE OUTPUT
    # ========================================================

    print(
        "\nGENERATED TEST RESULT:"
    )

    print(
        "DOCKER SANDBOX:",
        True,
    )

    print(
        "PASSED:",
        passed,
    )

    print(
        "RETURN CODE:",
        return_code,
    )

    print(
        "TIMED OUT:",
        timed_out,
    )

    if output:

        print(
            "\nOUTPUT:"
        )

        print(
            output
        )

    print(
        "=" * 60
    )

    return result
