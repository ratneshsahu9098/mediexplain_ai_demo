/**
 * Minimal renderer for the sectioned explanation text produced by the backend.
 * It intentionally avoids raw HTML / dangerouslySetInnerHTML.
 */
export default function ExplanationText({ text }) {
  if (!text) return null

  const lines = text.split('\n')
  return (
    <div className="space-y-2 text-sm leading-relaxed text-slate-700">
      {lines.map((line, index) => {
        const trimmed = line.trim()
        if (!trimmed) return null

        const heading = trimmed.match(/^\*\*(.+)\*\*$/)
        if (heading) {
          return (
            <h4 key={index} className="pt-2 text-[13px] font-semibold uppercase tracking-wide text-medical-800">
              {heading[1]}
            </h4>
          )
        }

        if (trimmed.startsWith('- ')) {
          return (
            <p key={index} className="flex gap-2 pl-1">
              <span aria-hidden="true" className="text-medical-600">
                •
              </span>
              <span>{trimmed.slice(2)}</span>
            </p>
          )
        }

        return <p key={index}>{trimmed}</p>
      })}
    </div>
  )
}
