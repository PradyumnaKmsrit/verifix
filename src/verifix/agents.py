"""Verifix agents: Planner gathers context, Tester writes a repro test,
Coder proposes a fix, Reflector diagnoses failures."""

import ast
import re
from pathlib import Path

from verifix.events import emit
from verifix.llm import get_llm
from verifix.search import grep
from verifix.state import AgentState

FENCE = "`" * 3
MAX_LOG_CHARS = 3000

CODER_SYSTEM = (
    "You are a careful Python engineer. Fix the bug in the given source file "
    "so that the tests pass. Reply with the COMPLETE corrected contents of that "
    f"one source file inside a single {FENCE}python code block. "
    "Do not include the tests, other files, or any explanation."
)

REFLECTOR_SYSTEM = (
    "You are a debugging assistant. You are given a Python source file, its "
    "tests, and the failing test output. In two or three sentences, explain the "
    "root cause of the failure and what change would fix it. "
    "Do not write code blocks or the full corrected file."
)

TESTER_SYSTEM = (
    "You write a single pytest test function that reproduces a described bug. "
    "You will be given a task description and the current source file. Write "
    "ONE test function, named test_reported_issue, that currently FAILS "
    "because of the bug. Import only from the module shown. Reply with the "
    f"test function inside a single {FENCE}python code block and nothing else."
)


def _block(text: str) -> str:
    return f"{FENCE}python\n{text}\n{FENCE}"


def _tail(text: str, limit: int = MAX_LOG_CHARS) -> str:
    """Keep only the end of a long log, where pytest prints the failures."""
    return text if len(text) <= limit else "...\n" + text[-limit:]


def _collect_tests(workspace: Path, module: str) -> str:
    """Return the text of test files that reference the target module."""
    parts = []
    for test_file in sorted(workspace.glob("test_*.py")):
        content = test_file.read_text(encoding="utf-8")
        if module in content:
            parts.append(f"Test file {test_file.name} (read-only):\n{_block(content)}")
    return "\n\n".join(parts)


def extract_code(text: str) -> str:
    """Pull the first fenced code block out of an LLM reply."""
    pattern = FENCE + r"(?:python)?\n(.*?)" + FENCE
    match = re.search(pattern, text, re.DOTALL)
    return (match.group(1) if match else text).strip() + "\n"


def strip_echoed_tests(code: str, module: str) -> str:
    """Drop top-level test functions and self-imports the model copied from the tests.

    Returns an empty string if nothing but tests/imports remained -- the caller
    must not treat that as valid source code.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    drop: set[int] = set()
    for node in tree.body:
        is_test = isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        is_self_import = isinstance(node, ast.ImportFrom) and node.module == module
        if is_test or is_self_import:
            decorators = getattr(node, "decorator_list", [])
            start = min([node.lineno] + [d.lineno for d in decorators])
            drop.update(range(start, node.end_lineno + 1))

    kept = [line for n, line in enumerate(code.splitlines(), 1) if n not in drop]
    cleaned = "\n".join(kept).strip()
    return cleaned + "\n" if cleaned else ""


def _top_level_names(code: str) -> set[str]:
    """Names of top-level functions and classes defined in a source file."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }

def _strip_self_imports(code: str, module: str) -> str:
    """Remove any import of the target module from generated test code, since
    the caller already prepends the correct import line."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    drop: set[int] = set()
    for node in tree.body:
        is_plain_import = isinstance(node, ast.Import) and any(
            alias.name == module for alias in node.names
        )
        is_from_import = isinstance(node, ast.ImportFrom) and node.module == module
        if is_plain_import or is_from_import:
            drop.update(range(node.lineno, node.end_lineno + 1))

    kept = [line for n, line in enumerate(code.splitlines(), 1) if n not in drop]
    return "\n".join(kept).strip() + "\n"

def _find_related_files(root: Path, target: Path, task: str, limit: int = 2) -> list[str]:
    """Grep for function/class names mentioned in the task to find related files."""
    names = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b", task)
    found: list[str] = []
    for name in names:
        for hit in grep(root, rf"\b{re.escape(name)}\b"):
            file_part = hit.split(":", 1)[0]
            if file_part != target.name and file_part not in found:
                found.append(file_part)
        if len(found) >= limit:
            break
    return found[:limit]


def planner(state: AgentState) -> dict:
    path = Path(state["file_path"])
    code = path.read_text(encoding="utf-8")
    emit("planner", f"read {path} ({len(code.splitlines())} lines)")

    root = path.parent
    related = _find_related_files(root, path, state["task_description"])
    if related:
        emit("planner", f"found related files: {', '.join(related)}")

    return {"code_content": code, "related_files": related}

def tester(state: AgentState) -> dict:
    path = Path(state["file_path"])
    prompt = "\n\n".join(
        [
            f"Task: {state['task_description']}",
            f"Module name to import from: {path.stem}",
            f"Source file ({path.name}):\n{_block(state['code_content'])}",
        ]
    )
    emit("tester", "writing a reproduction test")
    reply = get_llm().invoke([("system", TESTER_SYSTEM), ("human", prompt)])
    test_code = _strip_self_imports(extract_code(reply.content), path.stem)

    test_path = path.parent / "test_reported_issue.py"
    names = sorted(_top_level_names(state["code_content"]))
    import_line = (
        f"from {path.stem} import {', '.join(names)}\n\n\n"
        if names
        else f"from {path.stem} import *\n\n\n"
    )
    test_path.write_text(import_line + test_code, encoding="utf-8")
    emit("tester", f"wrote {test_path.name}")
    return {}

def coder(state: AgentState) -> dict:
    path = Path(state["file_path"])
    parts = [
        f"Task: {state['task_description']}",
        f"Source file to fix ({path.name}):\n{_block(state['code_content'])}",
        _collect_tests(path.parent, path.stem),
    ]
    for rel in state["related_files"]:
        rel_path = path.parent / rel
        if rel_path.exists():
            parts.append(
                f"Related file {rel} (read-only, for context):\n"
                f"{_block(rel_path.read_text(encoding='utf-8'))}"
            )
    if state["execution_logs"]:
        parts.append(f"Output of the last test run:\n{_tail(state['execution_logs'])}")
    if state["diagnosis"]:
        parts.append(f"Diagnosis of the last failure:\n{state['diagnosis']}")

    emit("coder", f"attempt {state['retries'] + 1}")
    reply = get_llm().invoke(
        [("system", CODER_SYSTEM), ("human", "\n\n".join(parts))]
    )
    new_code = strip_echoed_tests(extract_code(reply.content), path.stem)

    if not new_code.strip():
        emit("coder", "reply was test-only, keeping previous source unchanged")
        new_code = state["code_content"]
    else:
        before = _top_level_names(state["code_content"])
        after = _top_level_names(new_code)
        if before and not (before & after):
            emit(
                "coder",
                f"reply dropped expected definitions {sorted(before)}, "
                "keeping previous source unchanged",
            )
            new_code = state["code_content"]

    path.write_text(new_code, encoding="utf-8")
    return {"code_content": new_code}


def reflector(state: AgentState) -> dict:
    path = Path(state["file_path"])
    stuck_note = (
        "\n\nNote: your previous suggestion did not change the outcome. "
        "The failure is identical to a prior attempt. Propose a genuinely "
        "different approach, not a small variation of the last one."
        if state["stuck"]
        else ""
    )
    prompt = "\n\n".join(
        [
            f"Source file ({path.name}):\n{_block(state['code_content'])}",
            _collect_tests(path.parent, path.stem),
            f"Failing test output:\n{_tail(state['execution_logs'])}{stuck_note}",
        ]
    )
    emit(
        "reflector",
        "analysing failure" + (" (stuck, forcing replan)" if state["stuck"] else ""),
    )
    reply = get_llm().invoke([("system", REFLECTOR_SYSTEM), ("human", prompt)])
    return {"diagnosis": reply.content.strip(), "retries": state["retries"] + 1}