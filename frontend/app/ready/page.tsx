'use client'

import { useQuery } from '@tanstack/react-query'
import { getBottles, Bottle } from '@/lib/api'
import Link from 'next/link'

const currentYear = new Date().getFullYear()

export default function ReadyToDrink() {
  const { data: bottles, isLoading } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })

  if (isLoading) return <p className="text-[#f0ead8]/40">Loading...</p>

  const ready = bottles?.filter(b =>
    b.drink_from !== null && b.drink_by !== null &&
    currentYear >= b.drink_from && currentYear <= b.drink_by
  ) ?? []

  return (
    <div>
      <h1 className="text-3xl font-light text-[#f0ead8] mb-1" style={{ fontFamily: 'serif' }}>
        Ready to Drink
      </h1>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-8">In their drinking window now</p>

      {ready.length === 0 ? (
        <p className="text-[#f0ead8]/40">Nothing is currently in its drinking window.</p>
      ) : (
        <>
          <p className="text-sm text-[#5a8a5a] mb-6">{ready.length} bottle{ready.length !== 1 ? 's' : ''} ready to drink right now.</p>
          <div className="grid gap-2">
            {ready.map(bottle => (
              <Link href={`/edit/${bottle.id}`} key={bottle.id}>
                <div className="border border-[#2e2a25] rounded p-4 bg-[#161412] hover:bg-[#1c1917] transition-colors cursor-pointer">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[#f0ead8] text-lg font-light" style={{ fontFamily: 'serif' }}>
                        {bottle.winery}{bottle.wine_name ? ` ${bottle.wine_name}` : ''}
                      </span>
                      <span className="text-[#f0ead8]/40 text-sm ml-3">{bottle.vintage ?? 'NV'}</span>
                      <p className="text-[#f0ead8]/35 text-xs mt-1 tracking-wide">
                        {[bottle.varietal, bottle.region].filter(Boolean).join(' · ')}
                      </p>
                    </div>
                    <span className="text-xs text-[#5a8a5a] border border-[#5a8a5a]/50 rounded px-1.5 py-0.5">
                      Ready
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}