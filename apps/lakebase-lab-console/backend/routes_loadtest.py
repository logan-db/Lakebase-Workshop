"""Load test routes: start/stop synthetic traffic, stream metrics via SSE."""

import asyncio
import json
import time
import uuid
from collections import deque
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .db import get_connection

router = APIRouter(prefix="/api/loadtest", tags=["loadtest"])

_active_tests: dict[str, dict] = {}


class LoadTestRequest(BaseModel):
    concurrency: int = Field(default=5, ge=1, le=50)
    duration_seconds: int = Field(default=30, ge=5, le=300)
    write_ratio: float = Field(default=0.3, ge=0.0, le=1.0)
    branch_id: str | None = None


class LoadTestStatus(BaseModel):
    test_id: str
    running: bool
    elapsed_seconds: float
    total_queries: int
    total_errors: int
    qps: float
    avg_latency_ms: float
    p95_latency_ms: float


def _run_query(is_write: bool, branch_id: str | None):
    """Execute a single test query and return latency in ms."""
    start = time.monotonic()
    try:
        with get_connection(branch_id) as conn:
            with conn.cursor() as cur:
                if is_write:
                    cur.execute(
                        "INSERT INTO demo.events (event_type, source, payload) "
                        "VALUES (%s, %s, %s)",
                        ("loadtest", "lab-console", json.dumps({"ts": time.time()})),
                    )
                    conn.commit()
                else:
                    cur.execute(
                        "SELECT count(*) FROM demo.events WHERE event_type = 'loadtest'"
                    )
                    cur.fetchone()
        latency = (time.monotonic() - start) * 1000
        return latency, None
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return latency, str(e)


async def _worker(test_id: str, is_write: bool, branch_id: str | None):
    """Single async worker that runs queries in a loop."""
    state = _active_tests.get(test_id)
    if not state:
        return
    loop = asyncio.get_event_loop()
    while state["running"]:
        latency, error = await loop.run_in_executor(
            None, _run_query, is_write, branch_id
        )
        state["total_queries"] += 1
        state["latencies"].append(latency)
        if error:
            state["total_errors"] += 1
        await asyncio.sleep(0.01)


async def _orchestrator(test_id: str, req: LoadTestRequest):
    """Manage the load test lifecycle."""
    state = _active_tests[test_id]
    tasks = []

    for i in range(req.concurrency):
        is_write = (i / req.concurrency) < req.write_ratio
        tasks.append(asyncio.create_task(_worker(test_id, is_write, req.branch_id)))

    await asyncio.sleep(req.duration_seconds)
    state["running"] = False

    for t in tasks:
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass


@router.post("/start", response_model=LoadTestStatus)
async def start_load_test(req: LoadTestRequest):
    """Start a new load test."""
    if any(s["running"] for s in _active_tests.values()):
        raise HTTPException(409, "A load test is already running")

    test_id = str(uuid.uuid4())[:8]
    _active_tests[test_id] = {
        "running": True,
        "start_time": time.monotonic(),
        "total_queries": 0,
        "total_errors": 0,
        "latencies": deque(maxlen=10000),
        "concurrency": req.concurrency,
    }

    asyncio.create_task(_orchestrator(test_id, req))

    return LoadTestStatus(
        test_id=test_id,
        running=True,
        elapsed_seconds=0,
        total_queries=0,
        total_errors=0,
        qps=0,
        avg_latency_ms=0,
        p95_latency_ms=0,
    )


@router.post("/stop/{test_id}")
def stop_load_test(test_id: str):
    """Stop a running load test."""
    state = _active_tests.get(test_id)
    if not state:
        raise HTTPException(404, "Test not found")
    state["running"] = False
    return {"status": "stopped", "test_id": test_id}


@router.get("/status/{test_id}", response_model=LoadTestStatus)
def get_load_test_status(test_id: str):
    """Get current status of a load test."""
    state = _active_tests.get(test_id)
    if not state:
        raise HTTPException(404, "Test not found")

    elapsed = time.monotonic() - state["start_time"]
    latencies = list(state["latencies"])
    sorted_lat = sorted(latencies) if latencies else [0]

    return LoadTestStatus(
        test_id=test_id,
        running=state["running"],
        elapsed_seconds=round(elapsed, 1),
        total_queries=state["total_queries"],
        total_errors=state["total_errors"],
        qps=round(state["total_queries"] / max(elapsed, 0.1), 1),
        avg_latency_ms=round(sum(sorted_lat) / max(len(sorted_lat), 1), 2),
        p95_latency_ms=round(sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0, 2),
    )


@router.get("/stream/{test_id}")
async def stream_metrics(test_id: str):
    """Server-Sent Events stream of load test metrics."""
    state = _active_tests.get(test_id)
    if not state:
        raise HTTPException(404, "Test not found")

    async def event_generator():
        while state.get("running", False):
            elapsed = time.monotonic() - state["start_time"]
            latencies = list(state["latencies"])
            sorted_lat = sorted(latencies) if latencies else [0]

            data = {
                "test_id": test_id,
                "running": state["running"],
                "elapsed_seconds": round(elapsed, 1),
                "total_queries": state["total_queries"],
                "total_errors": state["total_errors"],
                "qps": round(state["total_queries"] / max(elapsed, 0.1), 1),
                "avg_latency_ms": round(sum(sorted_lat) / max(len(sorted_lat), 1), 2),
                "p95_latency_ms": round(
                    sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0, 2
                ),
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(1)

        yield f"data: {json.dumps({'running': False, 'test_id': test_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
