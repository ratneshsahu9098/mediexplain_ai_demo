export function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatNumber(value) {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 }).format(value)
}

export function formatFileSize(bytes) {
  if (!bytes && bytes !== 0) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function countStatuses(results = []) {
  return results.reduce(
    (counts, result) => {
      counts.total += 1
      if (result.status === 'LOW' || result.status === 'HIGH') counts.abnormal += 1
      if (result.status === 'NORMAL') counts.normal += 1
      if (result.status === 'UNKNOWN') counts.unknown += 1
      if (result.status === 'NEEDS_REVIEW') counts.review += 1
      return counts
    },
    { total: 0, abnormal: 0, normal: 0, unknown: 0, review: 0 },
  )
}
