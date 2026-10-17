'use client'

import { useState, useEffect } from 'react'
import { searchKnowledge, KnowledgeDocItem } from '../../lib/api'

export default function KnowledgePage() {
  const [query, setQuery] = useState('interference')
  const [docs, setDocs] = useState<KnowledgeDocItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSearch(searchQ: string) {
    if (!searchQ.trim() || searchQ.trim().length < 2) return
    setLoading(true)
    setError('')
    try {
      const res = await searchKnowledge(searchQ, 6)
      setDocs(res.documents || [])
    } catch (err: any) {
      setError(err.message || 'Failed to search knowledge base.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    handleSearch('interference')
  }, [])

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      <div className="mb-8 border-b border-slate-800 pb-6">
        <span className="font-mono text-xs uppercase tracking-widest text-teal-400">RAG Knowledge Base</span>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100 mt-1">
          3GPP & O-RAN Engineering Standards
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Curated telecom standards, specifications, and troubleshooting methodologies.
        </p>
      </div>

      <div className="mb-6 flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch(query)}
          placeholder="Search topics (e.g. interference, beamforming, PRB congestion, handover, eCPRI)..."
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-teal-500"
        />
        <button
          onClick={() => handleSearch(query)}
          className="rounded-lg bg-teal-500 px-5 py-2.5 text-sm font-semibold text-slate-950 hover:bg-teal-400 transition"
        >
          Search
        </button>
      </div>

      <div className="mb-8 flex flex-wrap gap-2 text-xs">
        <span className="text-slate-500 py-1 font-mono">Suggested:</span>
        {['Interference & RSRP', 'Massive MIMO Beamforming', 'O-RAN Non-RT RIC', 'Handover Ping-Pong', 'PRB Congestion', 'eCPRI Fronthaul'].map((tag) => (
          <button
            key={tag}
            onClick={() => {
              setQuery(tag)
              handleSearch(tag)
            }}
            className="rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-slate-300 hover:border-slate-700 hover:text-teal-300 transition"
          >
            {tag}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-rose-900 bg-rose-950/60 p-4 text-sm text-rose-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-12 text-center text-slate-400">
          Searching telecom specifications...
        </div>
      ) : docs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 p-16 text-center text-slate-500">
          No standards matched your query. Try broadening keywords.
        </div>
      ) : (
        <div className="space-y-4">
          {docs.map((doc) => (
            <div
              key={doc.id}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 transition hover:border-slate-700"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-xs font-bold text-teal-400">{doc.id}</span>
                  <span className="rounded bg-teal-950/80 px-2.5 py-0.5 text-[10px] font-bold text-teal-300 border border-teal-800">
                    {doc.domain}
                  </span>
                  <span className="text-xs text-slate-400 font-medium">{doc.source}</span>
                </div>
                <span className="text-[11px] font-mono text-slate-500">
                  Relevance: {doc.relevance_score}
                </span>
              </div>

              <h2 className="mt-3 text-base font-semibold text-slate-100">{doc.title}</h2>
              <p className="mt-2 text-sm text-slate-300 leading-relaxed">{doc.content}</p>

              {doc.keywords.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1.5 pt-3 border-t border-slate-800/60">
                  {doc.keywords.map((kw) => (
                    <span
                      key={kw}
                      className="rounded bg-slate-800/60 px-2 py-0.5 font-mono text-[10px] text-slate-400"
                    >
                      #{kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </main>
  )
}

