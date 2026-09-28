"""LangGraph pipeline for Verifix. The Reflector is a stub until the next step."""

from pathlib import Path

from langgraph.graph import END, StateGraph

from verifix.agents import coder, planner
from verifix.sandbox import run_pytest
from verifix.state import AgentState


def executor(state: AgentState) -> dict:
    workspace = str(Path(state["file_path"]).parent)
    result = run_pytest(workspace)
    print(f"[executor] tests_passed={result.passed} exit_code={result.exit_code}")
    return {"tests_passed": result.passed, "execution_logs": result.logs}


def reflector(state: AgentState) -> dict:
    print("[reflector] analysing failure")
    return {"diagnosis": "stub diagnosis", "retries": state["retries"] + 1}


def after_executor(state: AgentState) -> str:
    return "done" if state["tests_passed"] else "reflect"


def after_reflector(state: AgentState) -> str:
    return "retry" if state["retries"] < state["max_retries"] else "halt"


def build_graph():
    """Wire planner -> coder -> executor -> (reflector -> coder) loop."""
    graph = StateGraph(AgentState)
    graph.add_node("planner", planner)
    graph.add_node("coder", coder)
    graph.add_node("executor", executor)
    graph.add_node("reflector", reflector)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "executor")
    graph.add_conditional_edges(
        "executor", after_executor, {"done": END, "reflect": "reflector"}
    )
    graph.add_conditional_edges(
        "reflector", after_reflector, {"retry": "coder", "halt": END}
    )
    return graph.compile()