import {
  FileWarning,
  LayoutDashboard,
  LogOut,
  UploadCloud,
} from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

import Brand from '../components/Brand.jsx'
import Disclaimer from '../components/Disclaimer.jsx'
import { useAuth } from '../context/AuthContext.jsx'

const NAV_ITEMS = [
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/app/upload', label: 'Upload report', icon: UploadCloud, end: false },
]

function NavItems({ onNavigate }) {
  return (
    <nav className="space-y-1">
      {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
              isActive
                ? 'bg-medical-50 text-medical-800'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`
          }
        >
          <Icon size={18} aria-hidden="true" />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

export default function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col border-r border-slate-200 bg-white p-5 lg:flex">
        <Brand to="/app" />

        <div className="mt-8 flex-1">
          <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Workspace
          </p>
          <NavItems />
        </div>

        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-900">
            <FileWarning size={14} aria-hidden="true" />
            Educational tool
          </p>
          <p className="mt-1 text-[11px] leading-relaxed text-amber-800">
            Not a diagnosis. Always review results with a doctor.
          </p>
        </div>

        <div className="border-t border-slate-200 pt-4">
          <p className="truncate text-sm font-medium text-slate-800">{user?.name}</p>
          <p className="truncate text-xs text-slate-500">{user?.email}</p>
          <button type="button" onClick={logout} className="btn-ghost mt-2 w-full justify-start px-2">
            <LogOut size={16} aria-hidden="true" />
            Sign out
          </button>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <Brand to="/app" subtitle="" />
            <button type="button" onClick={logout} className="btn-ghost px-2" aria-label="Sign out">
              <LogOut size={18} aria-hidden="true" />
            </button>
          </div>
          <div className="flex gap-1 border-t border-slate-100 px-3 py-2">
            <NavLink
              to="/app"
              end
              className={({ isActive }) =>
                `flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold ${
                  isActive ? 'bg-medical-50 text-medical-800' : 'text-slate-600'
                }`
              }
            >
              <LayoutDashboard size={15} aria-hidden="true" />
              Dashboard
            </NavLink>
            <NavLink
              to="/app/upload"
              className={({ isActive }) =>
                `flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold ${
                  isActive ? 'bg-medical-50 text-medical-800' : 'text-slate-600'
                }`
              }
            >
              <UploadCloud size={15} aria-hidden="true" />
              Upload
            </NavLink>
          </div>
        </header>

        <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:py-10">
          <Outlet />
        </main>

        <footer className="mx-auto w-full max-w-6xl px-4 pb-8 sm:px-6">
          <Disclaimer compact />
        </footer>
      </div>
    </div>
  )
}
