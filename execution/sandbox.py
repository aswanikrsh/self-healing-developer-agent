from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

import docker
from django.conf import settings


class DockerSandbox:
    """
    Phase 8 Docker execution sandbox.

    The original project is NEVER mounted directly into the
    container.

    Instead:

        Original project
              ↓
        Temporary copy
              ↓
        Docker container
              ↓
        pytest
              ↓
        Result

    This prevents the container from directly modifying the
    user's working project.
    """

    def __init__(self):
        self.image = settings.DOCKER_SANDBOX_IMAGE

        self.timeout = int(
            settings.DOCKER_SANDBOX_TIMEOUT
        )

        self.memory = settings.DOCKER_SANDBOX_MEMORY

        self.cpus = float(
            settings.DOCKER_SANDBOX_CPUS
        )

        self.pids_limit = int(
            settings.DOCKER_SANDBOX_PIDS_LIMIT
        )

        self.network_disabled = bool(
            settings.DOCKER_SANDBOX_NETWORK_DISABLED
        )

        self.read_only_root = bool(
            settings.DOCKER_SANDBOX_READ_ONLY_ROOT
        )

        self.client = docker.from_env()

    # ========================================================
    # DOCKER AVAILABILITY
    # ========================================================

    def check_available(self) -> Dict[str, Any]:
        """
        Verify that Docker is reachable and the required image
        exists.
        """

        try:
            self.client.ping()

        except Exception as exc:
            return {
                "available": False,
                "message": (
                    "Docker is not available: "
                    f"{type(exc).__name__}: {exc}"
                ),
            }

        try:
            self.client.images.get(
                self.image
            )

        except docker.errors.ImageNotFound:
            return {
                "available": False,
                "message": (
                    f"Docker image '{self.image}' "
                    "was not found. Build it first."
                ),
            }

        except Exception as exc:
            return {
                "available": False,
                "message": (
                    "Unable to access Docker image: "
                    f"{type(exc).__name__}: {exc}"
                ),
            }

        return {
            "available": True,
            "message": "Docker sandbox is available.",
        }

    # ========================================================
    # PROJECT VALIDATION
    # ========================================================

    def _validate_project(
        self,
        project_path: str,
    ) -> Path:
        """
        Validate the project path before copying it.
        """

        path = Path(
            project_path
        ).resolve()

        if not path.exists():
            raise FileNotFoundError(
                f"Project path does not exist: {path}"
            )

        if not path.is_dir():
            raise ValueError(
                f"Project path is not a directory: {path}"
            )

        return path

    # ========================================================
    # COPY PROJECT
    # ========================================================

    def _copy_project(
        self,
        source: Path,
        destination: Path,
    ) -> None:
        """
        Copy the project into an isolated temporary directory.

        Large/generated/cache directories are excluded.
        """

        ignored_names = {
            ".git",
            ".venv",
            "venv",
            "env",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "node_modules",
            "dist",
            "build",
        }

        def ignore_function(
            directory,
            names,
        ):
            ignored = []

            for name in names:
                if name in ignored_names:
                    ignored.append(name)

            return ignored

        shutil.copytree(
            source,
            destination,
            ignore=ignore_function,
        )

    # ========================================================
    # GENERATED TEST
    # ========================================================

    def _write_generated_test(
        self,
        project_copy: Path,
        filename: str,
        test_code: str,
    ) -> Path:
        """
        Safely create a generated test inside the temporary
        project copy.
        """

        clean_name = Path(
            filename
        ).name

        if clean_name != filename:
            raise ValueError(
                "Generated test filename must not contain "
                "directory traversal."
            )

        if not clean_name.endswith(
            ".py"
        ):
            raise ValueError(
                "Generated test must be a Python file."
            )

        target = (
            project_copy
            / clean_name
        )

        target.write_text(
            test_code,
            encoding="utf-8",
        )

        return target

    # ========================================================
    # RUN CONTAINER
    # ========================================================

    def _run_container(
        self,
        project_copy: Path,
        pytest_args,
    ) -> Dict[str, Any]:
        """
        Run pytest inside an isolated Docker container.
        """

        availability = (
            self.check_available()
        )

        if not availability["available"]:
            return {
                "passed": False,
                "return_code": -1,
                "stdout": "",
                "stderr": availability[
                    "message"
                ],
                "timed_out": False,
                "docker": True,
            }

        container = None
        started_at = time.monotonic()

        try:
            command = [
                "python",
                "-m",
                "pytest",
            ]

            command.extend(
                pytest_args
            )

            container = (
                self.client.containers.run(
                    image=self.image,
                    command=command,
                    volumes={
                        str(project_copy): {
                            "bind": "/workspace",
                            "mode": "rw",
                        }
                    },
                    working_dir="/workspace",
                    detach=True,
                    network_disabled=(
                        self.network_disabled
                    ),
                    read_only=(
                        self.read_only_root
                    ),
                    cap_drop=["ALL"],
                    security_opt=[
                        "no-new-privileges:true"
                    ],
                    mem_limit=self.memory,
                    nano_cpus=int(
                        self.cpus
                        * 1_000_000_000
                    ),
                    pids_limit=self.pids_limit,
                    tmpfs={
                        "/tmp": (
                            "rw,nosuid,"
                            "size=64m"
                        )
                    },
                )
            )

            # ------------------------------------------------
            # WAIT WITH TIMEOUT
            # ------------------------------------------------

            try:
                wait_result = container.wait(
                    timeout=self.timeout
                )

            except Exception as exc:
                # The wait operation timed out or Docker
                # reported an execution/waiting problem.

                try:
                    container.kill()
                except Exception:
                    pass

                stdout = (
                    container.logs(
                        stdout=True,
                        stderr=False,
                    )
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )

                stderr = (
                    container.logs(
                        stdout=False,
                        stderr=True,
                    )
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )

                return {
                    "passed": False,
                    "return_code": -1,
                    "stdout": stdout,
                    "stderr": (
                        stderr
                        + "\n"
                        + "Docker sandbox timeout."
                        + f"\nTimeout: {self.timeout} seconds."
                    ),
                    "timed_out": True,
                    "duration": (
                        time.monotonic()
                        - started_at
                    ),
                    "docker": True,
                }

            # ------------------------------------------------
            # READ CONTAINER OUTPUT
            # ------------------------------------------------

            stdout = (
                container.logs(
                    stdout=True,
                    stderr=False,
                )
                .decode(
                    "utf-8",
                    errors="replace",
                )
            )

            stderr = (
                container.logs(
                    stdout=False,
                    stderr=True,
                )
                .decode(
                    "utf-8",
                    errors="replace",
                )
            )

            return_code = int(
                wait_result.get(
                    "StatusCode",
                    1,
                )
            )

            return {
                "passed": (
                    return_code == 0
                ),
                "return_code": return_code,
                "stdout": stdout,
                "stderr": stderr,
                "timed_out": False,
                "duration": (
                    time.monotonic()
                    - started_at
                ),
                "docker": True,
            }

        except Exception as exc:
            return {
                "passed": False,
                "return_code": -1,
                "stdout": "",
                "stderr": (
                    "Docker execution error: "
                    f"{type(exc).__name__}: {exc}"
                ),
                "timed_out": False,
                "duration": (
                    time.monotonic()
                    - started_at
                ),
                "docker": True,
            }

        finally:
            if container is not None:
                try:
                    container.remove(
                        force=True
                    )
                except Exception:
                    pass

    # ========================================================
    # RUN PROJECT TESTS
    # ========================================================

    def run_tests(
        self,
        project_path: str,
        pytest_args=None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run the project's pytest suite inside Docker.

        If timeout is supplied, it applies only to this
        execution.
        """

        if pytest_args is None:
            pytest_args = [
                "-q"
            ]

        # --------------------------------------------
        # Apply optional execution-specific timeout
        # --------------------------------------------

        original_timeout = self.timeout

        if timeout is not None:
            timeout = int(timeout)

            if timeout <= 0:
                raise ValueError(
                    "Timeout must be greater than zero."
                )

            self.timeout = timeout

        source = self._validate_project(
            project_path
        )

        temporary_root = Path(
            tempfile.mkdtemp(
                prefix="self_healing_docker_"
            )
        )

        project_copy = (
            temporary_root
            / "project"
        )

        try:
            self._copy_project(
                source,
                project_copy,
            )

            return self._run_container(
                project_copy,
                pytest_args,
            )

        finally:
            shutil.rmtree(
                temporary_root,
                ignore_errors=True,
            )

            # Restore the sandbox's default timeout
            # after this particular execution.
            self.timeout = original_timeout

    # ========================================================
    # RUN GENERATED TEST
    # ========================================================

    def run_generated_test(
        self,
        project_path: str,
        filename: str,
        test_code: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run a generated test inside Docker.

        If timeout is supplied, it applies only to this
        generated-test execution.
        """

        # --------------------------------------------
        # Apply optional execution-specific timeout
        # --------------------------------------------

        original_timeout = self.timeout

        if timeout is not None:
            timeout = int(timeout)

            if timeout <= 0:
                raise ValueError(
                    "Timeout must be greater than zero."
                )

            self.timeout = timeout

        source = self._validate_project(
            project_path
        )

        temporary_root = Path(
            tempfile.mkdtemp(
                prefix="self_healing_generated_docker_"
            )
        )

        project_copy = (
            temporary_root
            / "project"
        )

        try:
            self._copy_project(
                source,
                project_copy,
            )

            self._write_generated_test(
                project_copy,
                filename,
                test_code,
            )

            return self._run_container(
                project_copy,
                [
                    filename,
                    "-q",
                ],
            )

        finally:
            shutil.rmtree(
                temporary_root,
                ignore_errors=True,
            )

            # Restore the sandbox's default timeout
            # after this particular execution.
            self.timeout = original_timeout

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):
        """
        Close the Docker SDK client.
        """

        try:
            self.client.close()
        except Exception:
            pass