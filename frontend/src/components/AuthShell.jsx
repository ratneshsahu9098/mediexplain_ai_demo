import { Activity, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'

import Brand from './Brand.jsx'
import Disclaimer from './Disclaimer.jsx'

export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="grid min-h-screen bg-slate-50 lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden overflow-hidden bg-medical-950 p-10 text-white lg:flex lg:flex-col lg:justify-between">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-medical-600/30 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -bottom-24 -left-16 h-80 w-80 rounded-full bg-cyan-500/20 blur-3xl"
        />

        <div className="relative">
          <div className="flex items-center gap-2.5">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-white/10 ring-1 ring-white/20">
              <Activity size={22} aria-hidden="true" />
            </span>
            <span className="text-lg font-bold tracking-tight">
              MediExplain <span className="text-medical-300">AI</span>
            </span>
          </div>

          <h2 className="mt-16 max-w-md text-4xl font-bold leading-tight tracking-tight">
            Your lab report, explained in language you actually understand.
          </h2>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-medical-100/80">
            Upload a PDF or photo of your report. MediExplain extracts the values, compares them with
            the reference range printed on your report, and explains what each result means.
          </p>

          <ul className="mt-8 space-y-3 text-sm text-medical-100/90">
            {[
              'OCR for scanned reports and clear PDFs',
              'Rule-based flags — the AI never decides high or low',
              'Explanations in English, Hindi and Hinglish',
            ].map((item) => (
              <li key={item} className="flex items-start gap-2.5">
                <ShieldCheck size={17} className="mt-0.5 shrink-0 text-medical-300" aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative mt-10 max-w-md text-xs leading-relaxed text-medical-200/60">
          MediExplain AI is an educational project. It does not diagnose disease, prescribe treatment
          or replace professional medical advice.
        </p>
      </aside>

      <main className="flex items-center justify-center px-4 py-10 sm:px-6">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Brand />
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
          {subtitle ? <p className="mt-1.5 text-sm text-slate-500">{subtitle}</p> : null}

          <div className="mt-7">{children}</div>

          {footer ? <div className="mt-6 text-center text-sm text-slate-600">{footer}</div> : null}

          <div className="mt-8 border-t border-slate-200 pt-5">
            <Disclaimer compact />
          </div>

          <p className="mt-5 text-center text-xs text-slate-400">
            <Link to="/" className="hover:text-slate-600">
              Back to home
            </Link>
          </p>
        </div>
      </main>
    </div>
  )
}
