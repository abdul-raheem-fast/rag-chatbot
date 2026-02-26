"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { adminApi, authApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";

export default function SettingsPage() {
  const router = useRouter();
  const { token, user, loadFromStorage } = useAuthStore();
  const [org, setOrg] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-4o-mini");
  const [dailyBudget, setDailyBudget] = useState(500000);
  const [monthlyBudget, setMonthlyBudget] = useState(10000000);

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  useEffect(() => {
    if (user && user.role !== "admin") router.push("/chat");
  }, [user, router]);

  useEffect(() => {
    if (!token) return;
    authApi.org(token).then((data) => {
      setOrg(data);
      setProvider(data.default_llm_provider);
      setModel(data.default_llm_model);
      setDailyBudget(data.daily_token_budget);
      setMonthlyBudget(data.monthly_token_budget);
    }).catch(console.error);

    adminApi.users(token).then(setUsers).catch(console.error);
  }, [token]);

  async function handleSave() {
    if (!token) return;
    setSaving(true);
    setMessage("");
    try {
      await adminApi.updateSettings(token, {
        default_llm_provider: provider,
        default_llm_model: model,
        daily_token_budget: dailyBudget,
        monthly_token_budget: monthlyBudget,
      });
      setMessage("Settings saved successfully!");
    } catch (err: any) {
      setMessage("Error: " + err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleResetTokens() {
    if (!token) return;
    try {
      await adminApi.resetTokens(token);
      setMessage("Daily token usage reset!");
    } catch (err: any) {
      setMessage("Error: " + err.message);
    }
  }

  async function handleRoleChange(userId: string, newRole: string) {
    if (!token) return;
    try {
      await adminApi.updateUserRole(token, userId, newRole);
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, role: newRole } : u)));
    } catch (err: any) {
      setMessage("Error: " + err.message);
    }
  }

  const modelOptions: Record<string, string[]> = {
    openai: ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    anthropic: ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    google: ["gemini-1.5-flash", "gemini-1.5-pro"],
  };

  if (!user || user.role !== "admin") return null;

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-4xl mx-auto p-8">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-500 mt-1">Configure LLM provider, budgets, and team</p>
          </div>

          {message && (
            <div className={`px-4 py-3 rounded-lg text-sm mb-6 ${message.startsWith("Error") ? "bg-red-50 text-red-600" : "bg-green-50 text-green-600"}`}>
              {message}
            </div>
          )}

          {/* LLM Settings */}
          <div className="card p-6 mb-6">
            <h2 className="font-semibold text-gray-900 mb-4">LLM Configuration</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                <select
                  value={provider}
                  onChange={(e) => {
                    setProvider(e.target.value);
                    setModel(modelOptions[e.target.value]?.[0] || "");
                  }}
                  className="input-field"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic (Claude)</option>
                  <option value="google">Google (Gemini)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="input-field"
                >
                  {(modelOptions[provider] || []).map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Token Budgets */}
          <div className="card p-6 mb-6">
            <h2 className="font-semibold text-gray-900 mb-4">Token Budgets</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Daily Budget</label>
                <input
                  type="number"
                  value={dailyBudget}
                  onChange={(e) => setDailyBudget(Number(e.target.value))}
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Budget</label>
                <input
                  type="number"
                  value={monthlyBudget}
                  onChange={(e) => setMonthlyBudget(Number(e.target.value))}
                  className="input-field"
                />
              </div>
            </div>
            <div className="mt-4 flex gap-3">
              <button onClick={handleSave} disabled={saving} className="btn-primary">
                {saving ? "Saving..." : "Save Settings"}
              </button>
              <button onClick={handleResetTokens} className="btn-secondary">
                Reset Daily Tokens
              </button>
            </div>
          </div>

          {/* Team Management */}
          <div className="card p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Team Members ({users.length})</h2>
            {users.length === 0 ? (
              <p className="text-gray-500 text-sm">No users found.</p>
            ) : (
              <div className="divide-y divide-gray-200">
                {users.map((u) => (
                  <div key={u.id} className="py-3 flex items-center gap-4">
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-sm font-medium text-gray-600">
                      {u.full_name?.charAt(0)?.toUpperCase() || "?"}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{u.full_name}</p>
                      <p className="text-xs text-gray-500">{u.email}</p>
                    </div>
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      className="text-sm border border-gray-300 rounded-lg px-2 py-1"
                    >
                      <option value="admin">Admin</option>
                      <option value="member">Member</option>
                      <option value="viewer">Viewer</option>
                    </select>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
