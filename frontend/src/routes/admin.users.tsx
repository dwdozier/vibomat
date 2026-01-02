import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Disc, User, ShieldCheck, ShieldAlert } from 'lucide-react'
import { type User as UserType } from '../api/auth'
import { DataTable } from '../components/DataTable'
import { type ColumnDef } from '@tanstack/react-table'

export const Route = createFileRoute('/admin/users')({
  component: AdminUsers,
})

function AdminUsers() {
  const { data: users, isLoading } = useQuery<UserType[]>({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const res = await fetch('/api/v1/admin/users')
      if (!res.ok) throw new Error('Unauthorized')
      return res.json()
    }
  })

  const columns = React.useMemo<ColumnDef<UserType>[]>(
    () => [
      {
        accessorKey: 'email',
        header: 'Citizen',
        cell: (info) => (
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white rounded-lg border-2 border-retro-dark">
              <User className="w-5 h-5 text-retro-dark" />
            </div>
            <div className="font-body font-bold text-retro-dark">{info.getValue() as string}</div>
          </div>
        ),
      },
      {
        id: 'status',
        header: 'Status',
        accessorFn: (row) => `${row.is_active} ${row.is_public}`,
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            {row.original.is_active ? (
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-display uppercase border-2 border-green-800/20">Active</span>
            ) : (
              <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-display uppercase border-2 border-red-800/20">Disabled</span>
            )}
            {row.original.is_public ? (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-display uppercase border-2 border-blue-800/20">Public</span>
            ) : (
              <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-display uppercase border-2 border-gray-800/20">Private</span>
            )}
          </div>
        ),
      },
      {
        accessorKey: 'is_superuser',
        header: 'Clearance',
        cell: (info) => (
          <div className="flex items-center gap-2">
            {info.getValue() ? (
              <div className="flex items-center gap-1 text-retro-pink font-display text-sm">
                <ShieldAlert className="w-4 h-4" />
                OVERSEER
              </div>
            ) : (
              <div className="flex items-center gap-1 text-retro-teal font-display text-sm">
                <ShieldCheck className="w-4 h-4" />
                CITIZEN
              </div>
            )}
          </div>
        ),
      }
    ],
    []
  )

  if (isLoading) return <div className="flex justify-center p-20"><Disc className="animate-spin w-12 h-12 text-retro-teal" /></div>

  return (
    <div className="space-y-8">
      <h2 className="text-4xl font-display text-retro-dark uppercase italic tracking-tight">
        Citizen Registry
      </h2>

      <DataTable
        data={users ?? []}
        columns={columns}
        searchPlaceholder="Scan citizen archives..."
        accentColor="teal"
      />
    </div>
  )
}
