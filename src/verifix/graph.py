"""LangGraph pipeline: planner -> tester -> coder -> executor -> reflector loop."""

from pathlib import Path

from langgraph.graph import END, StateGraph

from verifix.agents import coder, planner, reflector, tester
from verifix.sandbox import run_pytest
from verifix.state import AgentState


def _signature(logs: str) -> str:
    """Reduce pytest output to its failing assertion lines, ignoring noise like timings."""
    lines = [line for line in logs.splitlines() if line.startswith(("E ", "FAILED"))]
    return "\n".join(lines) or logs.strip()


def executor(state: AgentState) -> dict:
    workspace = str(Path(state["file_path"]).parent)
    result = run_pytest(workspace)
    print(f"[executor] tests_passed={result.passed} exit_code={result.exit_code}")

    if result.passed:
        return {"tests_passed": True, "execution_logs": result.logs}

    sig = _signature(result.logs)
    seen = state["seen_failures"]
    stuck = sig in seen
    if stuck:
        print("[executor] same failure as a previous attempt, flagging as stuck")
    return {
        "tests_passed": False,
        "execution_logs": result.logs,
        "seen_failures": seen + [sig],
        "stuck": stuck,
    }


def after_executor(state: AgentState) -> str:
    return "done" if state["tests_passed"] else "reflect"


def after_reflector(state: AgentState) -> str:
    return "retry" if state["retries"] < state["max_retries"] else "halt"


def build_graph():
    """Wire planner -> tester -> coder -> executor -> (reflector -> coder) loop."""
    graph = StateGraph(AgentState)
    graph.add_node("planner", planner)
    graph.add_node("tester", tester)
    graph.add_node("coder", coder)
    graph.add_node("executor", executor)
    graph.add_node("reflector", reflector)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "tester")
    graph.add_edge("tester", "coder")
    graph.add_edge("coder", "executor")
    graph.add_conditional_edges(
        "executor", after_executor, {"done": END, "reflect": "reflector"}
    )
    graph.add_conditional_edges(
        "reflector", after_reflector, {"retry": "coder", "halt": END}
    )
    return graph.compile()