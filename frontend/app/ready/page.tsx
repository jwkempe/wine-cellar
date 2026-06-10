'use client'

import { useQuery } from '@tanstack/react-query'
import { getBottles } from '@/lib/api'
import { isReady } from '@/lib/wine'
import Link from 'next/link'
import PageHeader from '../components/PageHeader'

export default function ReadyToDrink() {
  const { data: bottles, isLoading, isError } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })

  if (isLoading) return <p className="text-[#f0ead8]/40">Loading...</p>
  if (isError) return <p className="text-red-400/70 text-sm">Could not load your cellar. Please refresh the page.</p>

  const ready = bottles?.filter(isReady) ?? []

  return (
    <div>
      <PageHeader title="Ready to Drink" subtitle="In their drinking window now" />

      {ready.length === 0 ? (
        <p className="text-[#f0ead8]/40">Nothing is currently in its drinking window.</p>
      ) : (
        <>
          <p className="text-sm text-[#5a8a5a] mb-6">{ready.length} bottle{ready.length !== 1 ? 's' : ''} ready to drink right now.</p>
          <div className="grid gap-2">
            {ready.map(bottle => (
              <Link href={`/bottle/${bottle.id}`} key={bottle.id}>
                <div className="border border-[#2e2a25] rounded p-4 bg-[#161412] hover:bg-[#1c1917] transition-colors cursor-pointer">
                  <div className="flex justify-between items-start gap-3">
                    <div className="min-w-0">
                      <span className="text-[#f0ead8] text-lg font-light">
                        {bottle.winery}{bottle.wine_name ? ` ${bottle.wine_name}` : ''}
                      </span>
                      <span className="text-[#f0ead8]/40 text-sm ml-3">{bottle.vintage ?? 'NV'}</span>
                      <p className="text-[#f0ead8]/35 text-xs mt-1 tracking-wide">
                        {[bottle.varietal, bottle.region].filter(Boolean).join(' · ')}
                      </p>
                    </div>
                    <span className="text-xs text-[#5a8a5a] border border-[#5a8a5a]/50 rounded px-1.5 py-0.5 shrink-0">
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
