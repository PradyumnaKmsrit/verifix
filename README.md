# Verifix

A self-correcting coding agent that patches code and verifies fixes in an
isolated Docker sandbox, built with LangGraph.

## How it works

1. **Planner** reads the target file and greps the repo for related files.
2. **Tester** writes a new test that reproduces the reported bug.
3. **Coder** proposes a fix using a local LLM (Ollama).
4. **Executor** runs the full test suite inside a network-disabled,
   resource-limited Docker container.
5. **Reflector** diagnoses a failure and feeds that diagnosis back to the
   Coder for the next attempt, up to a configurable retry limit.

Each run works on its own disposable git branch: a successful fix is kept
for review, a failed one is discarded automatically, and the original file
is restored if anything crashes mid-run.

## Usage

```powershell
uv run python -m verifix.cli path/to/file.py --task "describe the bug"
```

## Benchmark

Six bug-fixing tasks, run two ways: a single Coder attempt with no retries,
versus the full Verifix loop (Planner, Tester, Coder, Executor, Reflector,
up to 3 retries). Model: qwen2.5-coder:1.5b, local, via Ollama.

| Task | Single-shot | Full loop | Retries |
|------|-------------|-----------|---------|
| add | PASS | PASS | 0 |
| median | FAIL | PASS | 1 |
| discount | PASS | PASS | 0 |
| bank_withdraw | FAIL | FAIL | 3 |
| is_palindrome | PASS | PASS | 0 |
| factorial | PASS | PASS | 0 |

**Single-shot pass rate: 4/6. Full loop pass rate: 5/6.**

The loop recovered a task (`median`) that a single attempt couldn't fix, by
diagnosing the failure and retrying. `bank_withdraw` fails on every attempt
because it needs a non-trivial control-flow change (raising an exception
before a mutation happens) that a 1.5B model struggles to produce, even with
feedback.

Reproduce with:

```powershell
uv run python -m verifix.bench
```

## Stack

LangGraph, Ollama (qwen2.5-coder), Docker SDK for Python, pytest, uv.