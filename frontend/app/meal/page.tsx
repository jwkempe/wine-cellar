'use client'

import { useState } from 'react'
import { getMealPairing, MealPairingResult } from '@/lib/api'

export default function WhatsForDinner() {
  const [meal, setMeal] = useState('')
  const [result, setResult] = useState<MealPairingResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit() {
    if (!meal.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await getMealPairing(meal.trim())
      setResult(data)
    } catch {
      setError('Could not get pairing suggestions. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-light text-[#f0ead8] mb-1">
        What&apos;s for Dinner?
      </h1>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-8">Find the right bottle for your meal</p>

      <div className="mb-4">
        <textarea
          className="w-full bg-[#0f0d0b] border border-[#2e2a25] rounded px-3 py-2 text-[#f0ead8] text-sm focus:outline-none focus:border-[#c9a84c]/50 resize-none"
          rows={3}
          placeholder="e.g. Grilled salmon with lemon butter and roasted asparagus"
          value={meal}
          onChange={e => {
            setMeal(e.target.value)
            setResult(null)
            setError(null)
          }}
        />
      </div>

      <button
        onClick={handleSubmit}
        disabled={!meal.trim() || loading}
        className="text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed mb-4"
      >
        {loading ? 'Consulting the sommelier...' : 'Find a Pairing'}
      </button>

      {error && <p className="text-red-400/70 text-sm mb-4">{error}</p>}

      {result && (
        <div className="flex flex-col gap-4">
          <div className="border border-[#2e2a25] rounded p-6 bg-[#161412]">
            <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">From your cellar</p>
            <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{result.pairings}</p>
          </div>

          {result.gaps && (
            <div className="border border-[#7a3a3a]/40 rounded p-6 bg-[#161412]">
              <p className="text-xs text-[#c47a7a]/60 tracking-widest uppercase mb-4">Gaps in your cellar</p>
              <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{result.gaps}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
