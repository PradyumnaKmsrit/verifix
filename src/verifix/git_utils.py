"""Minimal git helpers: run each fix attempt on its own disposable branch."""

import subprocess
import uuid
from pathlib import Path


def _run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def repo_root(path: Path) -> Path:
    out = _run(["rev-parse", "--show-toplevel"], cwd=path.parent)
    return Path(out)


def start_fix_branch(target_file: Path) -> tuple[Path, str, str]:
    """Create and check out a new branch for this fix attempt.

    Returns (repo_root, branch_name, original_branch).
    """
    root = repo_root(target_file)
    original_branch = _run(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    branch = f"verifix/fix-{uuid.uuid4().hex[:8]}"
    _run(["checkout", "-b", branch], cwd=root)
    return root, branch, original_branch


def finish_fix_branch(root: Path, branch: str, original_branch: str, keep: bool) -> None:
    """Return to the original branch. Delete the fix branch unless keep is True."""
    _run(["checkout", original_branch], cwd=root)
    if not keep:
        _run(["branch", "-D", branch], cwd=root)