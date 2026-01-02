import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Disc, Music, Globe, Lock } from 'lucide-react'
import { DataTable } from '../components/DataTable'
import { type ColumnDef } from '@tanstack/react-table'

export const Route = createFileRoute('/admin/playlists')({
  component: AdminPlaylists,
})

interface AdminPlaylist {
  id: string
  name: string
  description: string
  public: boolean
  user_id: string
}

function AdminPlaylists() {
  const { data: playlists, isLoading } = useQuery<AdminPlaylist[]>({
    queryKey: ['admin-playlists'],
    queryFn: async () => {
      const res = await fetch('/api/v1/admin/playlists')
      if (!res.ok) throw new Error('Unauthorized')
      return res.json()
    }
  })

  const columns = React.useMemo<ColumnDef<AdminPlaylist>[]>(
    () => [
      {
        accessorKey: 'name',
        header: 'Playlist',
        cell: ({ row }) => (
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white rounded-lg border-2 border-retro-dark">
              <Music className="w-5 h-5 text-retro-dark" />
            </div>
            <div>
              <div className="font-body font-bold text-retro-dark leading-tight">{row.original.name}</div>
              <div className="text-xs text-retro-dark/60 font-body italic">{row.original.description || 'No description'}</div>
            </div>
          </div>
        ),
      },
      {
        accessorKey: 'public',
        header: 'Visibility',
        cell: (info) => info.getValue() ? (
          <div className="flex items-center gap-2 text-retro-teal font-display text-sm">
            <Globe className="w-4 h-4" /> BROADCAST
          </div>
        ) : (
          <div className="flex items-center gap-2 text-retro-dark/40 font-display text-sm">
            <Lock className="w-4 h-4" /> PRIVATE
          </div>
        ),
      },
      {
        accessorKey: 'user_id',
        header: 'Citizen ID',
        cell: (info) => <span className="font-body text-xs text-retro-dark/60">{info.getValue() as string}</span>
      }
    ],
    []
  )

  if (isLoading) return <div className="flex justify-center p-20"><Disc className="animate-spin w-12 h-12 text-retro-teal" /></div>

  return (
    <div className="space-y-8">
      <h2 className="text-4xl font-display text-retro-dark uppercase italic tracking-tight">
        Archive Surveillance
      </h2>

      <DataTable
        data={playlists ?? []}
        columns={columns}
        searchPlaceholder="Search archives..."
        accentColor="pink"
      />
    </div>
  )
}
