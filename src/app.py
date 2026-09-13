"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def summarize_observation(obs_data: dict) -> str:
    """Tổng hợp câu trả lời tiếng Việt từ Observation khi Agent không tự kết luận được"""
    if not obs_data:
        return "Chưa thể trả lời chi tiết do chưa nhận được dữ liệu từ MCP Server."

    if obs_data.get("status") == "SUCCESS":
        if "data" in obs_data:
            d = obs_data["data"]
            return (
                f"Kết quả tra cứu cho sinh viên {obs_data.get('student_id', '')} ({d.get('full_name', '')}): "
                f"Lớp {d.get('class', '')}, GPA: {d.get('gpa', '')}, Email: {d.get('email', '')}, "
                f"Trạng thái: {d.get('status', '')}, Cố vấn: {d.get('advisor', '')}."
            )
        if "message" in obs_data:
            return obs_data["message"]
        return f"Đã hoàn tất xử lý qua MCP Server: {json.dumps(obs_data, ensure_ascii=False)}"

    if obs_data.get("status") == "NOT_FOUND":
        return obs_data.get("message", "Không tìm thấy thông tin sinh viên yêu cầu.")

    return f"Phản hồi từ công cụ: {json.dumps(obs_data, ensure_ascii=False)}"


def iter_react_steps(user_query: str, provider, mcp_server: MCPAcademicServer):
    """
    [REACT AGENT LOOP - STREAMING] Sinh lần lượt các sự kiện của vòng lặp
    Thought -> Action -> Observation để giao diện realtime tiêu thụ được.
    """
    run_start_time = time.time()

    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    scratchpad = []
    executed_calls = set()
    last_observation = {}
    final_answer = None

    yield {
        "event": "start",
        "question": user_query,
        "max_iterations": MAX_ITERATIONS,
        "tools": [tool.get("name") for tool in tools_list]
    }

    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()

        # Nạp lại toàn bộ Observation đã thu thập để LLM quyết định hành động kế tiếp
        prompt = user_query
        if scratchpad:
            prompt = (
                f"{user_query}\n\n[KẾT QUẢ CÁC BƯỚC ĐÃ THỰC HIỆN]\n"
                + "\n".join(scratchpad)
                + "\n\nDựa vào các Observation trên: nếu yêu cầu của sinh viên chưa hoàn tất, hãy gọi tiếp Tool phù hợp. "
                "Nếu đã đủ dữ liệu, hãy trả lời cuối cùng bằng văn bản, chỉ dùng thông tin có trong Observation."
            )

        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(prompt, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)

        thought = llm_response.get("thought", "Đang suy luận...")
        yield {"event": "thought", "step": step, "thought": thought, "latency_ms": latency_ms}

        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_answer = llm_response.get("content", "") or summarize_observation(last_observation)
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_answer,
                "latency_ms": latency_ms
            })
            yield {
                "event": "final",
                "step": step,
                "thought": thought,
                "output": final_answer,
                "latency_ms": latency_ms
            }
            break

        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            yield {"event": "action", "step": step, "tool_name": tool_name, "arguments": arguments}

            # Chặn lặp vô hạn khi LLM đề xuất lại đúng lời gọi Tool đã thực thi
            call_signature = f"{tool_name}:{json.dumps(arguments, ensure_ascii=False, sort_keys=True)}"
            if call_signature in executed_calls:
                yield {"event": "guard", "step": step, "reason": "repeat_tool_call"}
                final_answer = summarize_observation(last_observation)
                guard_thought = "Phát hiện lời gọi Tool lặp lại, tổng hợp kết quả từ Observation gần nhất."
                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "FINAL_ANSWER",
                    "thought": guard_thought,
                    "output": final_answer,
                    "latency_ms": latency_ms
                })
                yield {
                    "event": "final",
                    "step": step,
                    "thought": guard_thought,
                    "output": final_answer,
                    "latency_ms": latency_ms
                }
                break
            executed_calls.add(call_signature)

            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            last_observation = obs_data
            obs_str = json.dumps(obs_data, ensure_ascii=False)

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })
            yield {
                "event": "observation",
                "step": step,
                "tool_name": tool_name,
                "observation": obs_data,
                "jsonrpc": "2.0",
                "server": mcp_server.server_name
            }

            # Nạp Observation vào scratchpad cho lượt suy luận kế tiếp
            scratchpad.append(
                f"- Bước {step}: gọi Tool {tool_name}({json.dumps(arguments, ensure_ascii=False)}) "
                f"→ Observation: {obs_str}"
            )

    # Hết số vòng lặp cho phép mà Agent vẫn chưa chốt câu trả lời
    if final_answer is None:
        yield {"event": "guard", "step": step, "reason": "max_iterations"}
        final_answer = summarize_observation(last_observation)
        max_iter_thought = f"Đã đạt giới hạn {MAX_ITERATIONS} vòng lặp, tổng hợp kết quả từ Observation gần nhất."
        trace_logs.append({
            "step": step + 1,
            "query": user_query,
            "action_type": "FINAL_ANSWER",
            "thought": max_iter_thought,
            "output": final_answer,
            "latency_ms": 10.0
        })
        yield {
            "event": "final",
            "step": step + 1,
            "thought": max_iter_thought,
            "output": final_answer,
            "latency_ms": 10.0
        }

    yield {
        "event": "done",
        "trace": trace_logs,
        "total_latency_ms": round((time.time() - run_start_time) * 1000, 2)
    }


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Trả về danh sách trace log của phiên thực thi.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    trace_logs = []
    for event in iter_react_steps(user_query, provider, mcp_server):
        event_type = event["event"]

        if event_type == "thought":
            print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {event['step']}/{MAX_ITERATIONS}) ---")
            print(f"🧠 [Thought]: {event['thought']}")
        elif event_type == "action":
            print(f"🛠️ [Action Proposed]: {event['tool_name']}({event['arguments']})")
        elif event_type == "observation":
            print(f"👁️ [Observation từ MCP Server]: {json.dumps(event['observation'], ensure_ascii=False)}")
        elif event_type == "guard" and event["reason"] == "repeat_tool_call":
            print("⚠️ [Loop Guard]: Tool này đã được gọi với cùng tham số. Dừng vòng lặp và tổng hợp kết quả.")
        elif event_type == "final":
            print(f"🏁 [Final Answer]: {event['output']}")
        elif event_type == "done":
            trace_logs = event["trace"]

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'")
        print("   - Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001'")
        print("   - Đặt lịch hẹn: 'Đặt lịch hẹn tư vấn cho SV2026001 vào 14:00 ngày 15/09/2026'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu học vụ) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
