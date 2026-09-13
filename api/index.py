"""
▲ VERCEL ENTRY POINT
Nạp FastAPI app từ ui/server.py để chạy trên Vercel Python Runtime (serverless).
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
for path in (str(ROOT_DIR), str(ROOT_DIR / "src")):
    if path not in sys.path:
        sys.path.insert(0, path)

# Serverless filesystem chỉ cho ghi vào /tmp, nên tắt mọi thao tác tạo thư mục
os.environ.setdefault("VERCEL_READONLY_FS", "1")

from ui.server import app  # noqa: E402

__all__ = ["app"]
