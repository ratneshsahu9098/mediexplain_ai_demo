import { Info } from 'lucide-react'

export default function Disclaimer({ compact = false, className = '' }) {
  if (compact) {
    return (
      <p className={`flex gap-2 text-xs leading-relaxed text-slate-500 ${className}`}>
        <Info size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
        <span>
          Educational information only — not a diagnosis or medical advice. Discuss results with a
          qualified healthcare professional.
        </span>
      </p>
    )
  }

  return (
    <div
      className={`flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 ${className}`}
    >
      <Info size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
      <div>
        <p className="font-semibold">Informational, not diagnostic</p>
        <p className="mt-1 leading-relaxed">
          MediExplain AI helps you understand laboratory values. It does not diagnose disease,
          recommend treatment or replace a doctor. An out-of-range result is not a diagnosis. For
          urgent symptoms or critical results, seek professional medical care immediately.
        </p>
      </div>
    </div>
  )
}
