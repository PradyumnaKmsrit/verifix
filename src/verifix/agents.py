"""Verifix agents. Planner gathers context, Coder proposes a fix via the LLM."""

import ast
import re
from pathlib import Path

from verifix.llm import get_llm
from verifix.state import AgentState

FENCE = "`" * 3

CODER_SYSTEM = (
    "You are a careful Python engineer. Fix the bug in the given source file "
    "so that the tests pass. Reply with the COMPLETE corrected contents of that "
    f"one source file inside a single {FENCE}python code block. "
    "Do not include the tests, other files, or any explanation."
)


def _block(text: str) -> str:
    return f"{FENCE}python\n{text}\n{FENCE}"


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
    """Drop top-level test functions and self-imports the model copied from the tests."""
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
    return cleaned + "\n" if cleaned else code


def planner(state: AgentState) -> dict:
    path = Path(state["file_path"])
    code = path.read_text(encoding="utf-8")
    print(f"[planner] read {path} ({len(code.splitlines())} lines)")
    return {"code_content": code}


def coder(state: AgentState) -> dict:
    path = Path(state["file_path"])
    parts = [
        f"Task: {state['task_description']}",
        f"Source file to fix ({path.name}):\n{_block(state['code_content'])}",
        _collect_tests(path.parent, path.stem),
    ]
    if state["execution_logs"]:
        parts.append(f"Output of the last test run:\n{state['execution_logs']}")
    if state["diagnosis"]:
        parts.append(f"Diagnosis of the last failure:\n{state['diagnosis']}")

    print(f"[coder] attempt {state['retries'] + 1}")
    reply = get_llm().invoke(
        [("system", CODER_SYSTEM), ("human", "\n\n".join(parts))]
    )
    new_code = strip_echoed_tests(extract_code(reply.content), path.stem)
    path.write_text(new_code, encoding="utf-8")
    return {"code_content": new_code}