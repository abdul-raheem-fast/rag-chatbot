"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore, useChatStore } from "@/lib/store";
import { chatApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import CitationsPanel from "@/components/CitationsPanel";

export default function ChatPage() {
  const router = useRouter();
  const { token, isAuthenticated, loadFromStorage } = useAuthStore();
  const {
    messages, conversationId, isLoading,
    addMessage, updateLastAssistant, setConversationId, setLoading, setSelectedCitations,
  } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  useEffect(() => {
    if (!isAuthenticated && typeof window !== "undefined") {
      const stored = localStorage.getItem("rag_token");
      if (!stored) router.push("/login");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(message: string) {
    if (!token) return;

    const userMsgId = crypto.randomUUID();
    addMessage({ id: userMsgId, role: "user", content: message });
    setLoading(true);

    const assistantMsgId = crypto.randomUUID();
    addMessage({
      id: assistantMsgId,
      role: "assistant",
      content: "",
      isStreaming: true,
    });

    try {
      let fullContent = "";
      for await (const chunk of chatApi.stream(token, message, conversationId || undefined)) {
        if (chunk.type === "content") {
          fullContent += chunk.content;
          updateLastAssistant(fullContent);
        } else if (chunk.type === "done") {
          // Final update with citations
          useChatStore.setState((state) => {
            const msgs = [...state.messages];
            const lastIdx = msgs.length - 1;
            if (lastIdx >= 0 && msgs[lastIdx].role === "assistant") {
              msgs[lastIdx] = {
                ...msgs[lastIdx],
                content: fullContent,
                citations: chunk.citations || [],
                confidence: chunk.citations?.length > 0 ? "high" : "low",
                isStreaming: false,
              };
            }
            return { messages: msgs };
          });
        }
      }
    } catch (err: any) {
      updateLastAssistant("Sorry, an error occurred: " + (err.message || "Unknown error"));
      useChatStore.setState((state) => {
        const msgs = [...state.messages];
        const lastIdx = msgs.length - 1;
        if (lastIdx >= 0) msgs[lastIdx] = { ...msgs[lastIdx], isStreaming: false };
        return { messages: msgs };
      });
    } finally {
      setLoading(false);
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 bg-brand-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">How can I help you?</h2>
                <p className="text-gray-500 text-sm">
                  Ask me anything about your organization&apos;s documents. I&apos;ll provide answers with citations to the source material.
                </p>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto p-6 space-y-6">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} {...msg} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <ChatInput onSend={handleSend} disabled={isLoading} />
      </div>

      <CitationsPanel />
    </div>
  );
}
