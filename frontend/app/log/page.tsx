'use client'

import { useQuery } from '@tanstack/react-query'
import { getLog, LogEntry } from '@/lib/api'

function formatDate(dateStr: string | null) {
  if (!dateStr) return '—'
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function DrinkLog() {
  const { data: log, isLoading, isError } = useQuery({
    queryKey: ['log'],
    queryFn: getLog,
  })

  if (isLoading) return <p className="text-[#f0ead8]/40 text-sm">Loading your drink log...</p>
  if (isError) return <p className="text-red-400/70 text-sm">Could not load your drink log.</p>

  return (
    <div className="min-w-0">
      <h1 className="text-2xl font-semibold text-[#f0ead8] mb-1 tracking-tight">Drink Log</h1>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-6">Bottles consumed</p>

      {!log?.length ? (
        <p className="text-[#f0ead8]/40 text-sm">No bottles logged yet. Open a bottle and record it from the edit page.</p>
      ) : (
        <div className="overflow-x-auto -mx-4 lg:mx-0">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-[#2e2a25]">
                {['Date', 'Wine', 'Vintage', 'Varietal', 'Qty', 'Notes'].map(h => (
                  <th key={h} className="py-2 pr-6 text-left text-xs font-normal tracking-widest uppercase text-[#f0ead8]/30 whitespace-nowrap first:pl-4 lg:first:pl-0">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {log.map((entry: LogEntry) => (
                <tr key={entry.id} className="border-b border-[#1a1714]">
                  <td className="py-3 pr-6 pl-4 lg:pl-0 text-[#f0ead8]/45 tabular-nums whitespace-nowrap">
                    {formatDate(entry.consumed_on)}
                  </td>
                  <td className="py-3 pr-6 text-[#f0ead8] font-medium">
                    {entry.winery}{entry.wine_name ? ` ${entry.wine_name}` : ''}
                  </td>
                  <td className="py-3 pr-6 text-[#f0ead8]/45 tabular-nums">
                    {entry.vintage ?? 'NV'}
                  </td>
                  <td className="py-3 pr-6 text-[#f0ead8]/45">
                    {entry.varietal ?? '—'}
                  </td>
                  <td className="py-3 pr-6 text-[#f0ead8]/45 tabular-nums">
                    {entry.quantity}
                  </td>
                  <td className="py-3 text-[#f0ead8]/40 text-xs max-w-xs truncate">
                    {entry.notes ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-[#f0ead8]/20 mt-4">
            {log.length} entr{log.length !== 1 ? 'ies' : 'y'}
          </p>
        </div>
      )}
    </div>
  )
}
