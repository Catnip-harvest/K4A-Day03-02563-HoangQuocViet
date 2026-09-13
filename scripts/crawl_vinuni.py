"""
🕷️ CRAWLER TẠO FIXTURE WEBSITE VINUNI
Thu thập một lần nội dung công khai từ website chính thức của VinUni và lưu thành
data/vinuni_pages.json để Tool 'search_vinuni_web' chạy được hoàn toàn offline.
"""

import io
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

USER_AGENT = "K4A-Day03-lab-fixture/1.0 (student project)"
REQUEST_TIMEOUT = 20
CRAWL_DELAY_SECONDS = 1.0
MIN_CHUNK_CHARS = 400
MAX_CHUNK_CHARS = 700
MAX_CHUNKS_PER_PAGE = 200

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "vinuni_pages.json")

# Fallback dùng bản HTML đã lưu sẵn khi wifi lớp học không truy cập được trang gốc
SNAPSHOT_DIR = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Local", "Temp", "claude", "C--Users-vieth-Documents-vinuni",
    "a993b99c-6dca-472a-9724-01bbab828a70", "scratchpad"
)

PAGES = [
    {
        "topic": "academic_regulations",
        "url": "https://policy.vinuni.edu.vn/all-policies/academic-regulations-for-full-time-undergraduate-programs/",
        "snapshot": "p4_policy_regs.html"
    },
    {
        "topic": "academic_calendar",
        "url": "https://vinuni.edu.vn/vi/lich-nam-hoc/lich-hoc-nam-hoc-2024-2025/",
        "snapshot": "p9_calendar_2024_2025.html"
    },
    {
        "topic": "programs",
        "url": "https://cecs.vinuni.edu.vn/undergraduate/computer-science/",
        "snapshot": "p5_cecs_cs.html"
    },
    {
        "topic": "tuition",
        "url": "https://admissions.vinuni.edu.vn/tuition-fee/undergraduate/",
        "snapshot": "p6_tuition_ug.html"
    },
    {
        "topic": "scholarships",
        "url": "https://admissions.vinuni.edu.vn/scholarship-and-financial-aid/undergraduate-programs/scholarships/",
        "snapshot": "p7_scholarship.html"
    },
    {
        "topic": "registrar",
        "url": "https://vinuni.edu.vn/registrar/",
        "snapshot": "p10_registrar.html"
    }
]

VIETNAMESE_ONLY_CHARS = "ăâđêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ"
BLOCK_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "tr", "blockquote", "pre"]
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def fetch_html(page: dict) -> tuple:
    """Tải HTML trực tiếp từ web, nếu lỗi thì dùng bản snapshot đã lưu"""
    try:
        response = requests.get(
            page["url"],
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        return response.text, f"LIVE {response.status_code}"
    except Exception as exc:
        snapshot_path = os.path.join(SNAPSHOT_DIR, page["snapshot"])
        if os.path.exists(snapshot_path):
            with open(snapshot_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(), f"SNAPSHOT ({type(exc).__name__})"
        raise


def extract_main(soup: BeautifulSoup):
    """Lấy vùng nội dung chính, loại bỏ menu/header/footer/script"""
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "form", "iframe"]):
        tag.decompose()
    for selector in ["article", ".entry-content", "main"]:
        node = soup.select_one(selector)
        if node and len(node.get_text(" ", strip=True)) > 200:
            return node
    return soup.body or soup


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def guess_lang(text: str) -> str:
    sample = text[:4000].lower()
    hits = sum(1 for ch in sample if ch in VIETNAMESE_ONLY_CHARS)
    return "vi" if hits > len(sample) * 0.01 else "en"


def split_long_unit(text: str) -> list:
    """Cắt một đoạn quá dài thành các mảnh ~MAX_CHUNK_CHARS tại ranh giới câu/khoảng trắng"""
    pieces = []
    buffer = ""
    for sentence in re.split(r"(?<=[.;:!?])\s+", text):
        while len(sentence) > MAX_CHUNK_CHARS:
            cut = sentence.rfind(" ", 0, MAX_CHUNK_CHARS) or MAX_CHUNK_CHARS
            pieces.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if len(buffer) + len(sentence) + 1 > MAX_CHUNK_CHARS and buffer:
            pieces.append(buffer.strip())
            buffer = sentence
        else:
            buffer = f"{buffer} {sentence}".strip()
    if buffer:
        pieces.append(buffer.strip())
    return [p for p in pieces if p]


def build_chunks(node, page_index: int) -> list:
    """Gom các khối văn bản thành chunk 400-700 ký tự, giữ heading gần nhất"""
    chunks = []
    heading = ""
    buffer = ""
    buffer_heading = ""

    def flush():
        nonlocal buffer, buffer_heading
        text = normalise(buffer)
        if len(text) >= 40:
            chunks.append({
                "id": f"p{page_index}c{len(chunks) + 1}",
                "heading": buffer_heading,
                "text": text
            })
        buffer = ""

    for element in node.find_all(BLOCK_TAGS):
        if element.find_parent(["li", "tr"]) is not None and element.name not in HEADING_TAGS:
            continue
        text = normalise(element.get_text(" | " if element.name == "tr" else " ", strip=True))
        if not text:
            continue

        if element.name in HEADING_TAGS:
            flush()
            heading = text
            buffer_heading = heading
            continue

        if not buffer:
            buffer_heading = heading

        if len(text) > MAX_CHUNK_CHARS:
            flush()
            for piece in split_long_unit(text):
                buffer_heading = heading
                buffer = piece
                flush()
            continue

        if len(buffer) + len(text) + 1 > MAX_CHUNK_CHARS and len(buffer) >= MIN_CHUNK_CHARS:
            flush()
            buffer_heading = heading
        buffer = f"{buffer} {text}".strip()

        if len(buffer) >= MAX_CHUNK_CHARS:
            flush()
            buffer_heading = heading

    flush()
    return chunks[:MAX_CHUNKS_PER_PAGE]


def crawl() -> dict:
    pages = []
    for index, page in enumerate(PAGES, start=1):
        html, status = fetch_html(page)
        soup = BeautifulSoup(html, "html.parser")
        title = normalise(soup.title.get_text()) if soup.title else page["topic"]
        node = extract_main(soup)
        full_text = normalise(node.get_text(" ", strip=True))
        chunks = build_chunks(node, index)

        pages.append({
            "topic": page["topic"],
            "url": page["url"],
            "title": title,
            "lang": guess_lang(full_text),
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "chunks": chunks
        })
        print(f"[{status}] {page['topic']:22s} | {title[:52]:52s} | {len(chunks):3d} chunks | {len(full_text) / 1024:6.1f} KB")

        if index < len(PAGES):
            time.sleep(CRAWL_DELAY_SECONDS)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pages": pages
    }


if __name__ == "__main__":
    print("==========================================================")
    print("🕷️ CRAWL WEBSITE VINUNI → data/vinuni_pages.json")
    print("==========================================================")
    fixture = crawl()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    total_chunks = sum(len(p["chunks"]) for p in fixture["pages"])
    print(f"\n✅ Đã ghi {len(fixture['pages'])} trang / {total_chunks} chunks vào '{OUTPUT_PATH}' ({size_kb:.1f} KB).")
