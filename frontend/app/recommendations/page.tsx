'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getBottles, getRecommendations } from '@/lib/api'

export default function Recommendations() {
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const { data: bottles } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })

  async function handleGenerate() {
    setLoading(true)
    try {
      const data = await getRecommendations()
      setResult(data.result)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-light text-[#f0ead8] mb-1" style={{ fontFamily: 'serif' }}>
        Recommendations
      </h1>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-8">Curated for your palate</p>

      {!bottles?.length ? (
        <p className="text-[#f0ead8]/40">Add and rate bottles to unlock personalized recommendations.</p>
      ) : (
        <>
          <p className="text-[#f0ead8]/50 text-sm mb-6">
            Based on your highest-rated bottles, our sommelier will suggest wines you're likely to love.
          </p>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed mb-6"
          >
            {loading ? 'Analyzing your taste profile...' : 'Generate Recommendations'}
          </button>
        </>
      )}

      {result && (
        <div className="border border-[#2e2a25] rounded p-6 bg-[#161412]">
          <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">Recommended For You</p>
          <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{result}</p>
        </div>
      )}
    </div>
  )
}