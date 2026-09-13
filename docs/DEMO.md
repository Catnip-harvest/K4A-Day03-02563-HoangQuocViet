# Kịch bản Thuyết trình Demo: Trợ lý Học vụ VinUni (Chatbot vs ReAct Agent MCP)

## Chuẩn bị trước buổi demo

Checklist chuẩn bị trước khi bắt đầu bài thuyết trình (5-7 phút):
- Khởi động server trước giờ demo 5 phút: Mở terminal tại thư mục gốc của dự án, kích hoạt môi trường ảo (.venv\Scripts\Activate.ps1 trên Windows) và thực thi lệnh `python ui/server.py`.
- Mở trình duyệt web: Truy cập địa chỉ http://127.0.0.1:8000.
- Kiểm tra thanh trạng thái hệ thống: Đảm bảo Health Chip hiển thị màu xanh lá cây, xác nhận kết nối thành công với Provider Google Gemini (mô hình gemini-3.1-flash-lite) và MCP Server (vinuni-academic-mcp-server).
- Chuẩn bị sẵn nội dung câu hỏi trong bộ nhớ tạm (clipboard):
  + Câu hỏi chính 1 (TC06): "Theo quy chế học vụ VinUni, sinh viên cần GPA tích lũy tối thiểu bao nhiêu để tốt nghiệp?"
  + Câu hỏi chính 2 (TC07): "Tra cứu GPA của sinh viên SV2026002, rồi đối chiếu với quy chế học vụ trên website VinUni để cho biết em ấy có đủ điều kiện GPA tốt nghiệp không."
  + Câu hỏi dự phòng (TC04): "Hãy tra cứu cố vấn học tập của sinh viên SV2026001 rồi đặt lịch hẹn tư vấn với đúng cố vấn đó vào lúc 14:00 ngày 15/09/2026."
- Phương án dự phòng sự cố mạng: Giao diện web và fixture dữ liệu hoạt động hoàn toàn offline, tuy nhiên cuộc gọi LLM API cần kết nối Internet. Trong trường hợp wifi phòng học gặp sự cố, chuyển sang trình chiếu trực tiếp tệp nhật ký `docs/trace_waterfall.json` đã lưu từ phiên chạy thật gần nhất để giải thích chi tiết chuỗi suy luận từng bước.

## 1. Chọn đề tài gì? Tại sao chọn đề tài đó?

- Đề tài lựa chọn: Gợi ý 1.1: Trợ lý Học vụ VinUni. Hệ thống hỗ trợ sinh viên tra cứu hồ sơ và điểm GPA cá nhân, đặt lịch hẹn tư vấn với Cố vấn học tập, đồng thời tra cứu các thông tin quy chế học vụ, lịch năm học, học phí, học bổng trên website chính thức của VinUni.
- Lý do lựa chọn đề tài:
  + Dữ liệu học vụ mang tính nội bộ và biến động: Thông tin hồ sơ sinh viên, điểm số và tên cố vấn không nằm trong dữ liệu huấn luyện tĩnh của LLM. Để trả lời chính xác, hệ thống bắt buộc phải sử dụng công cụ để truy vấn cơ sở dữ liệu thời gian thực.
  + Yêu cầu xử lý chuỗi hành động nối tiếp: Nhiều nghiệp vụ không thể giải quyết trong một bước đơn lẻ mà đòi hỏi chuỗi 2 bước phụ thuộc dữ liệu của nhau, ví dụ tra cứu cố vấn học tập trước rồi mới dùng tên cố vấn đó để đặt lịch hẹn.
  + Chống ảo giác (Anti-Hallucination) bằng dữ liệu quy chế chính thức: Khi giải đáp quy chế học vụ hay điều kiện tốt nghiệp, hệ thống bắt buộc phải đối chiếu văn bản quy định từ website VinUni và trích dẫn nguồn URL rõ ràng, không để LLM tự phỏng đoán gây hiểu lầm cho người học.
- Định vị hệ thống qua 4 cấp độ AI:
  + Cấp 1 (Rule-based): Hệ thống dựa trên luật tĩnh (if-else), cứng nhắc và không thể hiểu ngữ cảnh câu hỏi tự nhiên.
  + Cấp 2 (LLM Chatbot): Mô hình ngôn ngữ hội thoại thông thường nhưng không có công cụ tra cứu, dễ sinh ảo giác hoặc từ chối khi gặp dữ liệu riêng biệt.
  + Cấp 3 (ReAct Agent): Trọng tâm của bài lab này, tác tử kết hợp suy luận (Thought) và hành động (Action) thông qua công cụ và giao thức MCP để thu thập dữ liệu quan sát (Observation).
  + Cấp 4 (Autonomous Agent): Tác tử tự chủ hoàn toàn với khả năng tự lập kế hoạch dài hạn (planning), bộ nhớ dài hạn qua nhiều phiên (memory) và tự phản tư (reflection), nằm ngoài phạm vi bài lab.

## 2. Tại sao ReAct Agent Pattern phù hợp? (4 tiêu chí Agentic Fit, thang điểm 5)

Tổng điểm Agentic Fit của bài toán đạt 16 / 20 điểm. Mức điểm này vượt xa ngưỡng 12 / 20, chứng minh bài toán Trợ lý Học vụ VinUni hoàn toàn phù hợp để triển khai theo kiến trúc ReAct Agent kết hợp MCP thay vì dùng Chatbot thông thường.

Bảng đánh giá 4 tiêu chí Agentic Fit:

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| 1. Multi-step Reasoning | 4 / 5 | TC04 và TC07 đòi hỏi Agent chia nhỏ yêu cầu thành 2 bước nối tiếp: (1) tra cứu cố vấn học tập của sinh viên, (2) dùng chính tên cố vấn đó để đặt lịch hẹn - không thể trả lời trong một bước suy luận đơn lẻ. |
| 2. Tool Interaction | 5 / 5 | Không có dữ liệu học vụ (GPA, cố vấn, lịch hẹn) nào nằm sẵn trong tri thức tĩnh của LLM - bắt buộc phải gọi academic_query / schedule_appointment qua MCP Server để lấy dữ liệu thời gian thực từ MOCK_DATABASE. Tool thứ 3 search_vinuni_web còn tra cứu website chính thức VinUni (fixture crawl sẵn). |
| 3. Dynamic Decision | 4 / 5 | Hành động ở bước sau (chọn advisor_name khi đặt lịch) phụ thuộc trực tiếp vào Observation trả về từ bước tra cứu trước, đúng tinh thần chống Hallucination của REACT_AGENT_SYSTEM_PROMPT. |
| 4. Long Horizon Goal | 3 / 5 | Mục tiêu chỉ cần duy trì xuyên suốt trong phạm vi một phiên hỏi-đáp ngắn (vài lượt gọi Tool), chưa đòi hỏi ghi nhớ trạng thái qua nhiều ngày/phiên như một Autonomous Agent Cấp 4. |
| TỔNG ĐIỂM AGENTIC FIT | 16 / 20 | Tổng điểm > 12/20 xác nhận bài toán Trợ lý Học vụ VinUni rất phù hợp triển khai Agentic System (ReAct Agent + MCP) thay vì Chatbot Baseline. |

## 3. Kiến trúc Agent đã xây dựng (biểu đồ)

```mermaid
graph TD
    User["Nguoi dung (Trinh duyet Web)"] -->|Giao dien HTML/JS khong build step| UI["Frontend (ui/static/index.html)"]
    UI -->|POST /api/chatbot (Baseline Cap 2)| Server["FastAPI Server (ui/server.py)"]
    UI -->|POST /api/agent (SSE Stream Cap 3)| Server
    Server --> Core["Vong lap ReAct (src/app.py)<br/>Google Gemini (gemini-3.1-flash-lite)<br/>Scratchpad + Loop Guard + MAX_ITERATIONS = 5"]
    Core -->|MCP Client (JSON-RPC 2.0)| MCPServer["MCP Server (src/mcp_server.py)<br/>vinuni-academic-mcp-server"]
    MCPServer --> ToolDispatcher["Tool Router (src/tools.py)"]
    ToolDispatcher --> Tool1["academic_query"]
    ToolDispatcher --> Tool2["schedule_appointment"]
    ToolDispatcher --> Tool3["search_vinuni_web"]
    Tool1 --> DB[("MOCK_DATABASE<br/>2 sinh vien")]
    Tool2 --> DB
    Tool3 --> Fixture[("Fixture data/vinuni_pages.json<br/>6 trang web VinUni")]
    Core -.->|Ghi nhan vet thuc thi| TraceLog["docs/trace_waterfall.json<br/>15 su kien"]
```

Các điểm cốt lõi của kiến trúc cần trình bày:
- Tách bạch giao diện và dịch vụ phục vụ: Frontend là một trang HTML duy nhất trong `ui/static`, không cần bước build phức tạp, giao tiếp với FastAPI (`ui/server.py`) qua hai endpoint riêng biệt: `POST /api/chatbot` (phục vụ mô hình Cấp 2 không có công cụ) và `POST /api/agent` (phục vụ mô hình Cấp 3 truyền phát từng bước suy luận qua Server-Sent Events).
- Động cơ ReAct đa bước và Native Function Calling: `src/app.py` tích hợp mô hình Google Gemini `gemini-3.1-flash-lite`. Vòng lặp ReAct duy trì bộ nhớ tạm `scratchpad` để nạp ngược dữ liệu `Observation` của bước trước vào ngữ cảnh của bước tiếp theo, đi kèm cơ chế `Loop Guard` ngăn chặn gọi lặp công cụ và giới hạn an toàn `MAX_ITERATIONS = 5`.
- Chuẩn hóa giao tiếp bằng giao thức MCP: Mã nguồn `src/mcp_server.py` triển khai máy chủ `vinuni-academic-mcp-server` tuân thủ chuẩn JSON-RPC 2.0, giúp tách rời hoàn toàn tầng suy luận nghiệp vụ của LLM với tầng thực thi công cụ.
- Tầng dữ liệu thực tế và tra cứu offline: Kết hợp cơ sở dữ liệu mẫu `MOCK_DATABASE` (thông tin 2 sinh viên) và tệp fixture `data/vinuni_pages.json` chứa nội dung thu thập từ 6 trang web chính thức của VinUni (tuân thủ robots.txt), hỗ trợ đối sánh từ khóa song ngữ Việt - Anh và xử lý bỏ dấu tiếng Việt để demo hoàn toàn offline.
- Cơ chế ghi vết và đo lường (Observability): Mọi tương tác trong vòng lặp đều được ghi vết tự động ra tệp `docs/trace_waterfall.json`, cho phép kiểm chứng trực quan cấu trúc Thought - Action - Observation và định lượng thời gian trễ của từng bước.

## 4. Sử dụng những tool gì? Tác dụng của từng tool

Hệ thống cung cấp 3 công cụ chuẩn hóa được định nghĩa trong `src/tools.py` và công bố qua MCP Server:

| Tool | Tham số | Tác dụng | Ví dụ câu hỏi kích hoạt |
| :--- | :--- | :--- | :--- |
| academic_query | student_id (string, bắt buộc): Mã sinh viên cần tra cứu (ví dụ: 'SV2026001') | Truy vấn hồ sơ sinh viên trong MOCK_DATABASE; trả về thông tin họ tên, lớp, GPA, email, trạng thái và tên cố vấn học tập dưới dạng JSON với trạng thái SUCCESS hoặc NOT_FOUND | "Hãy tra cứu thông tin học vụ của sinh viên SV2026001." (TC02) |
| schedule_appointment | student_id (string, bắt buộc), datetime_str (string, bắt buộc): Định dạng 'HH:MM DD/MM/YYYY', advisor_name (string, bắt buộc): Tên cố vấn học tập | Thực hiện đặt lịch hẹn tư vấn học vụ với Cố vấn học tập được chỉ định; trả về mã đặt lịch booking_id cùng trạng thái SUCCESS | "Đặt lịch hẹn tư vấn học vụ cho sinh viên SV2026002 với cố vấn TS. Lê Thị B vào lúc 09:00 ngày 20/09/2026." (TC03) |
| search_vinuni_web | query (string, bắt buộc): Từ khóa tra cứu song ngữ Việt/Anh, topic (string, mặc định 'any'): Giới hạn phạm vi trang (academic_regulations, academic_calendar, programs, tuition, scholarships, registrar, any) | Tra cứu nội dung trên fixture website VinUni offline (data/vinuni_pages.json), chấm điểm từ vựng kết hợp mở rộng thuật ngữ song ngữ và đối sánh bỏ dấu; trả về danh sách tối đa 3 đoạn trích dẫn (snippets) phù hợp nhất kèm tiêu đề, đề mục và đường dẫn URL nguồn | "Theo quy chế học vụ VinUni, sinh viên cần GPA tích lũy tối thiểu bao nhiêu để tốt nghiệp?" (TC06) |

## 5. Demo trực tiếp 1-2 câu hỏi, show trace log từng bước

### Kịch bản Câu 1: So sánh Chatbot Baseline vs ReAct Agent (TC06)

- Thao tác của người thuyết trình: Chọn chế độ "So sánh Chatbot vs Agent" trên giao diện web, dán câu hỏi TC06 vào ô nhập liệu và nhấn nút gửi:
  "Theo quy chế học vụ VinUni, sinh viên cần GPA tích lũy tối thiểu bao nhiêu để tốt nghiệp?"
- Lời dẫn và điểm cần chỉ trên màn hình:
  + Phía Chatbot Baseline (Cấp 2): Hãy chỉ vào khung phản hồi của Chatbot và nêu rõ: Chatbot trả lời dựa trên kiến thức tổng quát của mô hình, không thể truy cập tài liệu nội bộ hoặc đưa ra câu trả lời phỏng đoán chung chung, không có trích dẫn nguồn văn bản chính thống.
  + Phía ReAct Agent (Cấp 3): Hãy chỉ vào luồng sự kiện streaming hiển thị từng bước:
    * Bước 1 (Thought): Agent nhận định câu hỏi liên quan đến quy chế học vụ VinUni nên cần sử dụng công cụ tra cứu website chính thức.
    * Bước 1 (Action): Agent phát sinh lời gọi công cụ `search_vinuni_web` với tham số query mở rộng song ngữ: `GPA tối thiểu tốt nghiệp minimum cumulative GPA graduation requirement`.
    * Bước 1 (Observation): MCP Server trả về đoạn trích dẫn từ Điều 28 (Article 28: Recognition of Graduation) thuộc trang Quy chế học vụ chương trình đại học chính quy: `https://policy.vinuni.edu.vn/all-policies/academic-regulations-for-full-time-undergraduate-programs/`.
    * Bước 2 (Final Answer): Agent tổng hợp câu trả lời khẳng định mức GPA tích lũy tối thiểu để tốt nghiệp là 2.00/4.00, đồng thời cung cấp đầy đủ liên kết URL nguồn để sinh viên kiểm chứng.

### Kịch bản Câu 2: Suy luận đa bước kết hợp đa công cụ (TC07)

- Thao tác của người thuyết trình: Dán câu hỏi TC07 vào ô nhập liệu:
  "Tra cứu GPA của sinh viên SV2026002, rồi đối chiếu với quy chế học vụ trên website VinUni để cho biết em ấy có đủ điều kiện GPA tốt nghiệp không."
  (Nếu muốn demo kịch bản đặt lịch hẹn tự động, có thể dùng câu dự phòng TC04 để Agent tra cứu cố vấn của SV2026001 rồi lấy đúng tên PGS.TS Nguyễn Văn A để đặt lịch).
- Lời dẫn và điểm cần chỉ trên màn hình:
  + Hành động 1 (Action 1): Agent nhận diện cần lấy điểm sinh viên trước, gọi `academic_query` với `student_id: SV2026002`.
  + Quan sát 1 (Observation 1): Dữ liệu trả về cho thấy sinh viên Trần Thị Bình có điểm GPA tích lũy là 3.60.
  + Hành động 2 (Action 2): Nhờ cơ chế Scratchpad lưu trữ Observation 1, Agent tiếp tục suy luận cần đối chiếu quy chế và tự động phát sinh lời gọi `search_vinuni_web` để tìm quy định về điểm tốt nghiệp.
  + Quan sát 2 (Observation 2): Dữ liệu từ fixture website VinUni trả về Điều 28 với mức GPA yêu cầu là 2.00/4.00.
  + Kết luận cuối cùng (Final Answer): Agent kết hợp thông tin từ cả hai công cụ, đưa ra kết luận rõ ràng: sinh viên Trần Thị Bình có GPA 3.60, cao hơn mức quy định tối thiểu 2.00/4.00 của VinUni nên đã đáp ứng điều kiện về điểm số để xét tốt nghiệp.
- Chỉ số định lượng và bằng chứng Waterfall Trace:
  + Hãy chỉ vào dòng tổng kết trên màn hình: Phiên xử lý hoàn thành qua 3 bước với 2 lượt gọi Tool qua MCP Server, tổng độ trễ trên API thật đạt xấp xỉ 5.4 giây (đặc trưng thời gian phản hồi mạng thực tế).
  + Nêu rõ toàn bộ chuỗi sự kiện được ghi nhận minh bạch vào tệp `docs/trace_waterfall.json`, bao gồm đầy đủ 15 sự kiện của toàn bộ 7 test cases với từng tham số đầu vào và kết quả quan sát.

## Câu hỏi có thể được hỏi

1. Tại sao hệ thống lại sử dụng dữ liệu fixture tĩnh mà không cào dữ liệu trực tiếp (live crawling) khi người dùng hỏi?
- Trả lời: Thu thập dữ liệu trực tiếp trong lúc trả lời dễ gây nghẽn mạng, tăng đột biến độ trễ hoặc bị chặn bởi máy chủ mục tiêu; việc dùng fixture gồm 6 trang đã thu thập tuân thủ robots.txt giúp hệ thống chạy ổn định, lặp lại nhất quán và hoạt động được ngay cả khi ngoại tuyến.

2. Cơ chế nào giúp Agent ngăn chặn hiện tượng bịa đặt thông tin (Hallucination)?
- Trả lời: System Prompt đặt ra quy tắc nghiêm ngặt buộc Agent chỉ được kết luận dựa trên dữ liệu nằm trong Observation do Tool trả về (Grounding); nếu mã sinh viên không tồn tại (như TC05) hoặc trang web không có thông tin, Agent phải thông báo trung thực thay vì tự suy đoán.

3. Nếu muốn nâng cấp hệ thống này lên AI Cấp độ 4 (Autonomous Agent), chúng ta cần bổ sung những thành phần nào?
- Trả lời: Cần bổ sung cơ chế tự phân rã mục tiêu và lập kế hoạch dài hạn (planning), hệ thống lưu trữ trạng thái và bộ nhớ ngữ cảnh qua nhiều phiên làm việc (persistent memory), cùng khả năng tự đánh giá và sửa đổi sai sót trong quá trình thực thi (self-reflection).

4. Giao thức MCP mang lại giá trị gia tăng gì so với việc triển khai Function Calling trực tiếp vào mã nguồn?
- Trả lời: MCP tách rời ứng dụng Agent và máy chủ cung cấp công cụ theo kiến trúc chuẩn JSON-RPC 2.0, cho phép các công cụ học vụ được quản lý độc lập, dễ dàng tái sử dụng cho nhiều tác tử hoặc nền tảng khác nhau mà không phải viết lại mã kết nối.

5. Cơ chế Loop Guard và biến MAX_ITERATIONS có vai trò gì trong vòng lặp ReAct?
- Trả lời: Loop Guard nhận diện chữ ký của lời gọi công cụ để lập tức ngắt vòng lặp nếu LLM liên tục đề xuất cùng một hành động đã thực hiện, trong khi MAX_ITERATIONS = 5 đóng vai trò chốt chặn an toàn cuối cùng giúp Agent luôn dừng lại và tổng hợp câu trả lời cho người dùng.
