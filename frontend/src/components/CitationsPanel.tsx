"use client";

import { useChatStore } from "@/lib/store";

export default function CitationsPanel() {
  const { selectedCitations, setSelectedCitations } = useChatStore();

  if (selectedCitations.length === 0) {
    return (
      <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900 text-sm">Sources</h3>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center">
            <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p className="text-sm text-gray-500">Click &quot;sources&quot; on a message to view cited documents</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900 text-sm">
          Sources ({selectedCitations.length})
        </h3>
        <button
          onClick={() => setSelectedCitations([])}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {selectedCitations.map((citation) => (
          <div
            key={citation.index}
            className="border border-gray-200 rounded-lg p-3 hover:border-brand-300 transition-colors"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 bg-brand-100 text-brand-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {citation.index}
                </span>
                <span className="text-sm font-medium text-gray-900 line-clamp-1">
                  {citation.doc_name}
                </span>
              </div>
            </div>

            {citation.page_number && (
              <p className="text-xs text-gray-500 mb-2">Page {citation.page_number}</p>
            )}

            <p className="text-xs text-gray-600 leading-relaxed line-clamp-6 bg-gray-50 rounded p-2">
              &quot;{citation.snippet}&quot;
            </p>

            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-gray-400">
                Score: {(citation.score * 100).toFixed(0)}%
              </span>
              {citation.source_url && (
                <a
                  href={citation.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-brand-600 hover:text-brand-700"
                >
                  Open source
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
