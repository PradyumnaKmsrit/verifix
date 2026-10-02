"""Benchmark runner: single-shot Coder vs. the full Verifix loop, over a fixed task set."""

import json
import time
from pathlib import Path

from verifix.agents import coder, planner
from verifix.bench_tasks import TASKS
from verifix.graph import build_graph
from verifix.sandbox import run_pytest
from verifix.state import initial_state

BENCH_ROOT = Path("examples/bench")


def _setup(task: dict) -> Path:
    workspace = BENCH_ROOT / task["id"]
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "app.py").write_text(task["code"], encoding="utf-8")
    (workspace / "test_app.py").write_text(task["test"], encoding="utf-8")
    return workspace / "app.py"


def run_single_shot(task: dict) -> dict:
    """One Planner + Coder attempt, no retries, no Tester, no Reflector."""
    path = _setup(task)
    state = initial_state(task["task"], str(path), max_retries=0)
    start = time.time()
    state.update(planner(state))
    state.update(coder(state))
    result = run_pytest(str(path.parent))
    elapsed = time.time() - start
    return {"passed": result.passed, "retries": 0, "seconds": round(elapsed, 1)}


def run_full_loop(task: dict) -> dict:
    """Full planner -> tester -> coder -> executor -> reflector loop."""
    path = _setup(task)
    start = time.time()
    final = build_graph().invoke(initial_state(task["task"], str(path), max_retries=3))
    elapsed = time.time() - start
    return {
        "passed": final["tests_passed"],
        "retries": final["retries"],
        "seconds": round(elapsed, 1),
    }


def main() -> None:
    rows = []
    for task in TASKS:
        print(f"\n=== {task['id']} ===")
        print("-- single-shot --")
        single = run_single_shot(task)
        print(f"-- full loop --")
        full = run_full_loop(task)
        rows.append({"id": task["id"], "single_shot": single, "full_loop": full})

    single_passed = sum(r["single_shot"]["passed"] for r in rows)
    full_passed = sum(r["full_loop"]["passed"] for r in rows)
    n = len(rows)

    print("\n\n| Task | Single-shot | Full loop | Retries |")
    print("|------|-------------|-----------|---------|")
    for r in rows:
        s = "PASS" if r["single_shot"]["passed"] else "FAIL"
        f = "PASS" if r["full_loop"]["passed"] else "FAIL"
        print(f"| {r['id']} | {s} | {f} | {r['full_loop']['retries']} |")

    print(f"\nSingle-shot pass rate: {single_passed}/{n}")
    print(f"Full loop pass rate:   {full_passed}/{n}")

    Path("bench_results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("\nSaved details to bench_results.json")


if __name__ == "__main__":
    main()
