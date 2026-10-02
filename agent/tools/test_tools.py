from execution.runner import run_project_tests


def run_tests(project_path, timeout=60):
    """
    Run pytest inside the Docker sandbox.

    The original project is never mounted directly into the container.
    The Docker runner creates a temporary project copy and executes pytest
    against that copy.
    """

    try:
        result = run_project_tests(
            project_path=project_path,
            pytest_args=["-q"],
            timeout=timeout,
        )

        return {
            "return_code": result.get("return_code", -1),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "passed": result.get("passed", False),
            "timed_out": result.get("timed_out", False),
            "docker": result.get("docker", True),
        }

    except Exception as exc:
        return {
            "return_code": -1,
            "stdout": "",
            "stderr": str(exc),
            "passed": False,
            "timed_out": False,
            "docker": True,
        }