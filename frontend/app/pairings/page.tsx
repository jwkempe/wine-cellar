'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getBottles } from '@/lib/api'
import { useStreamingCompletion } from '@/lib/useStream'
import PageHeader from '../components/PageHeader'

export default function FoodPairings() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const { text, loading, error, run, reset } = useStreamingCompletion()

  const { data: bottles, isError: bottlesError } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })

  const selectClass = "w-full bg-[#0f0d0b] border border-[#2e2a25] rounded px-3 py-2 text-[#f0ead8] text-sm focus:outline-none focus:border-[#c9a84c]/50"

  return (
    <div className="max-w-2xl">
      <PageHeader title="Food Pairings" subtitle="Sommelier recommendations" />

      {bottlesError && (
        <p className="text-red-400/70 text-sm mb-4">Could not load your bottles. Please refresh the page.</p>
      )}

      <div className="mb-4">
        <select
          className={selectClass}
          value={selectedId ?? ''}
          onChange={e => {
            setSelectedId(parseInt(e.target.value))
            reset()
          }}
        >
          <option value="">Select a bottle...</option>
          {bottles?.map(b => (
            <option key={b.id} value={b.id}>
              {b.vintage ?? 'NV'} {b.winery}{b.wine_name ? ` ${b.wine_name}` : ''} — {b.varietal}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={() => selectedId && run(`/ai/pairing/${selectedId}`)}
        disabled={!selectedId || loading}
        className="text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed mb-4"
      >
        {loading ? 'Consulting the sommelier...' : 'Get Pairing Suggestions'}
      </button>

      {error && <p className="text-red-400/70 text-sm mb-4">{error}</p>}

      {text && (
        <div className="border border-[#2e2a25] rounded p-6 bg-[#161412]">
          <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">Pairing Suggestions</p>
          <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{text}</p>
        </div>
      )}
    </div>
  )
}
