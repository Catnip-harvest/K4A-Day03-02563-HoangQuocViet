"""
▲ VERCEL ENTRY POINT
Nạp FastAPI app từ ui/server.py để chạy trên Vercel Python Runtime (serverless).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
for path in (str(ROOT_DIR), str(ROOT_DIR / "src")):
    if path not in sys.path:
        sys.path.insert(0, path)

from ui.server import app as fastapi_app  # noqa: E402

FUNCTION_PREFIX = "/api/index"


class StripFunctionPrefix:
    """
    Vercel rewrite mọi request về '/api/index' và từ 2026 truyền luôn đường dẫn đã
    rewrite vào ứng dụng, khiến FastAPI không khớp được route nào. Lớp bọc này cắt
    tiền tố đó ra để app định tuyến theo đường dẫn gốc mà người dùng gọi.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            path = scope.get("path", "")
            if path == FUNCTION_PREFIX or path.startswith(FUNCTION_PREFIX + "/"):
                trimmed = path[len(FUNCTION_PREFIX):] or "/"
                scope = dict(scope)
                scope["path"] = trimmed
                scope["raw_path"] = trimmed.encode("utf-8")
        await self.inner(scope, receive, send)


app = StripFunctionPrefix(fastapi_app)
