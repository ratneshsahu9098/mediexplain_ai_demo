const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(
  /\/$/,
  '',
)

export const TOKEN_KEY = 'mediexplain_token'

export class ApiError extends Error {
  constructor(message, status = 0, detail = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function authToken() {
  return localStorage.getItem(TOKEN_KEY)
}

function messageFromPayload(payload, fallback) {
  if (!payload) return fallback
  const detail = payload.detail ?? payload
  if (typeof detail === 'string') return detail
  if (detail && typeof detail.message === 'string') return detail.message
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message)
      .filter(Boolean)
      .join('; ')
  }
  return fallback
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {}
  if (auth) {
    const token = authToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(`Could not reach the server at ${BASE_URL}. Is the backend running?`)
  }

  if (response.status === 204) return null

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(
      messageFromPayload(payload, `Request failed (${response.status}).`),
      response.status,
      payload?.detail ?? null,
    )
  }
  return payload
}

export const api = {
  register: (data) => request('/api/auth/register', { method: 'POST', body: data, auth: false }),

  login: (data) => request('/api/auth/login', { method: 'POST', body: data, auth: false }),

  me: () => request('/api/auth/me'),

  listReports: () => request('/api/reports'),

  getReport: (reportId) => request(`/api/reports/${reportId}`),

  analyze: (reportId) => request(`/api/reports/${reportId}/analyze`, { method: 'POST' }),

  explain: (reportId, language) =>
    request(`/api/reports/${reportId}/explain?language=${encodeURIComponent(language)}`, {
      method: 'POST',
    }),

  getChat: (reportId) => request(`/api/reports/${reportId}/chat`),

  sendChat: (reportId, message, language) =>
    request(`/api/reports/${reportId}/chat`, {
      method: 'POST',
      body: { message, language },
    }),

  clearChat: (reportId) => request(`/api/reports/${reportId}/chat`, { method: 'DELETE' }),

  deleteReport: (reportId) => request(`/api/reports/${reportId}`, { method: 'DELETE' }),
}

export function uploadReport(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${BASE_URL}/api/reports/upload`)

    const token = authToken()
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    }

    xhr.onerror = () => {
      reject(new ApiError(`Could not reach the server at ${BASE_URL}. Is the backend running?`))
    }

    xhr.onload = () => {
      let payload = null
      try {
        payload = JSON.parse(xhr.responseText)
      } catch {
        payload = null
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(payload)
      } else {
        reject(
          new ApiError(
            messageFromPayload(payload, `Upload failed (${xhr.status}).`),
            xhr.status,
            payload?.detail ?? null,
          ),
        )
      }
    }

    const form = new FormData()
    form.append('file', file)
    xhr.send(form)
  })
}
