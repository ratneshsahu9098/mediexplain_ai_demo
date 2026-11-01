import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  FileText,
  Image as ImageIcon,
  Loader2,
  Lock,
  ScanLine,
  UploadCloud,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { uploadReport } from '../services/api.js'
import { formatFileSize } from '../utils/format.js'

const MAX_MB = 15
const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']

function extensionOf(filename) {
  const index = filename.lastIndexOf('.')
  return index >= 0 ? filename.slice(index).toLowerCase() : ''
}

function validateFile(file) {
  if (!file) return 'Choose a file first.'
  if (!ALLOWED_EXTENSIONS.includes(extensionOf(file.name))) {
    return 'Unsupported file type. Upload a PDF, JPG, JPEG or PNG.'
  }
  if (file.size === 0) return 'The selected file is empty.'
  if (file.size > MAX_MB * 1024 * 1024) {
    return `The file is ${formatFileSize(file.size)}. The maximum size is ${MAX_MB} MB.`
  }
  return ''
}

export default function Upload() {
  const navigate = useNavigate()
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [duplicateId, setDuplicateId] = useState(null)

  useEffect(() => {
    if (!file || !file.type.startsWith('image/')) {
      setPreviewUrl('')
      return undefined
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  function selectFile(candidate) {
    setError('')
    setDuplicateId(null)
    setProgress(0)
    const validationError = validateFile(candidate)
    if (validationError) {
      setError(validationError)
      setFile(null)
      return
    }
    setFile(candidate)
  }

  function handleDrop(event) {
    event.preventDefault()
    setDragging(false)
    const dropped = event.dataTransfer.files?.[0]
    if (dropped) selectFile(dropped)
  }

  async function handleUpload() {
    if (!file || uploading) return
    setError('')
    setUploading(true)
    setProgress(0)
    try {
      const report = await uploadReport(file, setProgress)
      navigate(`/app/reports/${report.id}`)
    } catch (err) {
      setError(err.message || 'Upload failed.')
      if (err.detail && typeof err.detail === 'object' && err.detail.report_id) {
        setDuplicateId(err.detail.report_id)
      }
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-medical-700">New analysis</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Upload a medical report</h1>
        <p className="mt-1 text-sm text-slate-500">
          We support digital PDFs and photos of printed reports. Scanned pages are processed with OCR.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.55fr_1fr]">
        <section className="card p-5 sm:p-6">
          <input
            ref={inputRef}
            type="file"
            accept={ALLOWED_EXTENSIONS.join(',')}
            className="sr-only"
            onChange={(event) => {
              const selected = event.target.files?.[0]
              if (selected) selectFile(selected)
              event.target.value = ''
            }}
          />

          {!file ? (
            <div
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') inputRef.current?.click()
              }}
              onDragOver={(event) => {
                event.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 text-center transition ${
                dragging
                  ? 'border-medical-500 bg-medical-50'
                  : 'border-slate-300 bg-slate-50/60 hover:border-medical-400 hover:bg-medical-50/40'
              }`}
            >
              <span className="grid h-14 w-14 place-items-center rounded-2xl bg-white text-medical-700 shadow-sm ring-1 ring-slate-200">
                <UploadCloud size={26} aria-hidden="true" />
              </span>
              <p className="mt-4 text-sm font-semibold text-slate-900">
                Drag & drop your report, or click to browse
              </p>
              <p className="mt-1 text-xs text-slate-500">PDF, JPG, JPEG or PNG · up to {MAX_MB} MB</p>
              <span className="btn-secondary mt-4">Choose file</span>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 p-4">
              <div className="flex items-start gap-4">
                <span className="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-xl bg-slate-100 text-slate-600">
                  {previewUrl ? (
                    <img src={previewUrl} alt="Selected report preview" className="h-full w-full object-cover" />
                  ) : extensionOf(file.name) === '.pdf' ? (
                    <FileText size={24} aria-hidden="true" />
                  ) : (
                    <ImageIcon size={24} aria-hidden="true" />
                  )}
                </span>

                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-900">{file.name}</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {extensionOf(file.name).replace('.', '').toUpperCase()} · {formatFileSize(file.size)}
                  </p>
                  {!uploading ? (
                    <div className="mt-2 flex gap-3">
                      <button
                        type="button"
                        onClick={() => inputRef.current?.click()}
                        className="text-xs font-semibold text-medical-700 hover:text-medical-900"
                      >
                        Replace file
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setFile(null)
                          setError('')
                          setProgress(0)
                        }}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-700"
                      >
                        <X size={12} aria-hidden="true" />
                        Remove
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>

              {uploading ? (
                <div className="mt-5">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Uploading and processing…</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-medical-600 transition-all"
                      style={{ width: `${Math.max(progress, 4)}%` }}
                    />
                  </div>
                  <p className="mt-2 text-[11px] text-slate-400">
                    Extraction and analysis can take a few seconds for scanned reports.
                  </p>
                </div>
              ) : (
                <button type="button" onClick={handleUpload} className="btn-primary mt-5 w-full">
                  Analyse this report
                  <ArrowRight size={16} aria-hidden="true" />
                </button>
              )}
            </div>
          )}

          {error ? (
            <div className="mt-4 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              <AlertCircle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
              <div>
                <p>{error}</p>
                {duplicateId ? (
                  <Link
                    to={`/app/reports/${duplicateId}`}
                    className="mt-1 inline-block text-xs font-semibold underline"
                  >
                    Open the existing report
                  </Link>
                ) : null}
              </div>
            </div>
          ) : null}
        </section>

        <aside className="space-y-4">
          <div className="card p-5">
            <h2 className="section-title">Best results</h2>
            <ul className="mt-3 space-y-3 text-xs leading-relaxed text-slate-600">
              <li className="flex gap-2">
                <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-emerald-600" aria-hidden="true" />
                Digital PDFs with selectable text give the highest extraction accuracy.
              </li>
              <li className="flex gap-2">
                <ScanLine size={15} className="mt-0.5 shrink-0 text-medical-600" aria-hidden="true" />
                For photos, keep the page flat, well lit and fully in frame.
              </li>
              <li className="flex gap-2">
                <FileText size={15} className="mt-0.5 shrink-0 text-slate-500" aria-hidden="true" />
                Include the test name, result, unit and reference range columns.
              </li>
            </ul>
          </div>

          <div className="rounded-2xl border border-medical-100 bg-medical-50/60 p-5">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-medical-900">
              <Lock size={15} aria-hidden="true" />
              Your document stays private
            </p>
            <p className="mt-1.5 text-xs leading-relaxed text-medical-800/80">
              Files are stored outside the public web root and can only be accessed by your account.
              You can delete a report and its stored file at any time.
            </p>
          </div>

          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
            <p className="text-sm font-semibold text-amber-900">Before you upload</p>
            <p className="mt-1.5 text-xs leading-relaxed text-amber-800">
              Use synthetic or de-identified reports while developing the project. Do not upload
              someone else’s medical document without their consent.
            </p>
          </div>
        </aside>
      </div>
    </div>
  )
}
