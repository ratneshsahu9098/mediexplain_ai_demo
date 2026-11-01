import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  FileText,
  Plus,
  ShieldCheck,
  UploadCloud,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import Disclaimer from '../components/Disclaimer.jsx'
import Spinner from '../components/Spinner.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { api } from '../services/api.js'
import { formatDate } from '../utils/format.js'

function StatCard({ icon: Icon, label, value, hint, tone = 'medical' }) {
  const toneClasses = {
    medical: 'bg-medical-50 text-medical-700',
    amber: 'bg-amber-50 text-amber-700',
    emerald: 'bg-emerald-50 text-emerald-700',
    slate: 'bg-slate-100 text-slate-600',
  }

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-bold tracking-tight text-slate-900">{value}</p>
          {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
        </div>
        <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${toneClasses[tone]}`}>
          <Icon size={19} aria-hidden="true" />
        </span>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    api
      .listReports()
      .then((data) => {
        if (active) setReports(data.items || [])
      })
      .catch((err) => {
        if (active) setError(err.message || 'Could not load your reports.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const latest = reports[0]
  const completed = reports.filter((report) => report.status === 'completed').length
  const latestAbnormal = latest?.abnormal_count ?? 0
  const latestNormal = Math.max((latest?.result_count ?? 0) - latestAbnormal, 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-medical-700">Dashboard</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">
            Hello, {user?.name?.split(' ')[0] || 'there'}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Review your uploaded reports and continue where you left off.
          </p>
        </div>
        <Link to="/app/upload" className="btn-primary shrink-0">
          <Plus size={16} aria-hidden="true" />
          Upload a report
        </Link>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          <AlertCircle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      ) : null}

      {loading ? (
        <Spinner label="Loading your dashboard…" />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              icon={FileText}
              label="Total reports"
              value={reports.length}
              hint="Uploaded to your account"
            />
            <StatCard
              icon={AlertTriangle}
              label="Abnormal in latest"
              value={latestAbnormal}
              hint={latest ? 'Low or high results' : 'No report yet'}
              tone="amber"
            />
            <StatCard
              icon={CheckCircle2}
              label="Completed"
              value={completed}
              hint="Successfully processed"
              tone="emerald"
            />
            <StatCard
              icon={ShieldCheck}
              label="Latest report"
              value={latest ? latest.report_type.replace('Complete Blood Count (CBC)', 'CBC') : '—'}
              hint={latest ? formatDate(latest.created_at) : 'Upload to begin'}
              tone="slate"
            />
          </div>

          {reports.length === 0 ? (
            <div className="card px-6 py-14 text-center">
              <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-medical-50 text-medical-700">
                <UploadCloud size={26} aria-hidden="true" />
              </span>
              <h2 className="mt-4 text-lg font-semibold text-slate-900">No reports yet</h2>
              <p className="mx-auto mt-1.5 max-w-md text-sm leading-relaxed text-slate-500">
                Upload a PDF or photo of a laboratory report. MediExplain will extract the results,
                check them against the report’s reference ranges and explain the findings.
              </p>
              <Link to="/app/upload" className="btn-primary mt-5">
                <Plus size={16} aria-hidden="true" />
                Upload your first report
              </Link>
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
              <section className="card overflow-hidden">
                <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
                  <div>
                    <h2 className="section-title">Recent reports</h2>
                    <p className="muted mt-0.5">Newest first</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                    {reports.length} total
                  </span>
                </div>

                <ul className="divide-y divide-slate-100">
                  {reports.slice(0, 8).map((report) => (
                    <li key={report.id}>
                      <Link
                        to={`/app/reports/${report.id}`}
                        className="flex items-center gap-3 px-5 py-4 transition hover:bg-slate-50"
                      >
                        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-medical-50 text-medical-700">
                          <FileText size={18} aria-hidden="true" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-semibold text-slate-900">
                            {report.original_filename}
                          </p>
                          <p className="mt-0.5 truncate text-xs text-slate-500">
                            {report.report_type} · {formatDate(report.created_at)}
                          </p>
                        </div>
                        <div className="hidden shrink-0 text-right sm:block">
                          <p className="text-xs font-medium text-slate-600">
                            {report.result_count} result{report.result_count === 1 ? '' : 's'}
                          </p>
                          <p className="text-[11px] text-slate-400">
                            {report.abnormal_count} out of range
                          </p>
                        </div>
                        <ArrowRight size={16} className="shrink-0 text-slate-400" aria-hidden="true" />
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>

              <aside className="space-y-4">
                {latest ? (
                  <div className="card p-5">
                    <div className="flex items-center justify-between">
                      <h2 className="section-title">Latest analysis</h2>
                      <StatusBadge status={latest.status.toUpperCase()} size="sm" />
                    </div>
                    <Link
                      to={`/app/reports/${latest.id}`}
                      className="mt-3 block truncate text-sm font-semibold text-medical-800 hover:text-medical-900"
                    >
                      {latest.original_filename}
                    </Link>
                    <p className="mt-0.5 text-xs text-slate-500">{latest.report_type}</p>

                    <div className="mt-4">
                      <div className="flex h-2.5 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="bg-emerald-500"
                          style={{
                            width: `${latest.result_count ? (latestNormal / latest.result_count) * 100 : 0}%`,
                          }}
                        />
                        <div
                          className="bg-amber-500"
                          style={{
                            width: `${latest.result_count ? (latestAbnormal / latest.result_count) * 100 : 0}%`,
                          }}
                        />
                      </div>
                      <div className="mt-2 flex justify-between text-[11px] text-slate-500">
                        <span>{latestNormal} normal</span>
                        <span>{latestAbnormal} out of range</span>
                      </div>
                    </div>

                    <Link
                      to={`/app/reports/${latest.id}`}
                      className="btn-secondary mt-4 w-full justify-center"
                    >
                      Open analysis
                      <ArrowRight size={15} aria-hidden="true" />
                    </Link>
                  </div>
                ) : null}

                <div className="rounded-2xl border border-medical-100 bg-medical-50/60 p-5">
                  <p className="flex items-center gap-1.5 text-sm font-semibold text-medical-900">
                    <ShieldCheck size={16} aria-hidden="true" />
                    A reminder
                  </p>
                  <p className="mt-1.5 text-xs leading-relaxed text-medical-800/80">
                    Values outside a reference range are common and are not a diagnosis. Reference
                    intervals differ by laboratory, age, sex and method. Always use the interval
                    printed on your own report.
                  </p>
                </div>

                <Disclaimer />
              </aside>
            </div>
          )}
        </>
      )}
    </div>
  )
}
