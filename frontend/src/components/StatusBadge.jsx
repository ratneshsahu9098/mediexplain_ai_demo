import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  CheckCircle2,
  Clock3,
  Info,
  MinusCircle,
  ShieldAlert,
} from 'lucide-react'

const CONFIG = {
  NORMAL: {
    label: 'Normal',
    icon: CheckCircle2,
    classes: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  },
  LOW: {
    label: 'Low',
    icon: ArrowDown,
    classes: 'bg-amber-50 text-amber-800 ring-amber-200',
  },
  HIGH: {
    label: 'High',
    icon: ArrowUp,
    classes: 'bg-rose-50 text-rose-700 ring-rose-200',
  },
  UNKNOWN: {
    label: 'Not classified',
    icon: MinusCircle,
    classes: 'bg-slate-100 text-slate-600 ring-slate-200',
  },
  NEEDS_REVIEW: {
    label: 'Needs review',
    icon: AlertTriangle,
    classes: 'bg-orange-50 text-orange-700 ring-orange-200',
  },
  NOT_AVAILABLE: {
    label: 'Not available',
    icon: MinusCircle,
    classes: 'bg-slate-100 text-slate-600 ring-slate-200',
  },
  QUALITATIVE: {
    label: 'Qualitative',
    icon: Info,
    classes: 'bg-sky-50 text-sky-700 ring-sky-200',
  },
  FAILED: {
    label: 'Failed',
    icon: ShieldAlert,
    classes: 'bg-rose-50 text-rose-700 ring-rose-200',
  },
  COMPLETED: {
    label: 'Completed',
    icon: CheckCircle2,
    classes: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  },
  PROCESSING: {
    label: 'Processing',
    icon: Clock3,
    classes: 'bg-sky-50 text-sky-700 ring-sky-200',
  },
}

export default function StatusBadge({ status, size = 'md' }) {
  const config = CONFIG[status] || CONFIG.UNKNOWN
  const Icon = config.icon
  const padding = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-semibold ring-1 ring-inset ${padding} ${config.classes}`}
    >
      <Icon size={size === 'sm' ? 12 : 14} aria-hidden="true" />
      {config.label}
    </span>
  )
}
