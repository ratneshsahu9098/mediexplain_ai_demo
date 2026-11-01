import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  FileText,
  Info,
  Languages,
  Loader2,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import Disclaimer from '../components/Disclaimer.jsx'
import ExplanationText from '../components/ExplanationText.jsx'
import Spinner from '../components/Spinner.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { api } from '../services/api.js'
import { countStatuses, formatDate, formatNumber } from '../utils/format.js'

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'हिन्दी (Hindi)' },
  { value: 'hinglish', label: 'Hinglish' },
]

function rangeLabel(result) {
  if (!result.range_text) return 'Not reported'
  return `${result.range_text}${result.range_unit ? ` ${result.range_unit}` : ''}`
}

function resultValue(result) {
  const value =
    result.value_text ||
    (result.value !== null && result.value !== undefined ? formatNumber(result.value) : '—')
  return `${value}${result.unit ? ` ${result.unit}` : ''}`
}

function sourceLabel(source) {
  if (!source || source === 'template') return 'Offline template'
  return `AI · ${source}`
}

export default function Report() {
  const { reportId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [explanationMap, setExplanationMap] = useState({})
  const [language, setLanguage] = useState('en')
  const [explaining, setExplaining] = useState(false)
  const [explainError, setExplainError] = useState('')
  const [provider, setProvider] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    setLoadError('')
    setReport(null)
    setExplanationMap({})

    api
      .getReport(reportId)
      .then((data) => {
        if (!active) return
        setReport(data)
        const map = {}
        data.results.forEach((result) => {
          if (result.explanation) {
            map[result.id] = {
              result_id: result.id,
              test_name: result.test_name,
              text: result.explanation,
              source: result.explanation_source || 'template',
            }
          }
        })
        setExplanationMap(map)
      })
      .catch((error) => {
        if (active) setLoadError(error.message || 'Could not load this report.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [reportId])

  const counts = useMemo(() => countStatuses(report?.results || []), [report])
  const criticalResults = useMemo(
    () => (report?.results || []).filter((result) => result.critical_flag),
    [report],
  )
  const explainedResults = useMemo(
    () => (report?.results || []).filter((result) => explanationMap[result.id]),
    [report, explanationMap],
  )

  async function generateExplanations() {
    setExplaining(true)
    setExplainError('')
    try {
      const data = await api.explain(reportId, language)
      const map = {}
      data.explanations.forEach((item) => {
        map[item.result_id] = item
      })
      setExplanationMap(map)
      setProvider(data.provider)
    } catch (error) {
      setExplainError(error.message || 'Could not generate explanations.')
    } finally {
      setExplaining(false)
    }
  }

  async function deleteReport() {
    const confirmed = window.confirm(
      'Delete this report and its stored file? This cannot be undone.',
    )
    if (!confirmed) return

    setDeleting(true)
    try {
      await api.deleteReport(reportId)
      navigate('/app', { replace: true })
    } catch (error) {
      setLoadError(error.message || 'Could not delete the report.')
      setDeleting(false)
    }
  }

  if (loading) return <Spinner label="Loading report…" />

  if (loadError) {
    return (
      <div className="card mx-auto max-w-xl p-8 text-center">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-rose-50 text-rose-600">
          <AlertCircle size={22} aria-hidden="true" />
        </span>
        <h1 className="mt-4 text-lg font-semibold text-slate-900">Report unavailable</h1>
        <p className="mt-1.5 text-sm text-slate-500">{loadError}</p>
        <Link to="/app" className="btn-primary mt-5">
          Back to dashboard
        </Link>
      </div>
    )
  }

  if (!report) return null

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/app"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft size={14} aria-hidden="true" />
          Back to dashboard
        </Link>

        <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="truncate text-2xl font-bold tracking-tight text-slate-900">
                {report.original_filename}
              </h1>
              <StatusBadge status={report.status.toUpperCase()} size="sm" />
            </div>
            <p className="mt-1 text-sm text-slate-500">
              {report.report_type} · {formatDate(report.created_at)} · {report.page_count} page
              {report.page_count === 1 ? '' : 's'}
              {report.extraction_method ? ` · ${report.extraction_method.toUpperCase()} extraction` : ''}
            </p>
          </div>

          <button type="button" onClick={deleteReport} disabled={deleting} className="btn-ghost shrink-0 text-rose-600 hover:bg-rose-50">
            {deleting ? <Loader2 size={15} className="animate-spin" aria-hidden="true" /> : <Trash2 size={15} aria-hidden="true" />}
            {deleting ? 'Deleting…' : 'Delete report'}
          </button>
        </div>
      </div>

      {report.status === 'failed' ? (
        <div className="flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          <AlertCircle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
          <div>
            <p className="font-semibold">This report could not be processed</p>
            <p className="mt-1">{report.error_message || 'Unknown processing error.'}</p>
          </div>
        </div>
      ) : null}

      {report.error_message && report.status === 'completed' ? (
        <div className="flex items-start gap-2 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <Info size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
          <span>{report.error_message}</span>
        </div>
      ) : null}

      {criticalResults.length > 0 ? (
        <div className="flex items-start gap-3 rounded-2xl border border-rose-300 bg-rose-50 p-4">
          <AlertTriangle size={20} className="mt-0.5 shrink-0 text-rose-600" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-rose-900">
              Critical-value rule triggered for {criticalResults.length} result
              {criticalResults.length === 1 ? '' : 's'}
            </p>
            <p className="mt-1 text-sm leading-relaxed text-rose-800">
              {criticalResults.map((result) => result.test_name).join(', ')}. These placeholder rules
              are for demonstration and are not clinically validated. Please contact a healthcare
              professional promptly — do not wait for an AI explanation.
            </p>
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'Results extracted', value: counts.total, tone: 'text-slate-900' },
          { label: 'Out of range', value: counts.abnormal, tone: 'text-amber-700' },
          { label: 'Normal', value: counts.normal, tone: 'text-emerald-700' },
          {
            label: 'Not classified',
            value: counts.unknown + counts.review,
            tone: 'text-slate-600',
          },
        ].map((item) => (
          <div key={item.label} className="card p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{item.label}</p>
            <p className={`mt-1.5 text-2xl font-bold ${item.tone}`}>{item.value}</p>
          </div>
        ))}
      </div>

      <section className="card overflow-hidden">
        <div className="flex flex-col gap-1 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="section-title">Extracted results</h2>
            <p className="muted mt-0.5">
              Values are shown exactly as extracted. Ranges come from this report only.
            </p>
          </div>
          <span className="text-xs text-slate-400">Status is rule-based</span>
        </div>

        {report.results.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <FileText size={26} className="mx-auto text-slate-300" aria-hidden="true" />
            <p className="mt-2 text-sm font-medium text-slate-700">No test results were extracted</p>
            <p className="mx-auto mt-1 max-w-md text-xs text-slate-500">
              Try a clearer scan or a PDF with selectable text. The original report remains the source
              of truth.
            </p>
          </div>
        ) : (
          <>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/70 text-[11px] uppercase tracking-wide text-slate-500">
                    <th scope="col" className="px-5 py-3 font-semibold">Test</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Result</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Reference range</th>
                    <th scope="col" className="px-5 py-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {report.results.map((result) => (
                    <tr key={result.id} className="align-top hover:bg-slate-50/60">
                      <td className="px-5 py-3.5">
                        <p className="font-medium text-slate-900">{result.test_name}</p>
                        {result.raw_name && result.raw_name !== result.test_name ? (
                          <p className="mt-0.5 text-[11px] text-slate-400">As printed: {result.raw_name}</p>
                        ) : null}
                        {result.notes ? (
                          <p className="mt-1 max-w-md text-[11px] leading-relaxed text-slate-400">
                            {result.notes}
                          </p>
                        ) : null}
                      </td>
                      <td className="px-4 py-3.5 font-medium text-slate-800">{resultValue(result)}</td>
                      <td className="px-4 py-3.5 text-slate-600">{rangeLabel(result)}</td>
                      <td className="px-5 py-3.5">
                        <div className="flex flex-col items-start gap-1.5">
                          <StatusBadge status={result.status} size="sm" />
                          {result.critical_flag ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
                              <AlertTriangle size={11} aria-hidden="true" />
                              Critical rule
                            </span>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <ul className="divide-y divide-slate-100 md:hidden">
              {report.results.map((result) => (
                <li key={result.id} className="px-4 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900">{result.test_name}</p>
                      <p className="mt-0.5 text-lg font-semibold text-slate-800">{resultValue(result)}</p>
                      <p className="text-xs text-slate-500">Ref: {rangeLabel(result)}</p>
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1.5">
                      <StatusBadge status={result.status} size="sm" />
                      {result.critical_flag ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-semibold text-rose-700">
                          <AlertTriangle size={10} aria-hidden="true" />
                          Critical
                        </span>
                      ) : null}
                    </div>
                  </div>
                  {result.notes ? (
                    <p className="mt-2 text-[11px] leading-relaxed text-slate-400">{result.notes}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="card p-5 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
              <Sparkles size={18} className="text-medical-600" aria-hidden="true" />
              AI explanations
            </h2>
            <p className="muted mt-1 max-w-2xl">
              Plain-language education, generated from the extracted values. The explanation never
              changes a number; the table above remains the source of truth.
            </p>
          </div>

          <div className="flex shrink-0 flex-col gap-2 sm:flex-row sm:items-center">
            <label htmlFor="language" className="sr-only">
              Explanation language
            </label>
            <div className="relative">
              <Languages
                size={15}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                aria-hidden="true"
              />
              <select
                id="language"
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
                className="input py-2 pl-9 pr-8"
              >
                {LANGUAGES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              onClick={generateExplanations}
              disabled={explaining || report.results.length === 0}
              className="btn-primary"
            >
              {explaining ? (
                <Loader2 size={16} className="animate-spin" aria-hidden="true" />
              ) : (
                <Sparkles size={16} aria-hidden="true" />
              )}
              {explaining ? 'Generating…' : explainedResults.length ? 'Regenerate' : 'Explain results'}
            </button>
          </div>
        </div>

        {explainError ? (
          <div className="mt-4 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <AlertCircle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
            <span>{explainError}</span>
          </div>
        ) : null}

        {explainedResults.length === 0 ? (
          <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-5 py-10 text-center">
            <Sparkles size={24} className="mx-auto text-slate-300" aria-hidden="true" />
            <p className="mt-2 text-sm font-medium text-slate-700">No explanations generated yet</p>
            <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-slate-500">
              Generate explanations to understand the tests, what the result shows, what else matters
              and what you could ask your doctor.
            </p>
          </div>
        ) : (
          <div className="mt-5 space-y-3">
            <p className="text-xs text-slate-500">
              {provider === 'template' || explainedResults.every((result) => explanationMap[result.id]?.source === 'template')
                ? 'Generated with the built-in offline template. Start Ollama for model-generated explanations.'
                : `Generated by ${provider || 'the configured AI provider'}. AI content can be wrong — verify with your clinician.`}
            </p>

            {explainedResults.map((result) => {
              const explanation = explanationMap[result.id]
              return (
                <article key={result.id} className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 sm:p-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-semibold text-slate-900">{result.test_name}</h3>
                    <StatusBadge status={result.status} size="sm" />
                    <span
                      className={`ml-auto rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${
                        explanation.source === 'template'
                          ? 'bg-slate-100 text-slate-600 ring-slate-200'
                          : 'bg-medical-50 text-medical-700 ring-medical-200'
                      }`}
                    >
                      {sourceLabel(explanation.source)}
                    </span>
                  </div>
                  <div className="mt-2 border-t border-slate-200/70 pt-2">
                    <ExplanationText text={explanation.text} />
                  </div>
                </article>
              )
            })}
          </div>
        )}

        <p className="mt-4 flex items-start gap-1.5 text-[11px] leading-relaxed text-slate-400">
          <Info size={13} className="mt-0.5 shrink-0" aria-hidden="true" />
          AI-generated educational content, not verified medical advice. It cannot diagnose, prescribe
          or replace a consultation. Critical results require urgent professional care.
        </p>
      </section>

      <Disclaimer />
    </div>
  )
}
