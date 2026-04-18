export type ChatResponse = {
  request_id: string;
  thread_id: string;
  intent: string;
  response: {
    answer: string;
    sources: string[];
    last_updated: string[];
    disclaimer: string;
    policy_decision: string;
  };
  messages_in_thread: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080";

export async function createThread(): Promise<string> {
  const res = await fetch(`${API_BASE}/api/thread`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  if (!res.ok) {
    throw new Error(`Failed to create thread (${res.status})`);
  }
  const data = (await res.json()) as { thread_id: string };
  return data.thread_id;
}

export async function sendChat(threadId: string, query: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, query })
  });
  if (!res.ok) {
    throw new Error(`Chat request failed (${res.status})`);
  }
  return (await res.json()) as ChatResponse;
}

export async function loadThread(threadId: string) {
  const res = await fetch(`${API_BASE}/api/thread/${encodeURIComponent(threadId)}`);
  if (!res.ok) {
    throw new Error(`Thread load failed (${res.status})`);
  }
  return res.json() as Promise<{
    thread_id: string;
    messages: Array<{
      role: string;
      content: string;
      intent?: string;
      policy_decision?: string;
    }>;
  }>;
}
