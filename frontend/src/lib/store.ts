import { create } from "zustand";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  org_id: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  login: (token, user) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("rag_token", token);
      localStorage.setItem("rag_user", JSON.stringify(user));
    }
    set({ token, user, isAuthenticated: true });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("rag_token");
      localStorage.removeItem("rag_user");
    }
    set({ token: null, user: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("rag_token");
    const userStr = localStorage.getItem("rag_user");
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        set({ token, user, isAuthenticated: true });
      } catch {
        set({ token: null, user: null, isAuthenticated: false });
      }
    }
  },
}));

interface Citation {
  index: number;
  doc_id: string;
  doc_name: string;
  page_number?: number;
  snippet: string;
  source_url?: string;
  score: number;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence?: string;
  feedback?: string;
  isStreaming?: boolean;
}

interface ChatState {
  messages: Message[];
  conversationId: string | null;
  isLoading: boolean;
  selectedCitations: Citation[];
  addMessage: (msg: Message) => void;
  updateLastAssistant: (content: string) => void;
  setConversationId: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setSelectedCitations: (citations: Citation[]) => void;
  clearChat: () => void;
  setFeedback: (messageId: string, feedback: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  conversationId: null,
  isLoading: false,
  selectedCitations: [],

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  updateLastAssistant: (content) =>
    set((state) => {
      const msgs = [...state.messages];
      const lastIdx = msgs.length - 1;
      if (lastIdx >= 0 && msgs[lastIdx].role === "assistant") {
        msgs[lastIdx] = { ...msgs[lastIdx], content };
      }
      return { messages: msgs };
    }),

  setConversationId: (id) => set({ conversationId: id }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSelectedCitations: (citations) => set({ selectedCitations: citations }),
  clearChat: () =>
    set({ messages: [], conversationId: null, selectedCitations: [] }),

  setFeedback: (messageId, feedback) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId ? { ...m, feedback } : m
      ),
    })),
}));
