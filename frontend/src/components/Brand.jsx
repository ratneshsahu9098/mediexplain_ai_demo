import { Activity } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Brand({ to = '/', subtitle = 'AI medical report explainer' }) {
  return (
    <Link to={to} className="inline-flex items-center gap-2.5">
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-medical-700 text-white shadow-sm">
        <Activity size={20} strokeWidth={2.4} aria-hidden="true" />
      </span>
      <span className="leading-tight">
        <span className="block text-[15px] font-bold tracking-tight text-slate-900">
          MediExplain <span className="text-medical-700">AI</span>
        </span>
        {subtitle ? <span className="block text-[11px] text-slate-500">{subtitle}</span> : null}
      </span>
    </Link>
  )
}
