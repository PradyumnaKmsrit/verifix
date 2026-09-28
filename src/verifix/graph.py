"""LangGraph skeleton for Verifix. Nodes are stubs until later phases."""

from langgraph.graph import END, StateGraph

from verifix.state import AgentState


def planner(state: AgentState) -> dict:
    print("[planner] reading target file")
    return {"code_content": "# stub: file contents", "plan": "stub plan"}


def coder(state: AgentState) -> dict:
    print(f"[coder] attempt {state['retries'] + 1}")
    return {"code_content": state["code_content"] + "\n# stub patch"}


def executor(state: AgentState) -> dict:
    # Stub: fail on the first attempt, pass on the second.
    passed = state["retries"] >= 1
    print(f"[executor] tests_passed={passed}")
    return {
        "tests_passed": passed,
        "execution_logs": "stub: all passed" if passed else "stub: 1 failed",
    }


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