const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  token?: string;
}

async function apiFetch<T = any>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { token, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(customHeaders as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${endpoint}`, { headers, ...rest });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || `API error: ${res.status}`);
  }

  return res.json();
}

// Auth
export const authApi = {
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    org_name?: string;
  }) => apiFetch("/api/auth/register", { method: "POST", body: JSON.stringify(data) }),

  login: (data: { email: string; password: string }) =>
    apiFetch("/api/auth/login", { method: "POST", body: JSON.stringify(data) }),

  me: (token: string) => apiFetch("/api/auth/me", { token }),

  org: (token: string) => apiFetch("/api/auth/org", { token }),
};

// Chat
export const chatApi = {
  send: (token: string, message: string, conversationId?: string) =>
    apiFetch("/api/chat", {
      method: "POST",
      token,
      body: JSON.stringify({
        message,
        conversation_id: conversationId || null,
      }),
    }),

  stream: async function* (token: string, message: string, conversationId?: string) {
    const res = await fetch(`${API_URL}/api/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId || null,
      }),
    });

    if (!res.ok) throw new Error(`Stream error: ${res.status}`);
    if (!res.body) throw new Error("No response body");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            yield JSON.parse(line.slice(6));
          } catch {}
        }
      }
    }
  },

  conversations: (token: string) =>
    apiFetch("/api/chat/conversations", { token }),

  conversation: (token: string, id: string) =>
    apiFetch(`/api/chat/conversations/${id}`, { token }),

  feedback: (token: string, messageId: string, feedback: "thumbs_up" | "thumbs_down") =>
    apiFetch("/api/chat/feedback", {
      method: "POST",
      token,
      body: JSON.stringify({ message_id: messageId, feedback }),
    }),
};

// Documents
export const docsApi = {
  list: (token: string) => apiFetch("/api/documents", { token }),

  upload: async (token: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_URL}/api/documents/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json();
  },

  ingestWebsite: (token: string, url: string, name?: string) =>
    apiFetch("/api/documents/ingest-website", {
      method: "POST",
      token,
      body: JSON.stringify({ url, name }),
    }),

  ingestGDoc: (token: string, docId: string, name?: string) =>
    apiFetch("/api/documents/ingest-gdoc", {
      method: "POST",
      token,
      body: JSON.stringify({ doc_id: docId, name }),
    }),

  ingestNotion: (token: string, pageId: string, name?: string) =>
    apiFetch("/api/documents/ingest-notion", {
      method: "POST",
      token,
      body: JSON.stringify({ page_id: pageId, name }),
    }),

  delete: (token: string, docId: string) =>
    apiFetch(`/api/documents/${docId}`, { method: "DELETE", token }),

  reindex: (token: string, docId: string) =>
    apiFetch(`/api/documents/${docId}/reindex`, { method: "POST", token }),
};

// Admin
export const adminApi = {
  analytics: (token: string) => apiFetch("/api/admin/analytics", { token }),

  updateSettings: (
    token: string,
    settings: {
      default_llm_provider?: string;
      default_llm_model?: string;
      daily_token_budget?: number;
      monthly_token_budget?: number;
    }
  ) =>
    apiFetch("/api/admin/settings", {
      method: "PUT",
      token,
      body: JSON.stringify(settings),
    }),

  users: (token: string) => apiFetch("/api/admin/users", { token }),

  updateUserRole: (token: string, userId: string, role: string) =>
    apiFetch(`/api/admin/users/${userId}/role`, {
      method: "PUT",
      token,
      body: JSON.stringify({ role }),
    }),

  resetTokens: (token: string) =>
    apiFetch("/api/admin/reset-token-usage", { method: "POST", token }),
};
