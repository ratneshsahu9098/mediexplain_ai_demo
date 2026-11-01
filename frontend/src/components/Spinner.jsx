import { Loader2 } from 'lucide-react'

export default function Spinner({ label = 'Loading…', fullPage = false }) {
  return (
    <div
      className={
        fullPage
          ? 'grid min-h-screen place-items-center bg-slate-50'
          : 'flex items-center justify-center gap-2 py-10 text-sm text-slate-500'
      }
      role="status"
    >
      <Loader2 className="animate-spin text-medical-600" size={20} aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}
