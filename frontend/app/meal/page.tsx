'use client'

import { useState } from 'react'
import { useStreamingCompletion } from '@/lib/useStream'
import PageHeader from '../components/PageHeader'

const GAPS_MARKER = '---GAPS---'

export default function WhatsForDinner() {
  const [meal, setMeal] = useState('')
  const { text, loading, error, run, reset } = useStreamingCompletion()

  // Split the streamed response into its two sections. Until the marker
  // arrives, everything renders in the "from your cellar" box.
  const markerIdx = text.indexOf(GAPS_MARKER)
  const pairings = markerIdx === -1 ? text : text.slice(0, markerIdx)
  const gaps = markerIdx === -1 ? '' : text.slice(markerIdx + GAPS_MARKER.length)

  return (
    <div className="max-w-2xl">
      <PageHeader title="What's for Dinner?" subtitle="Find the right bottle for your meal" />

      <div className="mb-4">
        <textarea
          className="w-full bg-[#0f0d0b] border border-[#2e2a25] rounded px-3 py-2 text-[#f0ead8] text-sm focus:outline-none focus:border-[#c9a84c]/50 resize-none"
          rows={3}
          placeholder="e.g. Grilled salmon with lemon butter and roasted asparagus"
          value={meal}
          onChange={e => {
            setMeal(e.target.value)
            reset()
          }}
        />
      </div>

      <button
        onClick={() => meal.trim() && run('/ai/meal-pairing', { meal: meal.trim() })}
        disabled={!meal.trim() || loading}
        className="text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed mb-4"
      >
        {loading ? 'Consulting the sommelier...' : 'Find a Pairing'}
      </button>

      {error && <p className="text-red-400/70 text-sm mb-4">{error}</p>}

      {text && (
        <div className="flex flex-col gap-4">
          <div className="border border-[#2e2a25] rounded p-6 bg-[#161412]">
            <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">From your cellar</p>
            <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{pairings.trim()}</p>
          </div>

          {gaps.trim() && (
            <div className="border border-[#7a3a3a]/40 rounded p-6 bg-[#161412]">
              <p className="text-xs text-[#c47a7a]/60 tracking-widest uppercase mb-4">Gaps in your cellar</p>
              <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{gaps.trim()}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
