"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { adminApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";

interface Analytics {
  total_documents: number;
  total_chunks: number;
  total_conversations: number;
  total_messages: number;
  messages_today: number;
  avg_latency_ms: number | null;
  thumbs_up_count: number;
  thumbs_down_count: number;
  tokens_used_today: number;
  tokens_used_month: number;
  daily_token_budget: number;
  monthly_token_budget: number;
  top_unanswered: string[];
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="card p-5">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const { token, user, loadFromStorage } = useAuthStore();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  useEffect(() => {
    if (user && user.role !== "admin") router.push("/chat");
  }, [user, router]);

  useEffect(() => {
    if (!token) return;
    adminApi.analytics(token).then(setAnalytics).catch(console.error).finally(() => setLoading(false));
  }, [token]);

  if (!user || user.role !== "admin") return null;

  const satisfactionRate = analytics
    ? analytics.thumbs_up_count + analytics.thumbs_down_count > 0
      ? (analytics.thumbs_up_count / (analytics.thumbs_up_count + analytics.thumbs_down_count) * 100).toFixed(0) + "%"
      : "N/A"
    : "...";

  const tokenUsagePercent = analytics
    ? ((analytics.tokens_used_today / analytics.daily_token_budget) * 100).toFixed(0)
    : "0";

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-6xl mx-auto p-8">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
            <p className="text-gray-500 mt-1">Overview of your RAG chatbot usage</p>
          </div>

          {loading ? (
            <div className="animate-pulse space-y-4">
              <div className="grid grid-cols-4 gap-4">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="card p-5 h-24 bg-gray-100" />
                ))}
              </div>
            </div>
          ) : analytics ? (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <StatCard label="Documents" value={analytics.total_documents} sub={`${analytics.total_chunks} chunks`} />
                <StatCard label="Conversations" value={analytics.total_conversations} />
                <StatCard label="Messages Today" value={analytics.messages_today} sub={`${analytics.total_messages} total`} />
                <StatCard label="Avg Latency" value={analytics.avg_latency_ms ? `${analytics.avg_latency_ms}ms` : "N/A"} />
                <StatCard label="Satisfaction" value={satisfactionRate} sub={`${analytics.thumbs_up_count} up / ${analytics.thumbs_down_count} down`} />
                <StatCard label="Tokens Today" value={analytics.tokens_used_today.toLocaleString()} sub={`Budget: ${analytics.daily_token_budget.toLocaleString()}`} />
                <StatCard label="Tokens This Month" value={analytics.tokens_used_month.toLocaleString()} sub={`Budget: ${analytics.monthly_token_budget.toLocaleString()}`} />
                <StatCard label="Budget Usage" value={`${tokenUsagePercent}%`} sub="Daily token budget" />
              </div>

              {/* Token usage bar */}
              <div className="card p-5 mb-8">
                <h3 className="font-semibold text-gray-900 mb-3">Daily Token Budget</h3>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      Number(tokenUsagePercent) > 80 ? "bg-red-500" :
                      Number(tokenUsagePercent) > 50 ? "bg-yellow-500" : "bg-green-500"
                    }`}
                    style={{ width: `${Math.min(Number(tokenUsagePercent), 100)}%` }}
                  />
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  {analytics.tokens_used_today.toLocaleString()} / {analytics.daily_token_budget.toLocaleString()} tokens used
                </p>
              </div>

              {/* Unanswered questions */}
              {analytics.top_unanswered.length > 0 && (
                <div className="card p-5">
                  <h3 className="font-semibold text-gray-900 mb-3">Recent Unanswered Questions</h3>
                  <ul className="space-y-2">
                    {analytics.top_unanswered.map((q, i) => (
                      <li key={i} className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
                        {q.length > 200 ? q.slice(0, 200) + "..." : q}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <p className="text-gray-500">Failed to load analytics.</p>
          )}
        </div>
      </main>
    </div>
  );
}
