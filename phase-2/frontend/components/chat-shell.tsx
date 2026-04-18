"use client";

import { useMemo, useState } from "react";
import { createThread, loadThread, sendChat } from "../lib/api";

type Session = {
  id: string;
  label: string;
};

export default function ChatShell() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [query, setQuery] = useState("");
  const [responseJson, setResponseJson] = useState("No response yet.");
  const [threadJson, setThreadJson] = useState("No messages loaded.");
  const [status, setStatus] = useState("Create a session to begin.");
  const [isLoading, setIsLoading] = useState(false);

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId),
    [sessions, activeSessionId]
  );

  async function handleCreateSession() {
    setIsLoading(true);
    setStatus("Creating chat session...");
    try {
      const threadId = await createThread();
      const newSession = { id: threadId, label: `Session ${sessions.length + 1}` };
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(threadId);
      setStatus(`Active session: ${newSession.label}`);
      setThreadJson("No messages loaded.");
      setResponseJson("No response yet.");
    } catch (error) {
      setStatus(`Failed to create session: ${String(error)}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSendMessage() {
    if (!activeSessionId || !query.trim()) {
      setStatus("Select a session and enter a query.");
      return;
    }
    setIsLoading(true);
    setStatus("Sending message...");
    try {
      const data = await sendChat(activeSessionId, query.trim());
      setResponseJson(JSON.stringify(data, null, 2));
      setStatus("Response received.");
    } catch (error) {
      setStatus(`Chat error: ${String(error)}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleLoadThread() {
    if (!activeSessionId) {
      setStatus("Choose a session first.");
      return;
    }
    setIsLoading(true);
    setStatus("Loading session history...");
    try {
      const data = await loadThread(activeSessionId);
      setThreadJson(JSON.stringify(data, null, 2));
      setStatus("Session history loaded.");
    } catch (error) {
      setStatus(`Load error: ${String(error)}`);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page">
      <header className="header">
        <h1>Mutual Fund FAQ Assistant</h1>
        <p>Phase 2 dark theme frontend (isolated multi-session testing)</p>
        <div className="badge">{status}</div>
      </header>

      <section className="panel row">
        <button onClick={handleCreateSession} disabled={isLoading}>
          + Create Session
        </button>
        <div className="sessions">
          {sessions.length === 0 && <span className="muted">No sessions yet</span>}
          {sessions.map((session) => (
            <button
              key={session.id}
              className={session.id === activeSessionId ? "session active" : "session"}
              onClick={() => setActiveSessionId(session.id)}
            >
              {session.label}
            </button>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="label">Active Thread ID</div>
        <div className="thread-id">{activeSession?.id || "No active session selected"}</div>
      </section>

      <section className="panel">
        <div className="label">Ask Query</div>
        <textarea
          rows={4}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask a factual mutual fund query"
        />
        <div className="row">
          <button onClick={handleSendMessage} disabled={isLoading}>
            Send
          </button>
          <button className="secondary" onClick={handleLoadThread} disabled={isLoading}>
            Load Session Messages
          </button>
        </div>
      </section>

      <section className="panel">
        <h2>Response</h2>
        <pre>{responseJson}</pre>
      </section>

      <section className="panel">
        <h2>Session Messages</h2>
        <pre>{threadJson}</pre>
      </section>
    </main>
  );
}
