import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Disc } from 'lucide-react'
import { DataTable } from '../components/DataTable'
import { type ColumnDef } from '@tanstack/react-table'

export const Route = createFileRoute('/admin/connections')({
  component: AdminConnections,
})

interface AdminConnection {
  id: string
  provider_name: string
  user_id: string
  expires_at: string | null
}

function AdminConnections() {
  const { data: connections, isLoading } = useQuery<AdminConnection[]>({
    queryKey: ['admin-connections'],
    queryFn: async () => {
      const res = await fetch('/api/v1/admin/connections')
      if (!res.ok) throw new Error('Unauthorized')
      return res.json()
    }
  })

  const columns = React.useMemo<ColumnDef<AdminConnection>[]>(
    () => [
      {
        accessorKey: 'provider_name',
        header: 'Provider',
        cell: (info) => (
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white rounded-lg border-2 border-retro-dark text-retro-yellow font-bold">
              {(info.getValue() as string).charAt(0).toUpperCase()}
            </div>
            <div className="font-display uppercase text-retro-dark">{info.getValue() as string}</div>
          </div>
        ),
      },
      {
        accessorKey: 'user_id',
        header: 'Citizen ID',
        cell: (info) => <span className="font-body text-xs text-retro-dark/60">{info.getValue() as string}</span>
      },
      {
        accessorKey: 'expires_at',
        header: 'Expiration',
        cell: (info) => (
          <span className="font-body text-sm text-retro-dark">
            {info.getValue() ? new Date(info.getValue() as string).toLocaleString() : 'N/A'}
          </span>
        )
      }
    ],
    []
  )

  if (isLoading) return <div className="flex justify-center p-20"><Disc className="animate-spin w-12 h-12 text-retro-teal" /></div>

  return (
    <div className="space-y-8">
      <h2 className="text-4xl font-display text-retro-dark uppercase italic tracking-tight">
        Relay Station Control
      </h2>

      <DataTable
        data={connections ?? []}
        columns={columns}
        searchPlaceholder="Monitor relay stations..."
        accentColor="yellow"
      />
    </div>
  )
}
