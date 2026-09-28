"""Command line entry point: uv run python -m verifix.cli FILE --task "..." """

import argparse
import difflib
from pathlib import Path

from verifix.graph import build_graph
from verifix.state import initial_state


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="verifix", description="Fix a Python file until its tests pass."
    )
    parser.add_argument("file", help="path to the source file to fix")
    parser.add_argument(
        "--task", default="Fix the bug so the tests pass", help="issue description"
    )
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    path = Path(args.file)
    original = path.read_text(encoding="utf-8")

    final = build_graph().invoke(
        initial_state(args.task, str(path), max_retries=args.max_retries)
    )

    if final["tests_passed"]:
        print(f"\nSUCCESS after {final['retries']} retries. Diff:\n")
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            path.read_text(encoding="utf-8").splitlines(keepends=True),
            fromfile=f"a/{path.name}",
            tofile=f"b/{path.name}",
        )
        print("".join(diff))
    else:
        path.write_text(original, encoding="utf-8")
        print(f"\nFAILED after {final['retries']} retries. Original file restored.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()