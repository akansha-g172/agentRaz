import { Link, Outlet, useLocation } from 'react-router-dom'

const nav = [
  { to: '/', label: 'Buyer Console' },
  { to: '/merchant', label: 'Merchant Dashboard' },
  { to: '/audit', label: 'Audit Console' },
]

export default function Layout() {
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">AgentRaz</h1>
            <p className="text-xs text-slate-400">Razorpay AI Buildathon — Agentic Commerce</p>
          </div>
          <nav className="flex gap-2">
            {nav.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                  pathname === to
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
