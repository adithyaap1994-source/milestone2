const API_BASE = "http://localhost:8080";

const statusEl = document.getElementById("status");
const threadInput = document.getElementById("threadId");
const queryInput = document.getElementById("query");
const responseBox = document.getElementById("responseBox");
const threadBox = document.getElementById("threadBox");

const createThreadBtn = document.getElementById("createThreadBtn");
const sendBtn = document.getElementById("sendBtn");
const loadThreadBtn = document.getElementById("loadThreadBtn");
const clearBtn = document.getElementById("clearBtn");

function setStatus(message) {
  statusEl.textContent = message;
}

async function createThread() {
  setStatus("Creating session...");
  try {
    const res = await fetch(`${API_BASE}/api/thread`, { method: "POST" });
    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.error || `HTTP ${res.status}`);
    }
    threadInput.value = payload.thread_id;
    setStatus("Session created");
  } catch (error) {
    setStatus(`Create session failed: ${error}`);
  }
}

async function sendMessage() {
  const threadId = threadInput.value.trim();
  const query = queryInput.value.trim();
  if (!threadId || !query) {
    setStatus("Thread ID and query are required");
    return;
  }
  setStatus("Sending query...");
  responseBox.textContent = "Loading...";
  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread_id: threadId, query })
    });
    const payload = await res.json();
    responseBox.textContent = JSON.stringify(payload, null, 2);
    setStatus(res.ok ? "Query successful" : `Query failed (${res.status})`);
  } catch (error) {
    responseBox.textContent = `Request failed: ${error}`;
    setStatus("Network error");
  }
}

async function loadThread() {
  const threadId = threadInput.value.trim();
  if (!threadId) {
    setStatus("Thread ID is required");
    return;
  }
  setStatus("Loading thread...");
  threadBox.textContent = "Loading...";
  try {
    const res = await fetch(`${API_BASE}/api/thread/${encodeURIComponent(threadId)}`);
    const payload = await res.json();
    threadBox.textContent = JSON.stringify(payload, null, 2);
    setStatus(res.ok ? "Thread loaded" : `Thread load failed (${res.status})`);
  } catch (error) {
    threadBox.textContent = `Load failed: ${error}`;
    setStatus("Network error");
  }
}

function clearOutput() {
  responseBox.textContent = "No response yet.";
  threadBox.textContent = "No thread loaded.";
  setStatus("Cleared");
}

createThreadBtn.addEventListener("click", createThread);
sendBtn.addEventListener("click", sendMessage);
loadThreadBtn.addEventListener("click", loadThread);
clearBtn.addEventListener("click", clearOutput);
