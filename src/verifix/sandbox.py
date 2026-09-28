"""Docker sandbox executor: runs pytest on a workspace in an isolated container."""

from dataclasses import dataclass
from pathlib import Path

import docker
from requests.exceptions import ConnectionError, ReadTimeout

IMAGE = "verifix-sandbox"
TIMEOUT_SECONDS = 60


@dataclass
class SandboxResult:
    passed: bool
    exit_code: int
    logs: str
    timed_out: bool = False


def run_pytest(workspace: str, timeout: int = TIMEOUT_SECONDS) -> SandboxResult:
    """Run pytest inside the sandbox container against a workspace directory."""
    path = Path(workspace).resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Workspace not found: {path}")

    client = docker.from_env()
    container = client.containers.run(
        IMAGE,
        volumes={str(path): {"bind": "/app", "mode": "rw"}},
        network_disabled=True,
        mem_limit="512m",
        nano_cpus=1_000_000_000,
        pids_limit=128,
        detach=True,
    )
    try:
        try:
            result = container.wait(timeout=timeout)
        except (ReadTimeout, ConnectionError):
            container.kill()
            logs = container.logs().decode("utf-8", errors="replace")
            return SandboxResult(False, -1, logs + "\n[timed out]", timed_out=True)

        logs = container.logs().decode("utf-8", errors="replace")
        exit_code = result["StatusCode"]
        return SandboxResult(exit_code == 0, exit_code, logs)
    finally:
        container.remove(force=True)