from __future__ import annotations

from typing import Any, Dict, Optional

from django.conf import settings

from .sandbox import DockerSandbox


def run_project_tests(
    project_path: str,
    pytest_args: Optional[list] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run the project's pytest suite inside the configured
    execution environment.
    """

    execution_mode = getattr(
        settings,
        "EXECUTION_MODE",
        "docker",
    ).lower()

    if execution_mode != "docker":
        return {
            "passed": False,
            "return_code": -1,
            "stdout": "",
            "stderr": (
                f"Unsupported execution mode: "
                f"{execution_mode}"
            ),
            "docker": False,
        }

    sandbox = DockerSandbox()

    try:
        return sandbox.run_tests(
            project_path=project_path,
            pytest_args=pytest_args,
            timeout=timeout,
        )

    finally:
        sandbox.close()


def run_generated_test(
    project_path: str,
    filename: str,
    test_code: str,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run a generated test inside the Docker sandbox.
    """

    execution_mode = getattr(
        settings,
        "EXECUTION_MODE",
        "docker",
    ).lower()

    if execution_mode != "docker":
        return {
            "passed": False,
            "return_code": -1,
            "stdout": "",
            "stderr": (
                f"Unsupported execution mode: "
                f"{execution_mode}"
            ),
            "docker": False,
        }

    sandbox = DockerSandbox()

    try:
        return sandbox.run_generated_test(
            project_path=project_path,
            filename=filename,
            test_code=test_code,
            timeout=timeout,
        )

    finally:
        sandbox.close()