'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getBottles, getPairing } from '@/lib/api'

export default function FoodPairings() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [pairing, setPairing] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: bottles, isError: bottlesError } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })

  async function handleGetPairing() {
    if (!selectedId) return
    setLoading(true)
    setError(null)
    try {
      const data = await getPairing(selectedId)
      setPairing(data.result)
    } catch {
      setError('Could not get pairing suggestions. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const selectClass = "w-full bg-[#0f0d0b] border border-[#2e2a25] rounded px-3 py-2 text-[#f0ead8] text-sm focus:outline-none focus:border-[#c9a84c]/50"

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-light text-[#f0ead8] mb-1">
        Food Pairings
      </h1>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-8">Sommelier recommendations</p>

      {bottlesError && (
        <p className="text-red-400/70 text-sm mb-4">Could not load your bottles. Please refresh the page.</p>
      )}

      <div className="mb-4">
        <select
          className={selectClass}
          value={selectedId ?? ''}
          onChange={e => {
            setSelectedId(parseInt(e.target.value))
            setPairing(null)
            setError(null)
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
        onClick={handleGetPairing}
        disabled={!selectedId || loading}
        className="text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed mb-4"
      >
        {loading ? 'Consulting the sommelier...' : 'Get Pairing Suggestions'}
      </button>

      {error && <p className="text-red-400/70 text-sm mb-4">{error}</p>}

      {pairing && (
        <div className="border border-[#2e2a25] rounded p-6 bg-[#161412]">
          <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">Pairing Suggestions</p>
          <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{pairing}</p>
        </div>
      )}
    </div>
  )
}
