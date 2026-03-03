console.log("KYC SCRIPT LOADED");

const vscodeApi = acquireVsCodeApi();

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("question");
  const chat = document.getElementById("chat");
  const btn = document.getElementById("sendBtn");
  const startupLoader = document.getElementById("startupLoader");

  let loadingEl = null;
  let isBusy = false;

  const state = vscodeApi.getState() || { messages: [] };

  function saveState() {
    vscodeApi.setState(state);
  }

  function appendNode(node) {
    chat.appendChild(node);
    chat.scrollTop = chat.scrollHeight;
  }

  function addMessage(text, type) {
    const div = document.createElement("div");
    div.className = `msg ${type}`;
    div.textContent = text;

    appendNode(div);

    state.messages.push({
      kind: "text",
      type,
      text,
    });

    saveState();
  }

  function renderAI(answer, sources, meta) {
    const wrapper = document.createElement("div");
    wrapper.className = "msg ai";

    const answerBox = document.createElement("div");
    answerBox.className = "answerBox";
    answerBox.textContent = answer;

    wrapper.appendChild(answerBox);

    if (meta && meta.search_time !== undefined) {
      const metrics = document.createElement("div");
      metrics.className = "metricsBar";

      const timeText =
        typeof meta.search_time === "number"
          ? meta.search_time.toFixed(2) + "s"
          : "";

      const fileText =
        meta.file_count !== undefined ? meta.file_count + " files" : "";

      const hitText = sources && sources.length ? sources.length + " hits" : "";

      metrics.innerHTML = `
    ${timeText ? `<div class="metricItem">⏱ ${timeText}</div>` : ""}
    ${fileText ? `<div class="metricItem">📂 ${fileText}</div>` : ""}
    ${hitText ? `<div class="metricItem">🎯 ${hitText}</div>` : ""}
  `;

      if (metrics.innerHTML.trim()) {
        wrapper.appendChild(metrics);
      }
    }

    if (sources && sources.length) {
      const srcWrap = document.createElement("div");
      srcWrap.className = "sources";

      sources.forEach((s) => {
        const card = document.createElement("div");
        card.className = "sourceCard";

        const conf =
          s.confidence !== undefined
            ? `<div class="confBadge">confidence: ${(s.confidence * 100).toFixed(1)}%</div>`
            : "";

        card.innerHTML = `
          <div class="filePath">${s.file}</div>
          <div class="lineNo">Line: ${s.line || "?"}</div>
          ${conf}
        `;

        card.onclick = () => {
          vscodeApi.postMessage({
            command: "openFile",
            file: s.file,
            line: s.line || 1,
          });
        };

        srcWrap.appendChild(card);
      });

      wrapper.appendChild(srcWrap);
    }

    appendNode(wrapper);

    state.messages.push({
      kind: "ai",
      answer,
      sources,
      meta,
    });

    saveState();
  }

  function restoreChat() {
    if (!state.messages.length) return;

    state.messages.forEach((m) => {
      if (m.kind === "text") {
        const div = document.createElement("div");
        div.className = `msg ${m.type}`;
        div.textContent = m.text;
        chat.appendChild(div);
      } else {
        renderAI(m.answer, m.sources, m.meta);
      }
    });
  }

  function showLoader() {
    if (loadingEl) return;

    loadingEl = document.createElement("div");
    loadingEl.className = "loader";
    loadingEl.innerHTML = `
      <div class="spinner"></div>
      <span>KYC is thinking...</span>
    `;
    appendNode(loadingEl);
  }

  function removeLoader() {
    if (loadingEl) {
      loadingEl.remove();
      loadingEl = null;
    }
  }

  function lockUI() {
    isBusy = true;
    btn.disabled = true;
    input.disabled = true;
  }

  function unlockUI() {
    isBusy = false;
    btn.disabled = false;
    input.disabled = false;
    input.focus();
  }

  async function send() {
    if (isBusy) return;

    const q = input.value.trim();
    if (!q) return;

    addMessage(q, "user");
    input.value = "";

    lockUI();
    showLoader();

    try {
      const res = await fetch(
        `http://127.0.0.1:${window.KYC_BACKEND_PORT}/ask`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q }),
        },
      );

      const data = await res.json();

      removeLoader();
      renderAI(data.answer, data.sources, {
        search_time: data.search_time,
        files_scanned: data.files_scanned,
      });
    } catch (err) {
      removeLoader();
      addMessage("Error: " + err, "ai");
    } finally {
      unlockUI();
    }
  }

  btn.addEventListener("click", send);

  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      send();
    }
  });

  restoreChat();

  function hideStartup() {
    if (!startupLoader) return;
    startupLoader.classList.add("hide");

    setTimeout(() => {
      startupLoader.remove();
    }, 500);
  }

  window.addEventListener("load", () => {
    setTimeout(hideStartup, 1800);
  });
});
