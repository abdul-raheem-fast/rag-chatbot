"use client";

import ReactMarkdown from "react-markdown";
import { useChatStore } from "@/lib/store";
import { chatApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";

interface Citation {
  index: number;
  doc_id: string;
  doc_name: string;
  page_number?: number;
  snippet: string;
  source_url?: string;
  score: number;
}

interface Props {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence?: string;
  feedback?: string;
  isStreaming?: boolean;
}

export default function ChatMessage({ id, role, content, citations, confidence, feedback, isStreaming }: Props) {
  const { token } = useAuthStore();
  const { setSelectedCitations, setFeedback } = useChatStore();

  const isUser = role === "user";

  async function handleFeedback(type: "thumbs_up" | "thumbs_down") {
    if (!token || feedback === type) return;
    try {
      await chatApi.feedback(token, id, type);
      setFeedback(id, type);
    } catch {}
  }

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
        </div>
      )}

      <div className={`max-w-[75%] ${isUser ? "order-first" : ""}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? "bg-brand-600 text-white rounded-br-md"
              : "bg-white border border-gray-200 rounded-bl-md"
          }`}
        >
          {isUser ? (
            <p className="text-sm leading-relaxed">{content}</p>
          ) : (
            <div className="prose-chat text-sm leading-relaxed text-gray-800">
              <ReactMarkdown>{content}</ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-brand-600 animate-pulse ml-1" />
              )}
            </div>
          )}
        </div>

        {/* Citations + Feedback (assistant only) */}
        {!isUser && !isStreaming && (
          <div className="mt-2 flex items-center gap-3 flex-wrap">
            {/* Confidence badge */}
            {confidence && (
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  confidence === "high"
                    ? "bg-green-100 text-green-700"
                    : confidence === "medium"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-red-100 text-red-700"
                }`}
              >
                {confidence} confidence
              </span>
            )}

            {/* Citations chips */}
            {citations && citations.length > 0 && (
              <button
                onClick={() => setSelectedCitations(citations)}
                className="text-xs text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                {citations.length} source{citations.length > 1 ? "s" : ""}
              </button>
            )}

            {/* Feedback buttons */}
            <div className="flex gap-1 ml-auto">
              <button
                onClick={() => handleFeedback("thumbs_up")}
                className={`p-1 rounded transition-colors ${
                  feedback === "thumbs_up" ? "text-green-600 bg-green-50" : "text-gray-400 hover:text-gray-600"
                }`}
              >
                <svg className="w-4 h-4" fill={feedback === "thumbs_up" ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6.633 10.5c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 012.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 00.322-1.672V3a.75.75 0 01.75-.75A2.25 2.25 0 0116.5 4.5c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 01-2.649 7.521c-.388.482-.987.729-1.605.729H14.23c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 00-1.423-.23H5.904M14.25 9h2.25M5.904 18.75c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 01-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 10.203 4.167 9.75 5 9.75h1.053c.472 0 .745.556.5.96a8.958 8.958 0 00-1.302 4.665c0 1.194.232 2.333.654 3.375z" />
                </svg>
              </button>
              <button
                onClick={() => handleFeedback("thumbs_down")}
                className={`p-1 rounded transition-colors ${
                  feedback === "thumbs_down" ? "text-red-600 bg-red-50" : "text-gray-400 hover:text-gray-600"
                }`}
              >
                <svg className="w-4 h-4" fill={feedback === "thumbs_down" ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7.5 15h2.25m8.024-9.75c.011.05.028.1.052.148.591 1.2.924 2.55.924 3.977a8.96 8.96 0 01-1.302 4.666c-.245.403.028.959.5.959h1.053c.832 0 1.612-.453 1.918-1.227C21.705 12.41 22 11.236 22 10c0-4.014-2.812-7.37-6.573-8.208A6.003 6.003 0 0014.25 1.5h-2.735c-.622 0-1.218.247-1.605.729A11.95 11.95 0 007.26 9.75H5.904c-.483 0-.964.078-1.423.23l-3.114 1.04a4.5 4.5 0 00-1.423.23H.75" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
