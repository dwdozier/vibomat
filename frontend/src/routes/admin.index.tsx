import { createFileRoute, Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Users, Music, Link2, Database, Disc } from 'lucide-react'

export const Route = createFileRoute('/admin/')({
  component: AdminDashboard,
})

function AdminDashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const res = await fetch('/api/v1/admin/stats')
      if (!res.ok) throw new Error('Unauthorized')
      return res.json()
    }
  })

  if (isLoading) return <div className="flex justify-center p-20"><Disc className="animate-spin w-12 h-12 text-retro-teal" /></div>

  return (
    <div className="space-y-12">
      {/* Stats Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <StatCard
          icon={<Users className="w-8 h-8 text-retro-teal" />}
          label="Citizens"
          value={stats?.users}
          color="teal"
          to="/admin/users"
        />
        <StatCard
          icon={<Music className="w-8 h-8 text-retro-pink" />}
          label="Archives"
          value={stats?.playlists}
          color="pink"
          to="/admin/playlists"
        />
        <StatCard
          icon={<Link2 className="w-8 h-8 text-retro-yellow" />}
          label="Relays"
          value={stats?.connections}
          color="yellow"
          to="/admin/connections"
        />
        <StatCard
          icon={<Database className="w-8 h-8 text-retro-chrome" />}
          label="Nodes"
          value={stats?.oauth_accounts}
          color="chrome"
        />
      </section>
      <div className="bg-white p-8 rounded-2xl border-8 border-retro-dark shadow-retro">
        <h2 className="text-3xl font-display text-retro-dark mb-6 uppercase border-b-4 border-retro-dark pb-4 border-dashed">
          System Overview
        </h2>
        <p className="font-body text-xl text-retro-dark/80 leading-relaxed italic">
          The Series 2000 Administrative Interface is fully operational. All sectors reporting optimal performance.
          Use the navigation menu to oversee Citizens, monitor the Archives, and manage Relay Stations.
        </p>
      </div>
    </div>
  )
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value?: number
  color: 'teal' | 'pink' | 'yellow' | 'chrome'
  to?: string
}

function StatCard({ icon, label, value, color, to }: StatCardProps) {
  const colorMap: Record<string, string> = {
    teal: 'bg-retro-teal/10 border-retro-teal',
    pink: 'bg-retro-pink/10 border-retro-pink',
    yellow: 'bg-retro-yellow/10 border-retro-yellow',
    chrome: 'bg-retro-chrome/10 border-retro-chrome',
  }

  const content = (
    <div className={`p-8 rounded-2xl border-4 border-retro-dark shadow-retro-sm flex items-center gap-6 w-full h-full transition-all ${colorMap[color]} ${to ? 'group-hover:shadow-retro group-hover:-translate-y-1 group-active:translate-x-1 group-active:translate-y-1 group-active:shadow-none' : ''}`}>
      <div className="p-4 bg-white rounded-xl border-2 border-retro-dark shadow-retro-xs">
        {icon}
      </div>
      <div className="space-y-1 text-left">
        <div className="text-5xl font-display text-retro-dark tracking-tighter">
          {value ?? '---'}
        </div>
        <div className="text-sm font-display text-retro-dark/60 uppercase tracking-widest">
          {label}
        </div>
      </div>
    </div>
  )

  if (to) {
    return (
      <Link to={to} className="group block h-full">
        {content}
      </Link>
    )
  }

  return content
}
