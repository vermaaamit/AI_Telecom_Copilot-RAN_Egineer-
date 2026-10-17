'use client'

import { ChangeEvent, Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { askQuestion, ChatResponse, DatasetAnalysis, listDatasets, uploadDataset } from '../../lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content?: string
  response?: ChatResponse
  timestamp: string
}

const SUGGESTIONS = [
  'Which cells are performing badly?',
  'Why is CELL102 performing badly?',
  'Compare CELL102 and CELL105.',
  'Which cells have SINR below 5?',
  'Which sites are congested?',
  'Show me anomalous cells.',
  'Give me a KPI summary.',
]

function ChatComponent() {
  const searchParams = useSearchParams()
  const initialQuestion = searchParams?.get('question') || ''
  const initialDataset = searchParams?.get('dataset') || ''

  const [datasets, setDatasets] = useState<DatasetAnalysis[]>([])
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDatasets()
  }, [])

  async function loadDatasets() {
    try {
      const list = await listDatasets()
      setDatasets(list)
      if (list.length > 0) {
        const activeId = initialDataset && list.some(d => d.id === initialDataset) ? initialDataset : list[0].id
        setSelectedDatasetId(activeId)
        if (initialQuestion) {
          sendQuery(initialQuestion, activeId)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to API.')
    }
  }

  async function sendQuery(queryText: string, datasetIdOverride?: string) {
    const dsId = datasetIdOverride || selectedDatasetId
    if (!queryText.trim() || !dsId) return

    const userMsg: Message = {
      id: String(Date.now()),
      role: 'user',
      content: queryText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setError('')

    try {
      const res = await askQuestion(dsId, queryText.trim())
      const assistantMsg: Message = {
        id: String(Date.now() + 1),
        role: 'assistant',
        response: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chat query failed.')
    } finally {
      setLoading(false)
    }
  }

  async function handleFileUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const uploaded = await uploadDataset(file)
      setDatasets(prev => [uploaded, ...prev])
      setSelectedDatasetId(uploaded.id)
      sendQuery('Give me a KPI summary.', uploaded.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8 flex flex-col h-[calc(100vh-65px)]">
      {/* Chat Header & Dataset Selector */}
      <div className="mb-4 flex flex-col justify-between gap-3 border-b border-slate-800 pb-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <span>RAN Engineering Copilot</span>
            <span className="rounded bg-teal-950 px-2 py-0.5 text-[10px] font-mono font-semibold text-teal-300 border border-teal-800">
              Grounded AI
            </span>
          </h1>
          <p className="text-xs text-slate-400">
            Natural language diagnostics strictly backed by deterministic analytics tools and safety guardrails.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Dataset:</span>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-teal-400"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.cell_count} cells)
                </option>
              ))}
              {datasets.length === 0 && <option value="">No datasets available</option>}
            </select>
          </div>

          <label className="cursor-pointer rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700">
            {uploading ? 'Analyzing…' : '+ Upload CSV'}
            <input className="hidden" type="file" accept=".csv,text/csv" onChange={handleFileUpload} disabled={uploading} />
          </label>
        </div>
      </div>

      {error && (
        <div className="mb-3 rounded-lg border border-red-900 bg-red-950/60 p-3 text-xs text-red-200">
          <strong>Error: </strong>{error}
        </div>
      )}

      {/* Conversation Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
        {messages.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center text-slate-400 my-auto">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-teal-950 border border-teal-800 mb-3">
              <span className="text-teal-400 text-lg font-mono font-bold">AI</span>
            </div>
            <h3 className="text-base font-semibold text-slate-200">Telecom Copilot Ready</h3>
            <p className="mx-auto mt-1 max-w-md text-xs text-slate-400">
              Ask natural language questions about cell health scores, root causes, KPI thresholds, or cell comparisons.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className="flex items-center gap-2 mb-1 px-1">
              <span className="font-mono text-[10px] text-slate-500">{msg.role === 'user' ? 'You' : 'Copilot'}</span>
              <span className="text-[10px] text-slate-600">{msg.timestamp}</span>
            </div>

            {msg.role === 'user' ? (
              <div className="rounded-2xl rounded-tr-sm bg-teal-600 px-4 py-2.5 text-sm text-slate-950 font-medium max-w-xl">
                {msg.content}
              </div>
            ) : (
              <div className="rounded-2xl rounded-tl-sm border border-slate-800 bg-slate-900 p-5 text-sm max-w-3xl w-full">
                {msg.response && (
                  <div>
                    {/* Execution Meta Pill */}
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2 text-[11px] text-slate-400 font-mono">
                      <div className="flex items-center gap-2">
                        <span className="rounded bg-slate-950 px-2 py-0.5 text-teal-400 border border-slate-800">
                          Tool: {msg.response.tool_called}
                        </span>
                        <span className="rounded bg-slate-950 px-2 py-0.5 text-slate-400 border border-slate-800">
                          Mode: {msg.response.mode}
                        </span>
                      </div>
                      <span className="inline-flex items-center gap-1 text-teal-400">
                        <span className="h-1.5 w-1.5 rounded-full bg-teal-400"></span>
                        Grounded: Verified
                      </span>
                    </div>

                    {/* Formatted Answer */}
                    <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-200">
                      {msg.response.answer}
                    </pre>

                    {/* Quick drill-down links if cells mentioned */}
                    {Array.isArray(msg.response.evidence?.items) && msg.response.evidence.items.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-800/80">
                        <p className="text-[11px] text-slate-400 font-medium mb-2">Affected Cell Drill-Downs:</p>
                        <div className="flex flex-wrap gap-2">
                          {(msg.response.evidence.items as Array<{ cell_id: string; health_score: number }>).slice(0, 5).map((item) => (
                            <Link
                              key={item.cell_id}
                              href={`/cells/${encodeURIComponent(item.cell_id)}`}
                              className="rounded bg-slate-950 px-2.5 py-1 text-xs font-mono text-teal-300 border border-slate-800 hover:border-teal-500 transition"
                            >
                              {item.cell_id} ({item.health_score}/100) →
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs text-slate-400 p-2">
            <span className="h-2 w-2 rounded-full bg-teal-400 animate-pulse"></span>
            Executing controlled analytics tool and verifying grounding…
          </div>
        )}
      </div>

      {/* Suggestions */}
      <div className="mb-3 flex flex-wrap gap-1.5">
        {SUGGESTIONS.map((sug) => (
          <button
            key={sug}
            onClick={() => sendQuery(sug)}
            disabled={loading}
            className="rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-xs text-slate-300 hover:border-teal-500 hover:text-teal-200 transition disabled:opacity-50"
          >
            {sug}
          </button>
        ))}
      </div>

      {/* Query Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          sendQuery(input)
        }}
        className="flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question (e.g. Which cells are performing badly? Why is CELL102 critical? Compare CELL102 and CELL105)..."
          className="flex-1 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-teal-400 focus:outline-none"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim() || !selectedDatasetId}
          className="rounded-xl bg-teal-400 px-6 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-teal-300 disabled:opacity-50 shadow-md shadow-teal-500/10"
        >
          {loading ? 'Analyzing…' : 'Send'}
        </button>
      </form>
    </main>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-slate-400">Loading Copilot Chat…</div>}>
      <ChatComponent />
    </Suspense>
  )
}

