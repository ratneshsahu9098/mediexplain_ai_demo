import {
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  FileSearch,
  FileText,
  HeartPulse,
  Languages,
  Lock,
  MessageSquareText,
  ScanLine,
  Sparkles,
  UploadCloud,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import Brand from '../components/Brand.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { useAuth } from '../context/AuthContext.jsx'

const WORKFLOW = [
  {
    icon: UploadCloud,
    step: '01',
    title: 'Upload your report',
    description: 'PDF, JPG or PNG. Scanned reports are processed with OCR.',
  },
  {
    icon: ScanLine,
    step: '02',
    title: 'Extract the values',
    description: 'Test names, numbers, units and the laboratory’s own reference ranges.',
  },
  {
    icon: FileSearch,
    step: '03',
    title: 'Classify, deterministically',
    description: 'A rule engine marks LOW, HIGH or NORMAL — not the language model.',
  },
  {
    icon: MessageSquareText,
    step: '04',
    title: 'Understand and ask',
    description: 'Plain-language explanations and a report-grounded assistant.',
  },
]

const FEATURES = [
  {
    icon: FileText,
    title: 'Clear PDF + table extraction',
    body: 'Selectable PDF text is read directly; tabular layouts are enriched with pdfplumber.',
  },
  {
    icon: ScanLine,
    title: 'OCR fallback',
    body: 'Image-only pages and phone photos are rendered and passed through Tesseract.',
  },
  {
    icon: BrainCircuit,
    title: 'Deterministic analysis',
    body: 'Your values are compared with the report’s own interval, with unit conversion where exact.',
  },
  {
    icon: Sparkles,
    title: 'Local AI explanations',
    body: 'Ollama + Qwen explains terminology, with a safe offline template fallback.',
  },
  {
    icon: Languages,
    title: 'English, Hindi, Hinglish',
    body: 'Explanations can be generated in the language you are most comfortable with.',
  },
  {
    icon: Lock,
    title: 'Private by design',
    body: 'Per-user access, hashed passwords, private upload storage and no public file URLs.',
  },
]

export default function Landing() {
  const { user } = useAuth()
  const primaryTo = user ? '/app' : '/register'
  const primaryLabel = user ? 'Open dashboard' : 'Analyse a report'

  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3.5 sm:px-6">
          <Brand />
          <div className="flex items-center gap-2">
            {user ? (
              <Link to="/app" className="btn-primary">
                Dashboard
                <ArrowRight size={16} aria-hidden="true" />
              </Link>
            ) : (
              <>
                <Link to="/login" className="btn-ghost">
                  Sign in
                </Link>
                <Link to="/register" className="btn-primary">
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden border-b border-slate-100 bg-gradient-to-b from-medical-50/70 to-white">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -right-32 top-0 h-96 w-96 rounded-full bg-medical-200/40 blur-3xl"
          />
          <div className="mx-auto grid max-w-6xl gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.02fr_0.98fr] lg:items-center lg:py-24">
            <div className="relative">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-medical-200 bg-white px-3 py-1 text-xs font-semibold text-medical-700">
                <Sparkles size={13} aria-hidden="true" />
                AI + OCR + rule-based analysis
              </span>

              <h1 className="mt-5 max-w-xl text-4xl font-extrabold leading-[1.08] tracking-tight text-slate-950 sm:text-5xl">
                Understand your lab report,{' '}
                <span className="text-medical-700">not just the numbers.</span>
              </h1>

              <p className="mt-5 max-w-xl text-base leading-relaxed text-slate-600">
                MediExplain AI reads your laboratory report, extracts every test result and explains
                what the values mean in plain language — always against the reference range printed
                on your own report.
              </p>

              <div className="mt-7 flex flex-wrap items-center gap-3">
                <Link to={primaryTo} className="btn-primary px-5 py-3">
                  {primaryLabel}
                  <ArrowRight size={17} aria-hidden="true" />
                </Link>
                <Link to="/login" className="btn-secondary px-5 py-3">
                  I already have an account
                </Link>
              </div>

              <div className="mt-7 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1.5">
                  <CheckCircle2 size={14} className="text-emerald-600" aria-hidden="true" />
                  No diagnosis, ever
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <CheckCircle2 size={14} className="text-emerald-600" aria-hidden="true" />
                  Values preserved verbatim
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <CheckCircle2 size={14} className="text-emerald-600" aria-hidden="true" />
                  Works with local AI
                </span>
              </div>
            </div>

            <div className="relative mx-auto w-full max-w-md">
              <div className="absolute inset-x-8 -bottom-4 h-24 rounded-3xl bg-medical-900/10 blur-xl" />
              <div className="card relative p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                      Sample report
                    </p>
                    <p className="mt-0.5 text-base font-semibold text-slate-900">
                      Complete Blood Count
                    </p>
                    <p className="text-xs text-slate-500">Synthetic data · not a real patient</p>
                  </div>
                  <span className="rounded-full bg-medical-50 px-2.5 py-1 text-[11px] font-semibold text-medical-700 ring-1 ring-inset ring-medical-200">
                    Analysed
                  </span>
                </div>

                <div className="mt-4 space-y-2">
                  {[
                    { name: 'Hemoglobin', value: '11.2 g/dL', range: '13.0 – 17.0', status: 'LOW' },
                    { name: 'WBC', value: '7,500 /µL', range: '4,000 – 11,000', status: 'NORMAL' },
                    { name: 'Platelets', value: '250,000 /µL', range: '150,000 – 450,000', status: 'NORMAL' },
                  ].map((row) => (
                    <div
                      key={row.name}
                      className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/60 px-3 py-2.5"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-800">{row.name}</p>
                        <p className="text-[11px] text-slate-500">
                          {row.value} · ref {row.range}
                        </p>
                      </div>
                      <StatusBadge status={row.status} size="sm" />
                    </div>
                  ))}
                </div>

                <div className="mt-4 rounded-xl border border-medical-100 bg-medical-50/70 p-3">
                  <p className="flex items-center gap-1.5 text-[11px] font-semibold text-medical-800">
                    <Sparkles size={13} aria-hidden="true" />
                    AI explanation
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-slate-600">
                    Hemoglobin carries oxygen in your blood. This value is below the interval printed
                    on this sample report; its meaning depends on your personal context and should be
                    discussed with a doctor.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-wider text-medical-700">
              How it works
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              From document to understandable result
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Each layer has one job. The AI explains; it never decides whether a value is high or low.
            </p>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {WORKFLOW.map(({ icon: Icon, step, title, description }) => (
              <div key={step} className="card p-5">
                <div className="flex items-center justify-between">
                  <span className="grid h-10 w-10 place-items-center rounded-xl bg-medical-50 text-medical-700">
                    <Icon size={19} aria-hidden="true" />
                  </span>
                  <span className="text-xs font-bold tracking-wider text-slate-300">{step}</span>
                </div>
                <h3 className="mt-4 text-sm font-semibold text-slate-900">{title}</h3>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-500">{description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="border-y border-slate-100 bg-slate-50/70">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
            <div className="max-w-2xl">
              <p className="text-xs font-semibold uppercase tracking-wider text-medical-700">
                Built for trust
              </p>
              <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                Healthcare-sensitive by design
              </h2>
            </div>

            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map(({ icon: Icon, title, body }) => (
                <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5">
                  <Icon size={19} className="text-medical-700" aria-hidden="true" />
                  <h3 className="mt-3 text-sm font-semibold text-slate-900">{title}</h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-slate-500">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <div className="overflow-hidden rounded-3xl bg-medical-950 px-6 py-10 text-white sm:px-10">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="max-w-2xl">
                <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-medical-300">
                  <HeartPulse size={15} aria-hidden="true" />
                  Informational, not diagnostic
                </p>
                <h2 className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
                  A clearer conversation with your doctor starts here.
                </h2>
                <p className="mt-2 text-sm leading-relaxed text-medical-100/80">
                  Use MediExplain to prepare questions, not to self-diagnose. Critical results should
                  always be discussed with a qualified healthcare professional without delay.
                </p>
              </div>
              <Link
                to={primaryTo}
                className="btn shrink-0 bg-white px-5 py-3 text-medical-900 hover:bg-medical-50"
              >
                {primaryLabel}
                <ArrowRight size={17} aria-hidden="true" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
          <Brand subtitle="B.Tech CSE (AI & ML) major project" />
          <p className="max-w-xl text-xs leading-relaxed text-slate-500">
            MediExplain AI is an educational prototype. It is not a medical device, does not provide
            medical advice, and must not be used for diagnosis or treatment decisions. Always consult
            a qualified healthcare professional.
          </p>
        </div>
      </footer>
    </div>
  )
}
