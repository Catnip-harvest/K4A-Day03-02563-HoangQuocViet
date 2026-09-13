"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
import os
import re
import unicodedata
from collections import Counter
from typing import Dict, Any, List

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Đã được định nghĩa mẫu sẵn cho Học viên tham khảo
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },
    
    # --------------------------------------------------------------------------
    # TODO 1.2: HỌC VIÊN HOÀN THIỆN TOOL SCHEMA CHO 'schedule_appointment'
    # 🎯 YÊU CẦU THIẾT KẾ SCHEMA (JSON SCHEMA STANDARD):
    # 1. Tool dùng để đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.
    # 2. Thiết kế các tham số (properties) để LLM trích xuất:
    #    - student_id (string): Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')
    #    - datetime_str (string): Thời gian hẹn (ví dụ: '14:00 15/09/2026')
    #    - advisor_name (string): Tên cố vấn học tập
    # 3. Khai báo danh sách các trường bắt buộc (required).
    # --------------------------------------------------------------------------
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn tư vấn, định dạng 'HH:MM DD/MM/YYYY' (ví dụ: '14:00 15/09/2026')"
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên cố vấn học tập mà sinh viên muốn đặt lịch hẹn (ví dụ: 'PGS.TS Nguyễn Văn A')"
                }
            },
            "required": ["student_id", "datetime_str", "advisor_name"]
        }
    },

    # Tool 3: Tra cứu website công khai của VinUni (fixture crawl sẵn, chạy offline)
    {
        "name": "search_vinuni_web",
        "description": (
            "Tra cứu thông tin công khai trên website chính thức của VinUni: quy chế học vụ, "
            "điều kiện tốt nghiệp/GPA, cảnh báo học vụ, lịch năm học, chương trình đào tạo, "
            "học phí, học bổng, phòng đào tạo (Registrar). "
            "Dữ liệu website có cả tiếng Anh và tiếng Việt nên tham số 'query' NÊN chứa từ khóa ở cả hai "
            "ngôn ngữ (ví dụ: 'GPA tốt nghiệp graduation GPA requirement')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Câu hỏi hoặc từ khóa cần tra cứu, nên gồm cả tiếng Việt lẫn tiếng Anh (ví dụ: 'GPA tối thiểu tốt nghiệp minimum cumulative GPA graduation')"
                },
                "topic": {
                    "type": "string",
                    "description": "Giới hạn phạm vi tìm kiếm theo nhóm trang của website VinUni. Mặc định 'any' là tìm trên tất cả các trang.",
                    "enum": [
                        "academic_regulations",
                        "academic_calendar",
                        "programs",
                        "tuition",
                        "scholarships",
                        "registrar",
                        "any"
                    ],
                    "default": "any"
                }
            },
            "required": ["query"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    }
}


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str = "PGS.TS Nguyễn Văn A") -> str:
    """Thực thi đặt lịch hẹn tư vấn học vụ"""
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": f"BK-{student_id}-99",
        "student_id": student_id,
        "datetime": datetime_str,
        "advisor": advisor_name,
        "message": f"Đặt lịch thành công cho sinh viên {student_id} với {advisor_name} vào lúc {datetime_str}."
    }, ensure_ascii=False)


# ==============================================================================
# 3. TRA CỨU WEBSITE VINUNI TỪ FIXTURE ĐÃ CRAWL SẴN (OFFLINE)
# ==============================================================================

VINUNI_FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "vinuni_pages.json"
)

SNIPPET_MAX_CHARS = 600
TOP_RESULTS = 3
HEADING_WEIGHT = 3.0
EXACT_MATCH_SCORE = 1.0
STRIPPED_MATCH_SCORE = 0.6
# Từ khóa dịch chéo mang ý định chính của câu hỏi nên được ưu tiên hơn từ gốc
SYNONYM_WEIGHT = 1.5
# Tiếng Việt chủ yếu là từ ghép 2 âm tiết ('tốt nghiệp', 'đào tạo') nên cụm 2 từ đáng tin hơn từ đơn
BIGRAM_WEIGHT = 2.5
SYLLABLE_WEIGHT = 0.4

# Website VinUni song ngữ: mở rộng từ khóa tiếng Việt sang thuật ngữ tiếng Anh tương ứng
BILINGUAL_SYNONYMS = {
    "gpa": ["gpa"],
    "tot nghiep": ["graduation", "graduate"],
    "hoc phi": ["tuition", "fee", "fees"],
    "hoc bong": ["scholarship", "scholarships", "financial", "aid"],
    "lich": ["calendar", "schedule"],
    "tin chi": ["credit", "credits"],
    "canh bao hoc vu": ["academic", "probation", "warning"],
    "hoc ky": ["semester", "term"],
    "ky": ["semester", "term"],
    "diem": ["grade", "score"],
    "nghi hoc": ["withdrawal", "dismissal"],
    "thoi hoc": ["withdrawal", "dismissal"],
    "dang ky": ["registration", "enrollment"],
    "phong dao tao": ["registrar"],
    "quy che": ["regulations", "policy"],
    "chuong trinh dao tao": ["program", "curriculum"]
}

SEARCH_STOPWORDS = {
    "la", "cua", "va", "cho", "cac", "mot", "co", "the", "voi", "theo", "ve", "duoc",
    "bao", "nhieu", "de", "can", "khi", "nay", "do", "toi", "ban", "em", "thi", "hay",
    "sinh", "vien", "vinuni", "vinuniversity", "truong", "hoi", "xin", "vui", "long",
    "a", "an", "the", "of", "for", "to", "is", "are", "in", "on", "at", "and", "or",
    "what", "how", "much", "many", "do", "does", "i", "my", "me", "you", "student",
    "students", "university"
}

_fixture_cache = None


def _strip_diacritics(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[0-9a-zà-ỹ]+", text.lower())


def _bigrams(text: str) -> set:
    tokens = _tokenize(_strip_diacritics(text))
    return {f"{first} {second}" for first, second in zip(tokens, tokens[1:])}


def _load_fixture():
    """Nạp fixture website VinUni một lần rồi cache lại ở cấp module"""
    global _fixture_cache
    if _fixture_cache is not None:
        return _fixture_cache
    if not os.path.exists(VINUNI_FIXTURE_PATH):
        return None

    with open(VINUNI_FIXTURE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    index = []
    for page in data.get("pages", []):
        for chunk in page.get("chunks", []):
            index.append({
                "topic": page.get("topic", ""),
                "url": page.get("url", ""),
                "title": page.get("title", ""),
                "heading": chunk.get("heading", ""),
                "text": chunk.get("text", ""),
                "heading_tokens": Counter(_tokenize(chunk.get("heading", ""))),
                "heading_ascii": Counter(_tokenize(_strip_diacritics(chunk.get("heading", "")))),
                "text_tokens": Counter(_tokenize(chunk.get("text", ""))),
                "text_ascii": Counter(_tokenize(_strip_diacritics(chunk.get("text", "")))),
                "heading_bigrams": _bigrams(chunk.get("heading", "")),
                "text_bigrams": _bigrams(chunk.get("text", ""))
            })

    _fixture_cache = {"generated_at": data.get("generated_at", ""), "chunks": index}
    return _fixture_cache


def _query_tokens(query: str) -> List[tuple]:
    """Sinh bộ (token gốc, token đã bỏ dấu, trọng số) kèm mở rộng thuật ngữ song ngữ"""
    ascii_query = _strip_diacritics(query.lower())
    tokens = []
    for token in _tokenize(query):
        ascii_token = _strip_diacritics(token)
        if ascii_token in SEARCH_STOPWORDS or len(ascii_token) < 2:
            continue
        # Âm tiết tiếng Việt đứng một mình ít mang nghĩa, nghĩa nằm ở cụm 2 âm tiết
        tokens.append((token, ascii_token, SYLLABLE_WEIGHT if token != ascii_token else 1.0))

    for phrase, expansions in BILINGUAL_SYNONYMS.items():
        if re.search(rf"\b{re.escape(phrase)}\b", ascii_query):
            tokens.extend((word, word, SYNONYM_WEIGHT) for word in expansions)

    best = {}
    for token, ascii_token, weight in tokens:
        if weight >= best.get(ascii_token, (None, 0.0))[1]:
            best[ascii_token] = (token, weight)
    return [(token, ascii_token, weight) for ascii_token, (token, weight) in best.items()]


def _field_score(exact_counter: Counter, ascii_counter: Counter, token: str, ascii_token: str) -> float:
    if exact_counter.get(token, 0):
        return EXACT_MATCH_SCORE
    if ascii_counter.get(ascii_token, 0):
        return STRIPPED_MATCH_SCORE
    return 0.0


def execute_search_vinuni_web(query: str, topic: str = "any") -> str:
    """Tra cứu nội dung website VinUni đã crawl sẵn bằng cách chấm điểm từ khóa"""
    fixture = _load_fixture()
    if fixture is None:
        return json.dumps({
            "status": "FIXTURE_MISSING",
            "message": "Chưa có dữ liệu website VinUni (data/vinuni_pages.json). Hãy chạy scripts/crawl_vinuni.py để tạo fixture."
        }, ensure_ascii=False)

    topic = (topic or "any").strip().lower()
    tokens = _query_tokens(query)
    query_bigrams = _bigrams(query)
    if not tokens and not query_bigrams:
        return json.dumps({
            "status": "NO_MATCH",
            "message": f"Không tìm thấy nội dung phù hợp trên website VinUni cho '{query}'."
        }, ensure_ascii=False)

    scored = []
    for chunk in fixture["chunks"]:
        if topic != "any" and chunk["topic"] != topic:
            continue
        score = 0.0
        for token, ascii_token, weight in tokens:
            heading_score = _field_score(chunk["heading_tokens"], chunk["heading_ascii"], token, ascii_token)
            text_score = _field_score(chunk["text_tokens"], chunk["text_ascii"], token, ascii_token)
            score += weight * (HEADING_WEIGHT * heading_score + text_score)
        for bigram in query_bigrams:
            in_heading = bigram in chunk["heading_bigrams"]
            in_text = bigram in chunk["text_bigrams"]
            score += BIGRAM_WEIGHT * (HEADING_WEIGHT * in_heading + in_text)
        if score > 0:
            scored.append((score, chunk))

    if not scored:
        return json.dumps({
            "status": "NO_MATCH",
            "message": f"Không tìm thấy nội dung phù hợp trên website VinUni cho '{query}'."
        }, ensure_ascii=False)

    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for rank, (score, chunk) in enumerate(scored[:TOP_RESULTS], start=1):
        snippet = chunk["text"]
        if len(snippet) > SNIPPET_MAX_CHARS:
            snippet = snippet[:SNIPPET_MAX_CHARS].rsplit(" ", 1)[0] + "..."
        results.append({
            "rank": rank,
            "title": chunk["title"],
            "url": chunk["url"],
            "heading": chunk["heading"],
            "snippet": snippet,
            "score": round(score, 2)
        })

    return json.dumps({
        "status": "SUCCESS",
        "query": query,
        "topic": topic,
        "results": results,
        "source": f"data/vinuni_pages.json (crawled {fixture['generated_at']})"
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "search_vinuni_web": execute_search_vinuni_web
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
