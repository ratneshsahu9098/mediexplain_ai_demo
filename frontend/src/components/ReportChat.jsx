import {
  AlertCircle,
  Languages,
  Loader2,
  MessageCircle,
  Send,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'

import { api } from '../services/api.js'
import ExplanationText from './ExplanationText.jsx'

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'हिन्दी (Hindi)' },
  { value: 'hinglish', label: 'Hinglish' },
]

function sourceLabel(message) {
  if (!message.source || message.source === 'template') return 'Offline template'
  return `AI · ${message.model || message.source}`
}

export default function ReportChat({ reportId, language, onLanguageChange, results }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)

  const resultNames = useMemo(
    () => Object.fromEntries(results.map((result) => [result.id, result.test_name])),
    [results],
  )

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    setMessages([])

    api
      .getChat(reportId)
      .then((data) => {
        if (active) setMessages(data.messages || [])
      })
      .catch((err) => {
        if (active) setError(err.message || 'Could not load the conversation.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reportId])

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'nearest' })
  }, [messages, sending])

  async function send(text) {
    const question = text.trim()
    if (!question || sending) return

    const optimistic = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: question,
      created_at: new Date().toISOString(),
    }
    setMessages((current) => [...current, optimistic])
    setInput('')
    setError('')
    setSending(true)

    try {
      const data = await api.sendChat(reportId, question, language)
      setMessages((current) => [...current, data.reply])
    } catch (err) {
      setMessages((current) => current.filter((message) => message.id !== optimistic.id))
      setInput(question)
      setError(err.message || 'Could not send your question.')
    } finally {
      setSending(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    send(input)
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      send(input)
    }
  }

  async function clearChat() {
    const confirmed = window.confirm('Clear this conversation? This cannot be undone.')
    if (!confirmed) return

    setClearing(true)
    setError('')
    try {
      await api.clearChat(reportId)
      setMessages([])
    } catch (err) {
      setError(err.message || 'Could not clear the conversation.')
    } finally {
      setClearing(false)
    }
  }

  const suggestions = [
    'Which results are out of range?',
    results[0] ? `What does ${results[0].test_name} mean?` : 'Summarise my report',
    'What should I do next?',
  ]

  return (
    <section className="card p-5 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
            <MessageCircle size={18} className="text-medical-600" aria-hidden="true" />
            Ask about this report
          </h2>
          <p className="muted mt-1 max-w-2xl">
            Answers use only the results extracted from this report. It cannot diagnose a condition
            or recommend medicines.
          </p>
        </div>

        <div className="flex shrink-0 flex-col items-start gap-2 sm:flex-row sm:items-center">
          <div className="relative">
            <Languages
              size={15}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <label htmlFor="chat-language" className="sr-only">
              Chat language
            </label>
            <select
              id="chat-language"
              value={language}
              onChange={(event) => onLanguageChange?.(event.target.value)}
              className="input py-2 pl-9 pr-8"
            >
              {LANGUAGES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {messages.length > 0 ? (
            <button
              type="button"
              onClick={clearChat}
              disabled={clearing || sending}
              className="btn-ghost text-slate-500"
            >
              {clearing ? (
                <Loader2 size={15} className="animate-spin" aria-hidden="true" />
              ) : (
                <Trash2 size={15} aria-hidden="true" />
              )}
              {clearing ? 'Clearing…' : 'Clear chat'}
            </button>
          ) : null}
        </div>
      </div>

      <div className="mt-4 max-h-[30rem] space-y-3 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50/50 p-3 sm:p-4">
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-10 text-sm text-slate-500">
            <Loader2 size={16} className="animate-spin" aria-hidden="true" />
            Loading conversation…
          </div>
        ) : messages.length === 0 && !sending ? (
          <div className="px-2 py-8 text-center">
            <Sparkles size={24} className="mx-auto text-slate-300" aria-hidden="true" />
            <p className="mt-2 text-sm font-medium text-slate-700">Ask a question about your report</p>
            <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-slate-500">
              For example, ask which values are outside the range or what a particular test means.
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => send(suggestion)}
                  className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-medical-300 hover:text-medical-700"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {messages.map((message) => {
          const isUser = message.role === 'user'
          const cited = (message.cited_result_ids || [])
            .map((id) => resultNames[id])
            .filter(Boolean)

          return (
            <div
              key={message.id}
              className={`max-w-[92%] rounded-2xl px-4 py-3 ${
                isUser
                  ? 'ml-auto bg-medical-700 text-sm text-white'
                  : 'border border-slate-200 bg-white shadow-sm'
              }`}
            >
              {isUser ? (
                <p className="whitespace-pre-wrap">{message.content}</p>
              ) : (
                <>
                  <ExplanationText text={message.content} />
                  <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-slate-100 pt-2.5">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${
                        message.source === 'template'
                          ? 'bg-slate-100 text-slate-600 ring-slate-200'
                          : 'bg-medical-50 text-medical-700 ring-medical-200'
                      }`}
                    >
                      {sourceLabel(message)}
                    </span>
                    {cited.length > 0 ? (
                      <span className="text-[10px] text-slate-400">
                        Grounded in: {cited.join(', ')}
                      </span>
                    ) : null}
                  </div>
                </>
              )}
            </div>
          )
        })}

        {sending ? (
          <div className="flex max-w-[92%] items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">
            <Loader2 size={15} className="animate-spin" aria-hidden="true" />
            Checking the report…
          </div>
        ) : null}

        <div ref={endRef} />
      </div>

      {error ? (
        <div className="mt-3 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          <AlertCircle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label htmlFor="chat-input" className="sr-only">
            Ask a question about this report
          </label>
          <textarea
            id="chat-input"
            rows={2}
            maxLength={2000}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about a test, a range or a result…"
            className="input resize-none"
          />
        </div>
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="btn-primary h-[46px] shrink-0"
        >
          {sending ? (
            <Loader2 size={16} className="animate-spin" aria-hidden="true" />
          ) : (
            <Send size={16} aria-hidden="true" />
          )}
          Send
        </button>
      </form>

      <p className="mt-3 text-[11px] leading-relaxed text-slate-400">
        AI-generated educational conversation, not verified medical advice. It cannot diagnose or
        prescribe. Critical results and severe symptoms need urgent professional care — do not rely
        on this chat for an emergency decision.
      </p>
    </section>
  )
}
