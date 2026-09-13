/* =============================================================
   Trợ lý Học vụ VinUni: ReAct Agent + MCP
   Vanilla JS. No build step, no runtime network dependency
   other than the local FastAPI server on the same origin.
   ============================================================= */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };

  var state = {
    mode: "agent",
    running: false,
    maxLatency: 0,
    trace: [],
    stepCount: 0,
    toolCalls: 0
  };

  /* ---------------- text safety ---------------- */

  function escapeHtml(value) {
    return String(value === null || value === undefined ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /* Model output may contain **bold** and newlines. Escape first,
     then allow only those two constructs back in. */
  function renderRich(value) {
    var safe = escapeHtml(value);
    safe = safe.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    safe = safe.replace(/\r\n|\r|\n/g, "<br>");
    return safe;
  }

  function prettyJson(value) {
    try { return JSON.stringify(value, null, 2); }
    catch (err) { return String(value); }
  }

  function formatMs(ms) {
    var n = Number(ms);
    if (!isFinite(n)) { return ""; }
    if (n >= 1000) { return (n / 1000).toFixed(2) + " s"; }
    return Math.round(n) + " ms";
  }

  /* ---------------- tabs ---------------- */

  function initTabs() {
    var tabs = document.querySelectorAll(".tab");
    Array.prototype.forEach.call(tabs, function (tab) {
      tab.addEventListener("click", function () {
        Array.prototype.forEach.call(tabs, function (other) {
          var on = other === tab;
          other.classList.toggle("is-active", on);
          if (on) { other.setAttribute("aria-current", "page"); }
          else { other.removeAttribute("aria-current"); }
        });
        var views = document.querySelectorAll(".view");
        Array.prototype.forEach.call(views, function (view) {
          view.classList.toggle("is-active", view.id === "view-" + tab.dataset.view);
        });
        window.scrollTo(0, 0);
      });
    });
  }

  /* ---------------- health chip ---------------- */

  function loadHealth() {
    var box = $("healthChip");
    fetch("/api/health")
      .then(function (res) {
        if (!res.ok) { throw new Error("HTTP " + res.status); }
        return res.json();
      })
      .then(function (data) {
        box.className = "health health-ok";
        box.innerHTML =
          '<span class="health-item">Provider <b>' + escapeHtml(data.provider) + "</b></span>" +
          '<span class="health-item">Model <b class="mono">' + escapeHtml(data.model) + "</b></span>" +
          '<span class="health-item">MCP <b class="mono">' + escapeHtml(data.mcp_server) +
            " v" + escapeHtml(data.mcp_version) + "</b></span>";
      })
      .catch(function (err) {
        box.className = "health health-err";
        box.textContent = "Không kết nối được máy chủ: " + err.message;
      });
  }

  /* ---------------- suggested questions ---------------- */

  function loadTestCases() {
    var box = $("chips");
    var errBox = $("chipsError");
    fetch("/api/test-cases")
      .then(function (res) {
        if (!res.ok) { throw new Error("HTTP " + res.status); }
        return res.json();
      })
      .then(function (items) {
        box.innerHTML = "";
        if (!Array.isArray(items) || items.length === 0) {
          box.innerHTML = '<p class="field-help">Chưa có câu hỏi mẫu nào trong config/test_cases.json.</p>';
          return;
        }
        items.forEach(function (item) {
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "chip";
          btn.innerHTML =
            '<span class="chip-id">' + escapeHtml(item.id) + "</span>" +
            "<span>" + escapeHtml(item.question) + "</span>";
          btn.addEventListener("click", function () {
            var field = $("question");
            field.value = item.question;
            field.focus();
            hideError($("questionError"));
          });
          box.appendChild(btn);
        });
      })
      .catch(function (err) {
        box.innerHTML = "";
        showError(errBox, "Không tải được câu hỏi mẫu: " + err.message);
      });
  }

  /* ---------------- tools view ---------------- */

  function loadTools() {
    var body = $("toolsBody");
    var meta = $("toolsMeta");
    fetch("/api/tools")
      .then(function (res) {
        if (!res.ok) { throw new Error("HTTP " + res.status); }
        return res.json();
      })
      .then(function (data) {
        var tools = (data && data.tools) || [];
        meta.textContent = data.server + " v" + data.version + " (" + tools.length + " Tool)";
        if (tools.length === 0) {
          body.innerHTML = '<p class="empty-text">MCP Server chưa công bố Tool nào.</p>';
          return;
        }
        body.innerHTML = tools.map(renderToolBlock).join("");
      })
      .catch(function (err) {
        body.innerHTML = '<p class="inline-error">Không tải được danh sách Tool: ' +
          escapeHtml(err.message) + "</p>";
      });
  }

  function renderToolBlock(tool) {
    var params = (tool.parameters && tool.parameters.properties) || {};
    var required = (tool.parameters && tool.parameters.required) || [];
    var names = Object.keys(params);

    var rows = names.map(function (name) {
      var spec = params[name] || {};
      var isReq = required.indexOf(name) !== -1;
      return "<tr>" +
        '<td class="mono">' + escapeHtml(name) + "</td>" +
        '<td class="mono">' + escapeHtml(spec.type || "string") + "</td>" +
        "<td>" + (isReq
          ? '<span class="badge badge-ok">Bắt buộc</span>'
          : '<span class="badge badge-plain">Tùy chọn</span>') + "</td>" +
        "<td>" + escapeHtml(spec.description || "") + "</td>" +
        "</tr>";
    }).join("");

    var table = names.length
      ? '<div class="table-wrap"><table class="params">' +
          "<thead><tr><th>Tên tham số</th><th>Kiểu</th><th>Bắt buộc</th><th>Mô tả</th></tr></thead>" +
          "<tbody>" + rows + "</tbody></table></div>"
      : '<p class="field-help">Tool này không nhận tham số.</p>';

    return '<section class="tool-block">' +
      '<div class="tool-head"><h3>' + escapeHtml(tool.name) + "</h3>" +
      '<span class="badge badge-plain">' + names.length + " tham số</span></div>" +
      '<p class="tool-desc">' + escapeHtml(tool.description || "") + "</p>" +
      table +
      "</section>";
  }

  /* ---------------- errors ---------------- */

  function showError(node, message) {
    node.textContent = message;
    node.hidden = false;
  }
  function hideError(node) {
    node.hidden = true;
    node.textContent = "";
  }

  /* ---------------- trace panel ---------------- */

  function resetTrace() {
    state.maxLatency = 0;
    state.trace = [];
    state.stepCount = 0;
    state.toolCalls = 0;
    $("trace").innerHTML =
      '<div class="waiting" id="traceWaiting">' +
      '<p class="empty-title">Đang chờ sự kiện đầu tiên từ Agent</p>' +
      '<span class="sk sk-line" style="width:30%"></span>' +
      '<span class="sk sk-line" style="width:84%"></span>' +
      '<span class="sk sk-line" style="width:66%"></span>' +
      "</div>";
    $("traceSummary").hidden = true;
    $("traceSummary").innerHTML = "";
    $("copyBtn").hidden = true;
  }

  function appendRow(html, variant) {
    var waiting = $("traceWaiting");
    if (waiting) { waiting.parentNode.removeChild(waiting); }
    var wrap = document.createElement("div");
    wrap.className = "row row-" + variant + " row-enter";
    wrap.innerHTML = html;
    $("trace").appendChild(wrap);
    wrap.scrollIntoView({ block: "nearest" });
    return wrap;
  }

  /* The waterfall: every bar is scaled against the slowest step
     seen so far, and existing bars are rescaled when a slower
     step arrives. */
  function registerLatency(node, ms) {
    var n = Number(ms);
    if (!isFinite(n) || n <= 0) { return; }
    node.dataset.latency = String(n);
    if (n > state.maxLatency) { state.maxLatency = n; }
    rescaleBars();
  }

  function rescaleBars() {
    var bars = document.querySelectorAll("#trace .row[data-latency]");
    Array.prototype.forEach.call(bars, function (row) {
      var bar = row.querySelector(".lat-bar");
      if (!bar) { return; }
      var pct = state.maxLatency > 0
        ? (Number(row.dataset.latency) / state.maxLatency) * 100
        : 0;
      bar.style.width = Math.max(pct, 2).toFixed(1) + "%";
    });
  }

  function latencyMarkup(ms) {
    return '<div class="lat">' +
      '<span class="lat-track"><span class="lat-bar"></span></span>' +
      '<span class="lat-val">' + escapeHtml(formatMs(ms)) + "</span>" +
      "</div>";
  }

  /* The server sends the Tool result directly as `observation`, but a raw
     JSON-RPC envelope would nest it under `result`. Accept both. */
  function statusBadge(observation) {
    if (!observation) { return ""; }
    var status = observation.status ||
      (observation.result && observation.result.status);
    if (!status) { return ""; }
    var cls = "badge-plain";
    if (status === "SUCCESS") { cls = "badge-ok"; }
    else if (status === "NOT_FOUND") { cls = "badge-warn"; }
    else if (String(status).indexOf("ERROR") !== -1 || status === "UNKNOWN_TOOL") { cls = "badge-err"; }
    return '<span class="badge ' + cls + '">' + escapeHtml(status) + "</span>";
  }

  function jsonBlock(value) {
    var text = prettyJson(value);
    var lines = text.split("\n").length;
    if (lines <= 12 && text.length <= 700) {
      return '<pre class="json">' + escapeHtml(text) + "</pre>";
    }
    return '<details class="json-wrap"><summary><span>JSON</span></summary>' +
      '<pre class="json">' + escapeHtml(text) + "</pre></details>";
  }

  function onThought(data) {
    state.stepCount = Math.max(state.stepCount, Number(data.step) || 0);
    var row = appendRow(
      '<div class="row-head"><span class="kind kind-thought">THOUGHT</span>' +
      '<span class="step-no">Bước ' + escapeHtml(data.step) + "</span></div>" +
      '<p class="row-text">' + renderRich(data.thought) + "</p>" +
      latencyMarkup(data.latency_ms),
      "thought"
    );
    registerLatency(row, data.latency_ms);
  }

  function onAction(data) {
    var args = data.arguments || {};
    var argHtml = Object.keys(args).map(function (key) {
      return '<div class="arg"><b>' + escapeHtml(key) + ":</b> " +
        escapeHtml(typeof args[key] === "object" ? prettyJson(args[key]) : args[key]) + "</div>";
    }).join("");
    if (!argHtml) { argHtml = '<div class="arg">Không có tham số</div>'; }

    appendRow(
      '<div class="row-head"><span class="kind kind-action">ACTION</span>' +
      '<span class="step-no">Bước ' + escapeHtml(data.step) + "</span>" +
      '<span class="tool-name">' + escapeHtml(data.tool_name) + "</span></div>" +
      '<div class="args">' + argHtml + "</div>",
      "action"
    );
  }

  /* Counted here, not on ACTION: an action blocked by the Loop Guard
     never reaches the MCP Server, so it is not a real Tool call. */
  function onObservation(data) {
    state.toolCalls += 1;
    appendRow(
      '<div class="row-head"><span class="kind kind-obs">OBSERVATION</span>' +
      '<span class="step-no">Bước ' + escapeHtml(data.step) + "</span>" +
      statusBadge(data.observation) +
      '<span class="src">' + escapeHtml(data.server || "") +
        " &middot; JSON-RPC " + escapeHtml(data.jsonrpc || "2.0") + "</span></div>" +
      jsonBlock(data.observation),
      "obs"
    );
  }

  function onGuard(data) {
    var reasons = {
      repeat_tool_call: "Phát hiện gọi lặp lại cùng một Tool với cùng tham số. Vòng lặp dừng lại và tổng hợp kết quả đã có.",
      max_iterations: "Đã chạm giới hạn số vòng lặp tối đa. Vòng lặp dừng lại để tránh chạy vô hạn."
    };
    appendRow(
      '<div class="row-head"><span class="kind kind-guard">GUARD</span>' +
      '<span class="step-no">Bước ' + escapeHtml(data.step) + "</span>" +
      '<span class="src">' + escapeHtml(data.reason) + "</span></div>" +
      '<p class="row-text">' + escapeHtml(reasons[data.reason] || "Vòng lặp bị chặn bởi Loop Guard.") + "</p>",
      "guard"
    );
  }

  function onFinal(data) {
    state.stepCount = Math.max(state.stepCount, Number(data.step) || 0);
    var row = appendRow(
      '<div class="row-head"><span class="kind kind-final">FINAL</span>' +
      '<span class="step-no">Bước ' + escapeHtml(data.step) + "</span></div>" +
      '<p class="row-text">' + renderRich(data.output) + "</p>" +
      latencyMarkup(data.latency_ms),
      "final"
    );
    registerLatency(row, data.latency_ms);
  }

  function onTraceError(message) {
    appendRow(
      '<div class="row-head"><span class="kind kind-error">LỖI</span></div>' +
      '<p class="row-text">' + escapeHtml(message) + "</p>",
      "error"
    );
  }

  function onDone(data) {
    state.trace = (data && data.trace) || [];
    var summary = $("traceSummary");
    summary.innerHTML =
      "<span>Số bước <b>" + state.stepCount + "</b></span>" +
      "<span>Số lượt gọi Tool <b>" + state.toolCalls + "</b></span>" +
      "<span>Tổng độ trễ <b>" + escapeHtml(formatMs(data && data.total_latency_ms)) + "</b></span>";
    summary.hidden = false;
    $("copyBtn").hidden = false;
  }

  /* ---------------- answer cards ---------------- */

  function skeletonCard() {
    return '<div class="sk-card">' +
      '<span class="sk sk-line" style="width:38%"></span>' +
      '<span class="sk sk-line" style="width:94%"></span>' +
      '<span class="sk sk-line" style="width:86%"></span>' +
      '<span class="sk sk-line" style="width:52%"></span>' +
      "</div>";
  }

  function showSkeleton(compare) {
    $("results").innerHTML =
      '<div class="answers' + (compare ? " is-compare" : "") + '">' +
      skeletonCard() + (compare ? skeletonCard() : "") +
      "</div>";
  }

  function renderAnswers(agent, chatbot) {
    var cards = "";
    if (chatbot) {
      cards +=
        '<article class="card card-chatbot">' +
        '<div class="card-head"><h3 class="card-title">Chatbot Cấp 2: không có Tool</h3>' +
        '<span class="card-meta">' + escapeHtml(formatMs(chatbot.latency_ms)) + "</span></div>" +
        '<div class="card-text">' + renderRich(chatbot.answer) + "</div>" +
        '<p class="card-note">Chatbot chỉ dùng kiến thức có sẵn trong mô hình, không tra cứu được cơ sở dữ liệu học vụ.</p>' +
        "</article>";
    }
    cards +=
      '<article class="card card-agent">' +
      '<div class="card-head"><h3 class="card-title">ReAct Agent Cấp 3: có Tool qua MCP</h3>' +
      '<span class="card-meta">' + escapeHtml(formatMs(agent.latency_ms)) + "</span></div>" +
      '<div class="card-text">' + renderRich(agent.answer) + "</div>" +
      (chatbot
        ? '<p class="card-note">Agent gọi Tool qua MCP Server nên trả lời bằng dữ liệu thật, xem vết suy luận bên phải.</p>'
        : "") +
      "</article>";

    $("results").innerHTML =
      '<div class="answers' + (chatbot ? " is-compare" : "") + '">' + cards + "</div>";
  }

  function renderResultError(message) {
    $("results").innerHTML = '<p class="inline-error">' + escapeHtml(message) + "</p>";
  }

  /* ---------------- SSE over POST ---------------- */

  function parseSseBlock(block) {
    var name = "message";
    var dataLines = [];
    block.split("\n").forEach(function (line) {
      if (line.indexOf("event:") === 0) {
        name = line.slice(6).trim();
      } else if (line.indexOf("data:") === 0) {
        dataLines.push(line.slice(5).replace(/^ /, ""));
      }
    });
    if (dataLines.length === 0) { return null; }
    var payload;
    try { payload = JSON.parse(dataLines.join("\n")); }
    catch (err) { return null; }
    return { name: name, data: payload };
  }

  function runAgent(question, onEvent) {
    return fetch("/api/agent", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
      body: JSON.stringify({ question: question })
    }).then(function (response) {
      if (!response.ok) { throw new Error("HTTP " + response.status); }
      if (!response.body) { throw new Error("Trình duyệt không hỗ trợ đọc luồng dữ liệu."); }

      var reader = response.body.getReader();
      var decoder = new TextDecoder("utf-8");
      var buffer = "";

      function flush(raw) {
        var parsed = parseSseBlock(raw);
        if (parsed) { onEvent(parsed.name, parsed.data); }
      }

      function pump() {
        return reader.read().then(function (chunk) {
          if (chunk.done) {
            if (buffer.trim()) { flush(buffer); }
            return;
          }
          buffer += decoder.decode(chunk.value, { stream: true });
          var blocks = buffer.split("\n\n");
          buffer = blocks.pop();
          blocks.forEach(function (block) {
            if (block.trim()) { flush(block); }
          });
          return pump();
        });
      }
      return pump();
    });
  }

  function runChatbot(question) {
    return fetch("/api/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question })
    }).then(function (res) {
      if (!res.ok) { throw new Error("HTTP " + res.status); }
      return res.json();
    });
  }

  /* ---------------- run orchestration ---------------- */

  function setRunning(on) {
    state.running = on;
    document.body.classList.toggle("is-running", on);
    var btn = $("runBtn");
    btn.disabled = on;
    btn.textContent = on ? "Đang chạy..." : "Chạy demo";
  }

  function submit() {
    if (state.running) { return; }
    var question = $("question").value.trim();
    if (!question) {
      showError($("questionError"), "Hãy nhập câu hỏi trước khi chạy demo.");
      $("question").focus();
      return;
    }
    hideError($("questionError"));

    var compare = state.mode === "compare";
    resetTrace();
    showSkeleton(compare);
    setRunning(true);

    var agentAnswer = "";
    var agentLatency = 0;
    var failed = false;

    var chatbotPromise = compare
      ? runChatbot(question).catch(function (err) {
          return { answer: "Không gọi được Chatbot: " + err.message, latency_ms: 0, failed: true };
        })
      : Promise.resolve(null);

    var agentPromise = runAgent(question, function (name, data) {
      if (name === "start") { return; }
      if (name === "thought") { onThought(data); }
      else if (name === "action") { onAction(data); }
      else if (name === "observation") { onObservation(data); }
      else if (name === "guard") { onGuard(data); }
      else if (name === "final") {
        agentAnswer = data.output;
        agentLatency = data.latency_ms;
        onFinal(data);
      } else if (name === "error") {
        failed = true;
        agentAnswer = data.message;
        onTraceError(data.message);
      } else if (name === "done") {
        onDone(data);
      }
    });

    Promise.all([agentPromise, chatbotPromise])
      .then(function (results) {
        var chatbot = results[1];
        if (failed) {
          renderResultError("Agent gặp lỗi: " + agentAnswer);
          return;
        }
        renderAnswers(
          { answer: agentAnswer || "Agent không trả về nội dung.", latency_ms: agentLatency },
          chatbot
        );
      })
      .catch(function (err) {
        renderResultError("Không chạy được demo: " + err.message);
        onTraceError(err.message);
      })
      .then(function () {
        setRunning(false);
      });
  }

  /* ---------------- copy trace ---------------- */

  function copyTrace() {
    var btn = $("copyBtn");
    var text = prettyJson(state.trace);
    var restore = function (label) {
      btn.textContent = label;
      window.setTimeout(function () { btn.textContent = "Sao chép trace JSON"; }, 2000);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text)
        .then(function () { restore("Đã sao chép"); })
        .catch(function () { restore("Không sao chép được"); });
      return;
    }
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try { document.execCommand("copy"); restore("Đã sao chép"); }
    catch (err) { restore("Không sao chép được"); }
    document.body.removeChild(area);
  }

  /* ---------------- wiring ---------------- */

  function initForm() {
    $("askForm").addEventListener("submit", function (event) {
      event.preventDefault();
      submit();
    });

    $("question").addEventListener("keydown", function (event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submit();
      }
    });

    var segs = document.querySelectorAll(".seg-btn");
    Array.prototype.forEach.call(segs, function (seg) {
      seg.addEventListener("click", function () {
        state.mode = seg.dataset.mode;
        Array.prototype.forEach.call(segs, function (other) {
          var on = other === seg;
          other.classList.toggle("is-on", on);
          other.setAttribute("aria-checked", on ? "true" : "false");
        });
      });
    });

    $("copyBtn").addEventListener("click", copyTrace);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTabs();
    initForm();
    loadHealth();
    loadTestCases();
    loadTools();
  });
})();
