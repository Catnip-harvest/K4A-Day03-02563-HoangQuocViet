# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Hoàng Quốc Việt  
> **Mã Sinh Viên / Mã Học viên:** 02563  
> **Chủ đề Lựa chọn:** Gợi ý 1.1 — Trợ lý Học vụ & Tra cứu Lịch thi VinUni (Tra cứu hồ sơ/GPA + Đặt lịch hẹn tư vấn với Cố vấn học tập)

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | TC04 và TC07 đòi hỏi Agent chia nhỏ yêu cầu thành 2 bước nối tiếp: (1) tra cứu cố vấn học tập của sinh viên, (2) dùng chính tên cố vấn đó để đặt lịch hẹn — không thể trả lời trong một bước suy luận đơn lẻ. |
| **2. Tool Interaction** | 5 / 5 | Không có dữ liệu học vụ (GPA, cố vấn, lịch hẹn) nào nằm sẵn trong tri thức tĩnh của LLM — bắt buộc phải gọi `academic_query`/`schedule_appointment` qua MCP Server để lấy dữ liệu thời gian thực từ `MOCK_DATABASE`. Tool thứ 3 `search_vinuni_web` còn tra cứu website chính thức VinUni (fixture crawl sẵn). |
| **3. Dynamic Decision** | 4 / 5 | Hành động ở bước sau (chọn `advisor_name` khi đặt lịch) phụ thuộc trực tiếp vào Observation trả về từ bước tra cứu trước, đúng tinh thần chống Hallucination của REACT_AGENT_SYSTEM_PROMPT. |
| **4. Long Horizon Goal** | 3 / 5 | Mục tiêu chỉ cần duy trì xuyên suốt trong phạm vi một phiên hỏi-đáp ngắn (vài lượt gọi Tool), chưa đòi hỏi ghi nhớ trạng thái qua nhiều ngày/phiên như một Autonomous Agent Cấp 4. |
| **TỔNG ĐIỂM AGENTIC FIT** | **16 / 20** | *Tổng điểm > 12/20 → Bài toán "Trợ lý Học vụ VinUni" rất phù hợp triển khai Agentic System (ReAct Agent + MCP) thay vì Chatbot Baseline.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.
>
> ✅ **TRẠNG THÁI NGHIỆM THU:** Đã chạy `python src/app.py --all` với **LLM API thật (Google Gemini: `gemini-3.1-flash-lite`)**. Toàn bộ 7/7 Test Cases chạy trực tiếp trên API thật, **không có lần nào fallback về Mock Offline** (0 cảnh báo `[Gemini API Warning]`). Độ trễ trung bình mỗi bước: **~1928 ms**, đặc trưng của lời gọi mạng thật (Mock Offline chỉ ~0.5 ms).

Dưới đây là đoạn trích xuất **TC04 (multi_step_reasoning)** từ `docs/trace_waterfall.json` — minh chứng rõ nhất cho chuỗi ReAct nhiều bước: Agent **tra cứu cố vấn trước**, lấy đúng tên `PGS.TS Nguyễn Văn A` từ Observation, rồi **dùng chính tên đó** để đặt lịch ở bước sau (không hề bịa tên cố vấn):

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu cố vấn học tập của sinh viên SV2026001 rồi đặt lịch hẹn tư vấn với đúng cố vấn đó vào lúc 14:00 ngày 15/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
      }
    },
    "latency_ms": 944.59
  },
  {
    "step": 2,
    "query": "Hãy tra cứu cố vấn học tập của sinh viên SV2026001 rồi đặt lịch hẹn tư vấn với đúng cố vấn đó vào lúc 14:00 ngày 15/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "schedule_appointment",
    "arguments": {
      "student_id": "SV2026001",
      "datetime_str": "14:00 15/09/2026",
      "advisor_name": "PGS.TS Nguyễn Văn A"
    },
    "observation": {
      "status": "SUCCESS",
      "booking_id": "BK-SV2026001-99",
      "student_id": "SV2026001",
      "datetime": "14:00 15/09/2026",
      "advisor": "PGS.TS Nguyễn Văn A",
      "message": "Đặt lịch thành công cho sinh viên SV2026001 với PGS.TS Nguyễn Văn A vào lúc 14:00 15/09/2026."
    },
    "latency_ms": 2151.54
  },
  {
    "step": 3,
    "query": "Hãy tra cứu cố vấn học tập của sinh viên SV2026001 rồi đặt lịch hẹn tư vấn với đúng cố vấn đó vào lúc 14:00 ngày 15/09/2026.",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Chào bạn, tôi đã hoàn tất yêu cầu của bạn.\n\nDưới đây là thông tin chi tiết:\n- **Cố vấn học tập của bạn:** PGS.TS Nguyễn Văn A.\n- **Trạng thái đặt lịch:** Đã đặt lịch thành công.\n- **Mã đặt lịch:** BK-SV2026001-99.\n- **Thời gian hẹn:** 14:00 ngày 15/09/2026.\n\nChúc bạn có buổi tư vấn học tập hiệu quả!",
    "latency_ms": 3267.28
  }
]
```

Đoạn trích xuất tiếp theo là **TC07 (multi_tool_reasoning)** minh họa năng lực phối hợp đa công cụ: Agent tra cứu GPA của SV2026002 bằng `academic_query` rồi đối chiếu quy chế trên website bằng `search_vinuni_web`, sau đó đưa ra câu trả lời có trích dẫn URL nguồn chính thức:

*(Trích lược: chỉ giữ kết quả #1 và rút gọn snippet cho dễ đọc; bản đầy đủ nằm trong docs/trace_waterfall.json)*
```json
[
  {
    "step": 1,
    "query": "Tra cứu GPA của sinh viên SV2026002, rồi đối chiếu với quy chế học vụ trên website VinUni để cho biết em ấy có đủ điều kiện GPA tốt nghiệp không.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026002"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026002",
      "data": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.6,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
      }
    },
    "latency_ms": 1737.79
  },
  {
    "step": 2,
    "query": "Tra cứu GPA của sinh viên SV2026002, rồi đối chiếu với quy chế học vụ trên website VinUni để cho biết em ấy có đủ điều kiện GPA tốt nghiệp không.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_vinuni_web",
    "arguments": {
      "query": "GPA tối thiểu tốt nghiệp minimum cumulative GPA graduation requirement",
      "topic": "academic_regulations"
    },
    "observation": {
      "status": "SUCCESS",
      "query": "GPA tối thiểu tốt nghiệp minimum cumulative GPA graduation requirement",
      "topic": "academic_regulations",
      "results": [
        {
          "rank": 1,
          "title": "Academic Regulations for Full-Time Undergraduate Programs - VinUni Policy",
          "url": "https://policy.vinuni.edu.vn/all-policies/academic-regulations-for-full-time-undergraduate-programs/",
          "heading": "Article 28. Recognition of Graduation",
          "snippet": "Complete the minimum credits requirement within the period of candidature for each program; Complete General Education/VinCore and English proficiency requirements; Complete the requirements for the major, defined by each College; Resolve any “I – Incomplete” grade for required courses from the reco…",
          "score": 13.0
        }
      ],
      "source": "data/vinuni_pages.json (crawled 2026-09-13T03:48:30+00:00)"
    },
    "latency_ms": 1747.64
  },
  {
    "step": 3,
    "query": "Tra cứu GPA của sinh viên SV2026002, rồi đối chiếu với quy chế học vụ trên website VinUni để cho biết em ấy có đủ điều kiện GPA tốt nghiệp không.",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Dựa trên kết quả tra cứu, tôi xin thông tin đến bạn về tình trạng học vụ của sinh viên Trần Thị Bình (SV2026002) như sau:\n\n1.  **GPA hiện tại:** Sinh viên Trần Thị Bình hiện có điểm trung bình tích lũy (Cumulative GPA) là **3.6/4.0**.\n2.  **Quy định về GPA tốt nghiệp:** Theo Điều 28 (Article 28) trong Quy chế học vụ dành cho chương trình đại học chính quy của VinUni, sinh viên cần đạt mức GPA tích lũy tối thiểu là **2.00/4.00** để đủ điều kiện tốt nghiệp.\n3.  **Kết luận:** Với GPA hiện tại là 3.6, sinh viên Trần Thị Bình **đã đáp ứng được yêu cầu về GPA** để xét tốt nghiệp theo quy định của nhà trường.\n\n*Lưu ý: Ngoài điều kiện về GPA, sinh viên cần hoàn thành các yêu cầu khác như số tín chỉ tối thiểu, các học phần bắt buộc (VinCore), yêu cầu về tiếng Anh và các quy định khác của chương trình đào tạo.*\n\nBạn có thể tham khảo chi tiết quy chế tại đây: [Academic Regulations for Full-Time Undergraduate Programs](https://policy.vinuni.edu.vn/all-policies/academic-regulations-for-full-time-undergraduate-programs/)",
    "latency_ms": 1986.94
  }
]
```

### 📈 Tổng hợp Waterfall Trace toàn bộ Test Suite (15 sự kiện)

| Test Case | Loại test | Bước 1 | Bước 2 | Bước 3 | Số lượt gọi Tool |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **TC01** | `direct_query` | FINAL_ANSWER | — | — | 0 |
| **TC02** | `single_tool_query` | TOOL: `academic_query` | FINAL_ANSWER | — | 1 |
| **TC03** | `appointment_booking` | TOOL: `schedule_appointment` | FINAL_ANSWER | — | 1 |
| **TC04** | `multi_step_reasoning` | TOOL: `academic_query` | TOOL: `schedule_appointment` | FINAL_ANSWER | 2 |
| **TC05** | `edge_case_handling` | TOOL: `academic_query` → `NOT_FOUND` | FINAL_ANSWER | — | 1 |
| **TC06** | `web_lookup` | TOOL: `search_vinuni_web` | FINAL_ANSWER | - | 1 |
| **TC07** | `multi_tool_reasoning` | TOOL: `academic_query` | TOOL: `search_vinuni_web` | FINAL_ANSWER | 2 |
| | | | | **TỔNG** | **8** |

**Nhận xét nghiệm thu:**
1. **TC01 chứng minh Agent biết *không* gọi Tool** khi câu hỏi thuộc kiến thức chung — tiết kiệm token, đúng nguyên tắc Agentic Fit.
2. **TC04 chứng minh vòng lặp ReAct thật sự nhiều bước:** Observation của bước 1 được nạp ngược lại vào prompt bước 2, nên Agent mới biết cố vấn là `PGS.TS Nguyễn Văn A` để điền vào tham số `advisor_name`.
3. **TC05 chứng minh khả năng chống ảo giác (Anti-Hallucination):** khi MCP Server trả về `NOT_FOUND`, Agent trả lời *"Rất tiếc, tôi không thể tìm thấy thông tin học vụ cho sinh viên có mã SV9999999..."* thay vì bịa ra một hồ sơ sinh viên giả.
4. **TC06 làm nổi bật sự khác biệt giữa Chatbot Cấp 2 và Agent Cấp 3:** Chatbot thuần túy không có công cụ sẽ không thể biết quy chế điểm GPA tốt nghiệp hoặc dễ bị ảo giác; trong khi đó, Agent tự động gọi công cụ tra cứu quy chế học vụ, trích dẫn chính xác câu văn quy định mức GPA tối thiểu 2.00/4.00 kèm theo URL nguồn chính thức.
5. **TC07 chứng minh khả năng kết hợp nhiều công cụ khác nhau trong cùng một chuỗi suy luận:** Agent tích hợp cả dữ liệu nội bộ (`academic_query`) và dữ liệu tra cứu website (`search_vinuni_web`), với từng bước thực thi và quan sát đều được thể hiện minh bạch trong trace log.

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (**Google Gemini `gemini-3.1-flash-lite`**, 0 lần fallback về Mock).
- **Tổng số Test Cases đã chạy thành công:** **7 / 7** test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** **8 lượt**: `academic_query` ×4 (TC02, TC04, TC05, TC07), `schedule_appointment` ×2 (TC03, TC04) và `search_vinuni_web` ×2 (TC06, TC07). Cả 8 lượt đều trả về đúng `status` mong đợi (7× `SUCCESS`, 1× `NOT_FOUND` ở TC05).
- **Tổng số sự kiện ghi trong `docs/trace_waterfall.json`:** 15 sự kiện (8 `TOOL_EXECUTION` + 7 `FINAL_ANSWER`).
- **Chế độ đàm thoại trực tiếp:** Đã kiểm thử thành công `python src/app.py --interactive` với truy vấn `SV2026002` → Agent gọi `academic_query` và trả về đúng hồ sơ *Trần Thị Bình (GPA 3.6, Cố vấn TS. Lê Thị B)*.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

## 4. GHI CHÚ KỸ THUẬT — NÂNG CẤP VÒNG LẶP REACT ĐA BƯỚC

Vòng lặp ReAct trong `src/app.py` được lắp ráp lại để hỗ trợ **chuỗi suy luận nhiều bước thật sự** (yêu cầu bắt buộc của TC04):

1. **Scratchpad nạp ngược Observation:** sau mỗi lần gọi Tool, kết quả Observation được nối vào `scratchpad` và đưa trở lại prompt của lượt suy luận kế tiếp. Nhờ đó LLM "nhìn thấy" dữ liệu bước trước để quyết định hành động tiếp theo, thay vì dừng lại ngay sau lời gọi Tool đầu tiên.
2. **Loop Guard chống lặp vô hạn:** mỗi lời gọi Tool được ký hiệu bằng `tool_name + arguments`; nếu LLM đề xuất lại đúng lời gọi đã thực thi, Agent dừng vòng lặp và tổng hợp kết quả từ Observation gần nhất.
3. **Chốt chặn `MAX_ITERATIONS`:** nếu hết 5 vòng lặp mà LLM vẫn chưa đưa ra câu trả lời văn bản, hàm `summarize_observation()` sẽ tổng hợp câu trả lời tiếng Việt từ Observation cuối cùng — đảm bảo mọi phiên chạy đều kết thúc bằng một sự kiện `FINAL_ANSWER` trong trace log.
4. **Công cụ tra cứu website `search_vinuni_web` và fixture ngoại tuyến:** Máy chủ MCP hiện cung cấp 3 công cụ gồm `academic_query`, `schedule_appointment` và `search_vinuni_web`. Công cụ `search_vinuni_web` đọc dữ liệu từ `data/vinuni_pages.json`, tệp fixture được thu thập một lần bởi `scripts/crawl_vinuni.py` từ 6 trang công khai của VinUni (quy chế học vụ policy.vinuni.edu.vn, lịch năm học 2024-2025, chương trình Khoa học Máy tính CECS, học phí, học bổng và phòng đào tạo), tất cả đều tuân thủ và được cho phép bởi robots.txt. Hệ thống xếp hạng các đoạn văn bản theo phương pháp từ vựng kết hợp mở rộng từ đồng nghĩa tiếng Việt/tiếng Anh và đối sánh không dấu, cho phép bản demo vận hành hoàn toàn offline.
5. **Giao diện Demo trực quan (Demo UI):** Ứng dụng cung cấp giao diện web gồm `ui/server.py` xây dựng trên FastAPI (truyền phát từng bước suy luận ReAct qua Server-Sent Events tại `POST /api/agent` và chatbot cơ sở tại `POST /api/chatbot`) cùng thư mục `ui/static` chứa một trang HTML duy nhất, không cần bước biên dịch phức tạp. Để khởi chạy giao diện thử nghiệm, người dùng chỉ cần thực thi lệnh `python ui/server.py` và truy cập địa chỉ `http://127.0.0.1:8000` trên trình duyệt.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
