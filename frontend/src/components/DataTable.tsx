import React from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { Search, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'

interface DataTableProps<T extends object> {
  data: T[]
  columns: ColumnDef<T, unknown>[]
  searchPlaceholder?: string
  accentColor?: 'teal' | 'pink' | 'yellow'
}

export function DataTable<T extends object>({
  data,
  columns,
  searchPlaceholder = "Search records...",
  accentColor = 'teal'
}: DataTableProps<T>) {
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [globalFilter, setGlobalFilter] = React.useState('')

  const table = useReactTable(
    React.useMemo(
      () => ({
        data,
        columns,
        state: {
          sorting,
          globalFilter,
        },
        onSortingChange: setSorting,
        onGlobalFilterChange: setGlobalFilter,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
      }),
      [data, columns, sorting, globalFilter]
    )
  )

  const colorClasses = {
    teal: 'bg-retro-teal text-retro-dark',
    pink: 'bg-retro-pink text-retro-dark',
    yellow: 'bg-retro-yellow text-retro-dark',
  }

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="flex items-center gap-4 bg-white p-4 rounded-xl border-4 border-retro-dark shadow-retro-sm">
        <Search className="w-6 h-6 text-retro-dark/40" />
        <input
          type="text"
          value={globalFilter ?? ''}
          onChange={(e) => setGlobalFilter(e.target.value)}
          placeholder={searchPlaceholder}
          className="flex-grow bg-transparent border-none focus:outline-none font-body font-bold text-lg text-retro-dark placeholder-retro-dark/20"
        />
        <div className="text-xs font-display uppercase tracking-widest text-retro-dark/40 px-3 py-1 border-2 border-retro-dark/10 rounded-lg">
          {table.getFilteredRowModel().rows.length} Records Found
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-white rounded-2xl border-8 border-retro-dark overflow-hidden shadow-retro overflow-x-auto">
        <table className="min-w-full divide-y-4 divide-retro-dark">
          <thead className={colorClasses[accentColor]}>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-6 py-4 text-left font-display uppercase tracking-widest border-r-4 border-retro-dark last:border-r-0 cursor-pointer select-none group"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-2">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      <span className="text-retro-dark/30 group-hover:text-retro-dark transition-colors">
                        {{
                          asc: <ChevronUp className="w-4 h-4" />,
                          desc: <ChevronDown className="w-4 h-4" />,
                        }[header.column.getIsSorted() as string] ?? <ChevronsUpDown className="w-4 h-4 opacity-20" />}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y-4 divide-retro-dark bg-retro-cream">
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="hover:bg-retro-teal/5 transition-colors group">
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className="px-6 py-4 border-r-4 border-retro-dark last:border-r-0"
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="px-6 py-20 text-center">
                  <div className="font-display text-2xl text-retro-dark/20 uppercase tracking-widest">
                    No data detected in this sector
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
