"""Command line entry point: uv run python -m verifix.cli FILE --task "..." """

import argparse
import difflib
from pathlib import Path

from verifix.git_utils import finish_fix_branch, start_fix_branch
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

    path = Path(args.file).resolve()
    original = path.read_text(encoding="utf-8")

    root, branch, original_branch = start_fix_branch(path)
    print(f"[git] working on branch {branch}")

    try:
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
            finish_fix_branch(root, branch, original_branch, keep=True)
            print(f"[git] fix kept on branch {branch}, back on {original_branch}")
        else:
            path.write_text(original, encoding="utf-8")
            print(f"\nFAILED after {final['retries']} retries.")
            finish_fix_branch(root, branch, original_branch, keep=False)
            print(f"[git] branch discarded, back on {original_branch}")
            raise SystemExit(1)
    except Exception:
        path.write_text(original, encoding="utf-8")
        finish_fix_branch(root, branch, original_branch, keep=False)
        raise


if __name__ == "__main__":
    main()