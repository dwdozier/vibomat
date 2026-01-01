import { createFileRoute, redirect, Link, Outlet, useLocation } from '@tanstack/react-router'
import { ShieldAlert, Users, Music, Link2, ArrowLeft, LayoutDashboard } from 'lucide-react'

export const Route = createFileRoute('/admin')({
  beforeLoad: async ({ context }) => {
    const user = await context.auth.getCurrentUser()
    if (!user || !user.is_superuser) {
      throw redirect({ to: '/' })
    }
  },
  component: AdminLayout,
})

function AdminLayout() {
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="max-w-7xl mx-auto space-y-12 pb-20">
      {/* Header */}
      <header className="bg-retro-dark p-8 rounded-2xl border-b-8 border-retro-teal shadow-retro relative overflow-hidden">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-6">
            <div className="bg-retro-yellow p-4 rounded-2xl border-4 border-retro-dark shadow-retro-sm transform -rotate-3">
              <ShieldAlert className="w-10 h-10 text-retro-dark" />
            </div>
            <div>
              <h1 className="text-4xl font-display text-retro-cream uppercase italic tracking-tighter">
                Control Center
              </h1>
              <p className="font-display text-retro-teal text-lg tracking-widest uppercase mt-1">Series 2000 Administrative Interface</p>
            </div>
          </div>
          <Link
            to="/"
            className="flex items-center gap-2 px-6 py-2 bg-retro-pink text-retro-dark font-display text-lg uppercase rounded-xl border-4 border-retro-dark shadow-retro-sm hover:bg-pink-400 active:shadow-none active:translate-x-1 active:translate-y-1 transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
            Exit Command
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
        {/* Admin Sidebar */}
        <aside className="space-y-4">
          <div className="bg-white p-6 rounded-2xl border-8 border-retro-dark shadow-retro">
            <h3 className="font-display text-xl text-retro-dark uppercase mb-6 border-b-4 border-retro-dark border-dashed pb-2">
              Navigation
            </h3>
            <nav className="flex flex-col gap-2">
              <AdminNavLink
                to="/admin"
                icon={<LayoutDashboard className="w-5 h-5" />}
                label="Dashboard"
                active={isActive('/admin')}
              />
              <AdminNavLink
                to="/admin/users"
                icon={<Users className="w-5 h-5" />}
                label="Citizens"
                active={isActive('/admin/users')}
              />
              <AdminNavLink
                to="/admin/playlists"
                icon={<Music className="w-5 h-5" />}
                label="Archives"
                active={isActive('/admin/playlists')}
              />
              <AdminNavLink
                to="/admin/connections"
                icon={<Link2 className="w-5 h-5" />}
                label="Relay Stations"
                active={isActive('/admin/connections')}
              />
            </nav>
          </div>

          <div className="bg-retro-cream p-6 rounded-2xl border-8 border-retro-dark shadow-retro">
            <h3 className="text-lg font-display text-retro-dark uppercase mb-4">System Status</h3>
            <div className="space-y-3 font-body font-bold text-xs uppercase tracking-wider text-retro-dark/70">
              <StatusItem label="Core Temp" value="Optimal" color="teal" />
              <StatusItem label="AI Synapse" value="Stabilized" color="teal" />
              <StatusItem label="Citizens" value="Elevated" color="pink" />
            </div>
          </div>
        </aside>

        {/* Admin Content */}
        <main className="lg:col-span-3">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

interface AdminNavLinkProps {
  to: string
  icon: React.ReactNode
  label: string
  active: boolean
}

function AdminNavLink({ to, icon, label, active }: AdminNavLinkProps) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl border-4 border-transparent transition-all font-display text-lg uppercase ${
        active
          ? 'bg-retro-teal text-retro-dark border-retro-dark shadow-retro-xs translate-x-1'
          : 'hover:bg-retro-teal/10 hover:translate-x-1 text-retro-dark/60'
      }`}
    >
      {icon}
      {label}
    </Link>
  )
}

interface StatusItemProps {
  label: string
  value: string
  color: 'teal' | 'pink'
}

function StatusItem({ label, value, color }: StatusItemProps) {
  const colors: Record<string, string> = {
    teal: 'text-retro-teal',
    pink: 'text-retro-pink',
  }
  return (
    <div className="flex justify-between items-center bg-white/50 p-2 rounded border-2 border-retro-dark/10">
      <span>{label}</span>
      <span className={colors[color]}>{value}</span>
    </div>
  )
}
