"""
🖥️ FASTAPI DEMO SERVER (DAY 03: CHATBOT VS REACT AGENT)
Phục vụ giao diện demo realtime: Chatbot Baseline (Cấp 2) và ReAct Agent streaming qua SSE (Cấp 3).
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
STATIC_DIR = Path(__file__).resolve().parent / "static"
DOCS_TRACE_PATH = BASE_DIR / "docs" / "trace_waterfall.json"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import iter_react_steps, load_test_cases
from mcp_server import MCPAcademicServer
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

app = FastAPI(title="VinUni Day03 - Chatbot vs ReAct Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = get_llm_provider()
mcp_server = MCPAcademicServer()

if not STATIC_DIR.is_dir():
    # Trên serverless (Vercel) hệ thống tệp chỉ đọc, nên chỉ tạo khi thật sự thiếu
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class QuestionRequest(BaseModel):
    question: str


@app.exception_handler(Exception)
async def handle_unexpected_error(request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/")
async def serve_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(str(index_path))
    return {"message": "ok"}


@app.get("/api/health")
async def health():
    return {
        "provider": provider.__class__.__name__,
        "model": provider.model_name,
        "mcp_server": mcp_server.server_name,
        "mcp_version": mcp_server.version,
        "max_iterations": MAX_ITERATIONS,
    }


@app.get("/api/tools")
async def tools():
    return {
        "server": mcp_server.server_name,
        "version": mcp_server.version,
        "tools": mcp_server.list_tools(),
    }


@app.get("/api/test-cases")
async def test_cases():
    return load_test_cases()


@app.get("/api/trace")
async def trace():
    if not DOCS_TRACE_PATH.is_file():
        return []
    with open(DOCS_TRACE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/chatbot")
async def chatbot(payload: QuestionRequest):
    started = time.perf_counter()
    answer = provider.generate(payload.question, system_prompt=CHATBOT_BASELINE_PROMPT)
    return {
        "answer": answer,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "provider": provider.__class__.__name__,
        "model": provider.model_name,
    }


def _sse(event_name: str, data: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _stream_agent_events(question: str):
    try:
        for event in iter_react_steps(question, provider, mcp_server):
            payload = {key: value for key, value in event.items() if key != "event"}
            yield _sse(event["event"], payload)
    except Exception as exc:
        yield _sse("error", {"message": str(exc)})
        yield _sse("done", {"trace": [], "total_latency_ms": 0})


@app.post("/api/agent")
async def agent(payload: QuestionRequest):
    return StreamingResponse(
        _stream_agent_events(payload.question),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
