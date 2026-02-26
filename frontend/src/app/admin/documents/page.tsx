"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { docsApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";

interface Document {
  id: string;
  name: string;
  source_type: string;
  source_url: string | null;
  chunk_count: number;
  status: string;
  error_message: string | null;
  created_at: string;
}

export default function DocumentsPage() {
  const router = useRouter();
  const { token, user, loadFromStorage } = useAuthStore();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  useEffect(() => {
    if (user && user.role !== "admin") router.push("/chat");
  }, [user, router]);

  const fetchDocs = useCallback(async () => {
    if (!token) return;
    try {
      const data = await docsApi.list(token);
      setDocuments(data.documents || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    setUploading(true);
    setError("");
    try {
      await docsApi.upload(token, file);
      await fetchDocs();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleWebsiteIngest() {
    if (!websiteUrl || !token) return;
    setUploading(true);
    setError("");
    try {
      await docsApi.ingestWebsite(token, websiteUrl);
      setWebsiteUrl("");
      await fetchDocs();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(docId: string) {
    if (!token || !confirm("Delete this document and all its chunks?")) return;
    try {
      await docsApi.delete(token, docId);
      await fetchDocs();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function handleReindex(docId: string) {
    if (!token) return;
    try {
      await docsApi.reindex(token, docId);
      await fetchDocs();
    } catch (err: any) {
      setError(err.message);
    }
  }

  if (!user || user.role !== "admin") return null;

  const statusColors: Record<string, string> = {
    ready: "bg-green-100 text-green-700",
    processing: "bg-yellow-100 text-yellow-700",
    failed: "bg-red-100 text-red-700",
  };

  const typeIcons: Record<string, string> = {
    pdf: "PDF",
    csv: "CSV",
    website: "WEB",
    gdoc: "DOC",
    notion: "NTN",
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-6xl mx-auto p-8">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Document Management</h1>
            <p className="text-gray-500 mt-1">Upload and manage knowledge base documents</p>
          </div>

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm mb-6">
              {error}
              <button onClick={() => setError("")} className="ml-2 font-medium underline">Dismiss</button>
            </div>
          )}

          {/* Upload section */}
          <div className="card p-6 mb-8">
            <h2 className="font-semibold text-gray-900 mb-4">Add Documents</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* File upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Upload File</label>
                <label className="flex items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-brand-400 hover:bg-brand-50 transition-colors">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                    <p className="text-sm text-gray-500">
                      {uploading ? "Uploading..." : "Click to upload PDF, CSV, TXT"}
                    </p>
                  </div>
                  <input
                    type="file"
                    accept=".pdf,.csv,.txt,.docx,.xlsx"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="hidden"
                  />
                </label>
              </div>

              {/* Website URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Ingest Website</label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    value={websiteUrl}
                    onChange={(e) => setWebsiteUrl(e.target.value)}
                    placeholder="https://example.com/page"
                    className="input-field flex-1"
                  />
                  <button
                    onClick={handleWebsiteIngest}
                    disabled={uploading || !websiteUrl}
                    className="btn-primary whitespace-nowrap"
                  >
                    {uploading ? "..." : "Ingest"}
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-2">Scrapes and indexes the page content</p>
              </div>
            </div>
          </div>

          {/* Documents list */}
          <div className="card">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900">Documents ({documents.length})</h2>
            </div>

            {loading ? (
              <div className="p-6 text-center text-gray-400">Loading documents...</div>
            ) : documents.length === 0 ? (
              <div className="p-12 text-center">
                <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <p className="text-gray-500">No documents yet. Upload your first document above.</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {documents.map((doc) => (
                  <div key={doc.id} className="px-6 py-4 flex items-center gap-4 hover:bg-gray-50">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-xs font-bold text-gray-500 flex-shrink-0">
                      {typeIcons[doc.source_type] || "DOC"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{doc.name}</p>
                      <p className="text-xs text-gray-500">
                        {doc.chunk_count} chunks &middot; {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                      {doc.error_message && (
                        <p className="text-xs text-red-500 mt-1">{doc.error_message}</p>
                      )}
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColors[doc.status] || "bg-gray-100 text-gray-600"}`}>
                      {doc.status}
                    </span>
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleReindex(doc.id)}
                        className="text-xs text-gray-500 hover:text-brand-600 px-2 py-1"
                        title="Re-index"
                      >
                        Re-index
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="text-xs text-gray-500 hover:text-red-600 px-2 py-1"
                        title="Delete"
                      >
                        Delete
                      </button>
                    </div>
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
