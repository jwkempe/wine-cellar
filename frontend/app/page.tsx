'use client'

import { useQuery } from '@tanstack/react-query'
import { getBottles, Bottle } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { useState, useMemo } from 'react'

const currentYear = new Date().getFullYear()

function isReady(bottle: Bottle) {
  return bottle.drink_from !== null && bottle.drink_by !== null &&
    currentYear >= bottle.drink_from && currentYear <= bottle.drink_by
}

type SortKey = 'wine' | 'vintage' | 'varietal' | 'region' | 'quantity' | 'window' | 'rating'

const columns: { key: SortKey; label: string; className?: string }[] = [
  { key: 'wine',     label: 'Wine' },
  { key: 'vintage',  label: 'Vintage' },
  { key: 'varietal', label: 'Varietal' },
  { key: 'region',   label: 'Region',   className: 'hidden lg:table-cell' },
  { key: 'quantity', label: 'Qty',      className: 'text-right' },
  { key: 'window',   label: 'Window',   className: 'hidden md:table-cell' },
  { key: 'rating',   label: 'Rating',   className: 'text-right hidden sm:table-cell' },
]

function sortBottles(bottles: Bottle[], key: SortKey, asc: boolean): Bottle[] {
  return [...bottles].sort((a, b) => {
    let av: any, bv: any
    if (key === 'wine')     { av = a.winery ?? ''; bv = b.winery ?? '' }
    if (key === 'vintage')  { av = a.vintage ?? 0; bv = b.vintage ?? 0 }
    if (key === 'varietal') { av = a.varietal ?? ''; bv = b.varietal ?? '' }
    if (key === 'region')   { av = a.region ?? ''; bv = b.region ?? '' }
    if (key === 'quantity') { av = a.quantity; bv = b.quantity }
    if (key === 'window')   { av = a.drink_from ?? 0; bv = b.drink_from ?? 0 }
    if (key === 'rating')   { av = a.your_rating ?? 0; bv = b.your_rating ?? 0 }
    if (typeof av === 'string') return asc ? av.localeCompare(bv) : bv.localeCompare(av)
    return asc ? av - bv : bv - av
  })
}

export default function Home() {
  const router = useRouter()
  const { data: bottles, isLoading, isError } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })

  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('wine')
  const [sortAsc, setSortAsc] = useState(true)

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(key === 'rating' || key === 'quantity' ? false : true) }
  }

  const filtered = useMemo(() => {
    if (!bottles) return []
    const q = search.toLowerCase()
    const results = q
      ? bottles.filter(b =>
          [b.winery, b.wine_name, b.varietal, b.region].some(v => v?.toLowerCase().includes(q))
        )
      : bottles
    return sortBottles(results, sortKey, sortAsc)
  }, [bottles, search, sortKey, sortAsc])

  if (isLoading) return <p className="text-[#f0ead8]/40 text-sm">Loading your cellar...</p>
  if (isError) return <p className="text-red-400/70 text-sm">Could not load your cellar. Please check your connection and refresh.</p>
  if (!bottles?.length) return <p className="text-[#f0ead8]/40 text-sm">Your cellar is empty. Add your first bottle!</p>

  const totalBottles = bottles.reduce((sum, b) => sum + b.quantity, 0)
  const readyCount = bottles.filter(isReady).length
  const ratings = bottles.map(b => b.your_rating).filter(Boolean) as number[]
  const avgRating = ratings.length
    ? (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1)
    : '—'

  return (
    <div className="min-w-0">
      <h1 className="text-2xl font-semibold text-[#f0ead8] mb-1 tracking-tight">My Cellar</h1>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-6">Collection Overview</p>

      {/* Stats */}
      <div className="flex gap-6 mb-8 text-sm">
        {[
          { label: 'Bottles', value: totalBottles },
          { label: 'Wines', value: bottles.length },
          { label: 'Ready', value: readyCount },
          { label: 'Avg Rating', value: avgRating },
        ].map((s, i) => (
          <div key={s.label} className={`${i > 0 ? 'pl-6 border-l border-[#2e2a25]' : ''}`}>
            <p className="text-xl font-semibold text-[#f0ead8] tabular-nums">{s.value}</p>
            <p className="text-xs text-[#f0ead8]/30 mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search wines..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full max-w-sm bg-transparent border border-[#2e2a25] rounded-md px-3 py-1.5 text-sm text-[#f0ead8] placeholder-[#f0ead8]/25 focus:outline-none focus:border-[#f0ead8]/30 transition-colors"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto -mx-4 lg:mx-0">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-[#2e2a25]">
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={`py-2 pr-6 text-left text-xs font-normal tracking-widest uppercase text-[#f0ead8]/30 hover:text-[#f0ead8]/60 cursor-pointer select-none transition-colors whitespace-nowrap first:pl-4 lg:first:pl-0 ${col.className ?? ''} ${sortKey === col.key ? 'text-[#c9a84c]/70' : ''}`}
                >
                  {col.label}
                  <span className="ml-1 opacity-60">
                    {sortKey === col.key ? (sortAsc ? '↑' : '↓') : ''}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-[#f0ead8]/25 text-sm pl-4 lg:pl-0">
                  No wines match your search.
                </td>
              </tr>
            ) : filtered.map(bottle => (
              <tr
                key={bottle.id}
                onClick={() => router.push(`/edit/${bottle.id}`)}
                className="border-b border-[#1a1714] hover:bg-[#161412] cursor-pointer transition-colors"
              >
                <td className="py-3 pr-6 pl-4 lg:pl-0">
                  <span className="text-[#f0ead8] font-medium">
                    {bottle.winery}{bottle.wine_name ? ` ${bottle.wine_name}` : ''}
                  </span>
                  {isReady(bottle) && (
                    <span className="ml-2 text-xs text-[#5a8a5a] border border-[#5a8a5a]/40 rounded px-1.5 py-0.5 align-middle">
                      Ready
                    </span>
                  )}
                </td>
                <td className="py-3 pr-6 text-[#f0ead8]/45 tabular-nums">
                  {bottle.vintage ?? 'NV'}
                </td>
                <td className="py-3 pr-6 text-[#f0ead8]/45">
                  {bottle.varietal ?? '—'}
                </td>
                <td className="py-3 pr-6 text-[#f0ead8]/45 hidden lg:table-cell">
                  {bottle.region ?? '—'}
                </td>
                <td className="py-3 pr-6 text-[#f0ead8]/45 tabular-nums text-right">
                  {bottle.quantity}
                </td>
                <td className="py-3 pr-6 text-[#f0ead8]/45 tabular-nums hidden md:table-cell">
                  {bottle.drink_from && bottle.drink_by
                    ? `${bottle.drink_from}–${bottle.drink_by}`
                    : '—'}
                </td>
                <td className="py-3 text-[#f0ead8]/45 tabular-nums text-right hidden sm:table-cell">
                  {bottle.your_rating ?? '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length > 0 && (
        <p className="text-xs text-[#f0ead8]/20 mt-4">
          {filtered.length} of {bottles.length} wine{bottles.length !== 1 ? 's' : ''}
        </p>
      )}
    </div>
  )
}
