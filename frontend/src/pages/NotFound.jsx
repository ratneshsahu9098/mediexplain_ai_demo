import { ArrowLeft, FileQuestion } from 'lucide-react'
import { Link } from 'react-router-dom'

import Brand from '../components/Brand.jsx'

export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center bg-slate-50 px-4">
      <div className="w-full max-w-md text-center">
        <div className="flex justify-center">
          <Brand />
        </div>
        <span className="mx-auto mt-10 grid h-16 w-16 place-items-center rounded-2xl bg-white text-slate-400 shadow-sm ring-1 ring-slate-200">
          <FileQuestion size={30} aria-hidden="true" />
        </span>
        <h1 className="mt-5 text-2xl font-bold tracking-tight text-slate-900">Page not found</h1>
        <p className="mt-1.5 text-sm text-slate-500">
          The page you are looking for does not exist, or you may not have access to it.
        </p>
        <Link to="/" className="btn-primary mt-5">
          <ArrowLeft size={16} aria-hidden="true" />
          Back to home
        </Link>
      </div>
    </div>
  )
}
