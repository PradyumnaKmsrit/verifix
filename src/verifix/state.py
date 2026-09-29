"""Shared state passed between all Verifix agents."""

from typing import TypedDict


class AgentState(TypedDict):
    task_description: str
    file_path: str
    code_content: str
    plan: str
    execution_logs: str
    tests_passed: bool
    diagnosis: str
    retries: int
    max_retries: int
    seen_failures: list[str]
    stuck: bool


def initial_state(
    task_description: str, file_path: str, max_retries: int = 3
) -> AgentState:
    """Build the starting state for a run."""
    return AgentState(
        task_description=task_description,
        file_path=file_path,
        code_content="",
        plan="",
        execution_logs="",
        tests_passed=False,
        diagnosis="",
        retries=0,
        max_retries=max_retries,
        seen_failures=[],
        stuck=False,
    )