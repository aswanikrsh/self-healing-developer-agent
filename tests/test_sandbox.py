import pytest

from execution.sandbox import DockerSandbox


@pytest.fixture
def project_path():
    return (
        r"D:\desktop\self_healing_agent"
        r"\self_healing_agent"
        r"\workspace"
        r"\test_project"
    )


def test_docker_sandbox_initializes():
    sandbox = DockerSandbox()

    try:
        assert sandbox is not None
        assert sandbox.image
        assert sandbox.timeout > 0
    finally:
        sandbox.close()


def test_docker_sandbox_is_available():
    sandbox = DockerSandbox()

    try:
        result = sandbox.check_available()

        assert isinstance(
            result,
            dict,
        )

        assert "available" in result
        assert "message" in result

    finally:
        sandbox.close()


@pytest.mark.integration
def test_docker_runs_project_tests(
    project_path,
):
    sandbox = DockerSandbox()

    try:
        result = sandbox.run_tests(
            project_path,
            pytest_args=["-q"],
        )

        assert result["docker"] is True
        assert "passed" in result
        assert "return_code" in result

    finally:
        sandbox.close()