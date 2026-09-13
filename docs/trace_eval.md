# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Hoàng Quốc Việt  
> **Mã Sinh Viên / Mã Học viên:** 02563  
> **Chủ đề Lựa chọn:** Gợi ý 1.1 — Trợ lý Học vụ & Tra cứu Lịch thi VinUni (Tra cứu hồ sơ/GPA + Đặt lịch hẹn tư vấn với Cố vấn học tập)

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | TC04 đòi hỏi Agent chia nhỏ yêu cầu thành 2 bước nối tiếp: (1) tra cứu cố vấn học tập của sinh viên, (2) dùng chính tên cố vấn đó để đặt lịch hẹn — không thể trả lời trong một bước suy luận đơn lẻ. |
| **2. Tool Interaction** | 5 / 5 | Không có dữ liệu học vụ (GPA, cố vấn, lịch hẹn) nào nằm sẵn trong tri thức tĩnh của LLM — bắt buộc phải gọi `academic_query`/`schedule_appointment` qua MCP Server để lấy dữ liệu thời gian thực từ `MOCK_DATABASE`. |
| **3. Dynamic Decision** | 4 / 5 | Hành động ở bước sau (chọn `advisor_name` khi đặt lịch) phụ thuộc trực tiếp vào Observation trả về từ bước tra cứu trước, đúng tinh thần chống Hallucination của REACT_AGENT_SYSTEM_PROMPT. |
| **4. Long Horizon Goal** | 3 / 5 | Mục tiêu chỉ cần duy trì xuyên suốt trong phạm vi một phiên hỏi-đáp ngắn (vài lượt gọi Tool), chưa đòi hỏi ghi nhớ trạng thái qua nhiều ngày/phiên như một Autonomous Agent Cấp 4. |
| **TỔNG ĐIỂM AGENTIC FIT** | **16 / 20** | *Tổng điểm > 12/20 → Bài toán "Trợ lý Học vụ VinUni" rất phù hợp triển khai Agentic System (ReAct Agent + MCP) thay vì Chatbot Baseline.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.
>
> ✅ **TRẠNG THÁI NGHIỆM THU:** Đã chạy `python src/app.py --all` với **LLM API thật (Google Gemini — `gemini-2.5-flash`)**. Toàn bộ 5/5 Test Cases chạy trực tiếp trên API thật, **không có lần nào fallback về Mock Offline** (0 cảnh báo `[Gemini API Warning]`). Độ trễ trung bình mỗi bước: **~2396 ms**, đặc trưng của lời gọi mạng thật (Mock Offline chỉ ~0.5 ms).

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

### 📈 Tổng hợp Waterfall Trace toàn bộ Test Suite (10 sự kiện)

| Test Case | Loại test | Bước 1 | Bước 2 | Bước 3 | Số lượt gọi Tool |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **TC01** | `direct_query` | FINAL_ANSWER | — | — | 0 |
| **TC02** | `single_tool_query` | TOOL: `academic_query` | FINAL_ANSWER | — | 1 |
| **TC03** | `appointment_booking` | TOOL: `schedule_appointment` | FINAL_ANSWER | — | 1 |
| **TC04** | `multi_step_reasoning` | TOOL: `academic_query` | TOOL: `schedule_appointment` | FINAL_ANSWER | 2 |
| **TC05** | `edge_case_handling` | TOOL: `academic_query` → `NOT_FOUND` | FINAL_ANSWER | — | 1 |
| | | | | **TỔNG** | **5** |

**Nhận xét nghiệm thu:**
1. **TC01 chứng minh Agent biết *không* gọi Tool** khi câu hỏi thuộc kiến thức chung — tiết kiệm token, đúng nguyên tắc Agentic Fit.
2. **TC04 chứng minh vòng lặp ReAct thật sự nhiều bước:** Observation của bước 1 được nạp ngược lại vào prompt bước 2, nên Agent mới biết cố vấn là `PGS.TS Nguyễn Văn A` để điền vào tham số `advisor_name`.
3. **TC05 chứng minh khả năng chống ảo giác (Anti-Hallucination):** khi MCP Server trả về `NOT_FOUND`, Agent trả lời *"Rất tiếc, tôi không thể tìm thấy thông tin học vụ cho sinh viên có mã SV9999999..."* thay vì bịa ra một hồ sơ sinh viên giả.

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (**Google Gemini `gemini-2.5-flash`**, 0 lần fallback về Mock).
- **Tổng số Test Cases đã chạy thành công:** **5 / 5** test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** **5 lượt** — `academic_query` ×3 (TC02, TC04, TC05) và `schedule_appointment` ×2 (TC03, TC04). Cả 5 lượt đều trả về đúng `status` mong đợi (4× `SUCCESS`, 1× `NOT_FOUND`).
- **Tổng số sự kiện ghi trong `docs/trace_waterfall.json`:** 10 sự kiện (5 `TOOL_EXECUTION` + 5 `FINAL_ANSWER`).
- **Chế độ đàm thoại trực tiếp:** Đã kiểm thử thành công `python src/app.py --interactive` với truy vấn `SV2026002` → Agent gọi `academic_query` và trả về đúng hồ sơ *Trần Thị Bình (GPA 3.6, Cố vấn TS. Lê Thị B)*.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

## 4. GHI CHÚ KỸ THUẬT — NÂNG CẤP VÒNG LẶP REACT ĐA BƯỚC

Vòng lặp ReAct trong `src/app.py` được lắp ráp lại để hỗ trợ **chuỗi suy luận nhiều bước thật sự** (yêu cầu bắt buộc của TC04):

1. **Scratchpad nạp ngược Observation:** sau mỗi lần gọi Tool, kết quả Observation được nối vào `scratchpad` và đưa trở lại prompt của lượt suy luận kế tiếp. Nhờ đó LLM "nhìn thấy" dữ liệu bước trước để quyết định hành động tiếp theo, thay vì dừng lại ngay sau lời gọi Tool đầu tiên.
2. **Loop Guard chống lặp vô hạn:** mỗi lời gọi Tool được ký hiệu bằng `tool_name + arguments`; nếu LLM đề xuất lại đúng lời gọi đã thực thi, Agent dừng vòng lặp và tổng hợp kết quả từ Observation gần nhất.
3. **Chốt chặn `MAX_ITERATIONS`:** nếu hết 5 vòng lặp mà LLM vẫn chưa đưa ra câu trả lời văn bản, hàm `summarize_observation()` sẽ tổng hợp câu trả lời tiếng Việt từ Observation cuối cùng — đảm bảo mọi phiên chạy đều kết thúc bằng một sự kiện `FINAL_ANSWER` trong trace log.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
