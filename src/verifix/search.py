"""Simple repo-scoped search tools, used by the Planner to find related code."""

import re
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}


def list_py_files(root: Path) -> list[Path]:
    return [
        p
        for p in root.rglob("*.py")
        if not any(part in SKIP_DIRS for part in p.parts)
    ]


def grep(root: Path, pattern: str, max_results: int = 20) -> list[str]:
    """Search .py files under root for a pattern. Returns 'path:line: text' entries."""
    regex = re.compile(pattern)
    hits: list[str] = []
    for path in list_py_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            if regex.search(line):
                hits.append(f"{path.relative_to(root)}:{i}: {line.strip()}")
                if len(hits) >= max_results:
                    return hits
    return hits