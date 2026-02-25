'use client'

import { useQuery } from '@tanstack/react-query'
import { getBottles, Bottle } from '@/lib/api'
import Link from 'next/link'

const currentYear = new Date().getFullYear()

function isReady(bottle: Bottle) {
  return bottle.drink_from !== null && bottle.drink_by !== null &&
    currentYear >= bottle.drink_from && currentYear <= bottle.drink_by
}

export default function Home() {
  const { data: bottles, isLoading } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })

  if (isLoading) return <p className="text-[#f0ead8]/40">Loading your cellar...</p>
  if (!bottles?.length) return <p className="text-[#f0ead8]/40">Your cellar is empty. Add your first bottle!</p>

  const totalBottles = bottles.reduce((sum, b) => sum + b.quantity, 0)
  const readyCount = bottles.filter(isReady).length
  const ratings = bottles.map(b => b.your_rating).filter(Boolean) as number[]
  const avgRating = ratings.length ? (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1) : '—'

  return (
    <div>
      <h1 className="text-3xl font-light text-[#f0ead8] mb-1" style={{ fontFamily: 'serif' }}>
        My Cellar
      </h1>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-8">Collection Overview</p>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Total Bottles', value: totalBottles },
          { label: 'Unique Wines', value: bottles.length },
          { label: 'Ready to Drink', value: readyCount },
          { label: 'Avg Rating', value: avgRating },
        ].map(stat => (
          <div key={stat.label} className="border border-[#2e2a25] rounded p-4 bg-[#161412]">
            <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-1">{stat.label}</p>
            <p className="text-2xl font-light text-[#f0ead8]" style={{ fontFamily: 'serif' }}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Bottle list */}
      <div className="grid gap-2">
        {bottles.map(bottle => (
          <Link href={`/edit/${bottle.id}`} key={bottle.id}>
            <div className="border border-[#2e2a25] rounded p-4 bg-[#161412] hover:bg-[#1c1917] transition-colors cursor-pointer">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[#f0ead8] text-lg font-light" style={{ fontFamily: 'serif' }}>
                    {bottle.winery}{bottle.wine_name ? ` ${bottle.wine_name}` : ''}
                  </span>
                  <span className="text-[#f0ead8]/40 text-sm ml-3">
                    {bottle.vintage ?? 'NV'}
                  </span>
                  <p className="text-[#f0ead8]/35 text-xs mt-1 tracking-wide">
                    {[bottle.varietal, bottle.region].filter(Boolean).join(' · ')}
                  </p>
                </div>
                <div className="text-right flex items-center gap-3">
                  <span className="text-[#f0ead8]/30 text-xs">
                    Qty {bottle.quantity}
                  </span>
                  <span className="text-[#f0ead8]/40 text-sm">
                    {bottle.drink_from} – {bottle.drink_by}
                  </span>
                  {isReady(bottle) && (
                    <span className="text-xs text-[#5a8a5a] border border-[#5a8a5a]/50 rounded px-1.5 py-0.5">
                      Ready
                    </span>
                  )}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}