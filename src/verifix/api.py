"""FastAPI server: runs a Verifix fix and streams agent progress over SSE."""

import asyncio
import difflib
import json
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from verifix.events import set_listener
from verifix.graph import build_graph
from verifix.state import initial_state

app = FastAPI(title="Verifix API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    file_path: str
    task: str
    max_retries: int = 3


def _diff(original: str, updated: str, name: str) -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{name}",
            tofile=f"b/{name}",
        )
    )


def _run_graph_in_thread(req: RunRequest, events: Queue) -> None:
    def listener(node: str, message: str) -> None:
        events.put({"node": node, "message": message})

    token = set_listener(listener)
    try:
        path = Path(req.file_path).resolve()
        original = path.read_text(encoding="utf-8")
        final = build_graph().invoke(
            initial_state(req.task, str(path), max_retries=req.max_retries)
        )
        attempted_code = final["code_content"]
        diff = _diff(original, attempted_code, path.name)

        if not final["tests_passed"]:
            path.write_text(original, encoding="utf-8")

        events.put(
            {
                "node": "done",
                "message": "success" if final["tests_passed"] else "failed",
                "passed": final["tests_passed"],
                "retries": final["retries"],
                "diff": diff,
                "code": attempted_code,
            }
        )
    except Exception as exc:  # noqa: BLE001
        events.put({"node": "error", "message": str(exc)})
    finally:
        events.put(None)


@app.post("/run")
async def run(req: RunRequest):
    """Start a fix run and stream its progress as Server-Sent Events."""
    events: Queue = Queue()
    Thread(target=_run_graph_in_thread, args=(req, events), daemon=True).start()

    async def event_stream():
        loop = asyncio.get_event_loop()
        while True:
            item = await loop.run_in_executor(None, _get, events)
            if item is None:
                break
            yield {"event": "progress", "data": json.dumps(item)}

    return EventSourceResponse(event_stream())


def _get(events: Queue):
    try:
        return events.get(timeout=300)
    except Empty:
        return {"node": "error", "message": "timed out waiting for progress"}


@app.get("/health")
async def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="src/verifix/static", html=True), name="static")