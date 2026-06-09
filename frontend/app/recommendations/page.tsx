'use client'

import { useQuery } from '@tanstack/react-query'
import { getBottles } from '@/lib/api'
import { useStreamingCompletion } from '@/lib/useStream'
import PageHeader from '../components/PageHeader'

export default function Recommendations() {
  const { text, loading, error, run } = useStreamingCompletion()

  const { data: bottles, isError: bottlesError } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })

  return (
    <div className="max-w-2xl">
      <PageHeader title="Recommendations" subtitle="Curated for your palate" />

      {bottlesError && (
        <p className="text-red-400/70 text-sm mb-4">Could not load your bottles. Please refresh the page.</p>
      )}

      {!bottles?.length ? (
        <p className="text-[#f0ead8]/40">Add and rate bottles to unlock personalized recommendations.</p>
      ) : (
        <>
          <p className="text-[#f0ead8]/50 text-sm mb-6">
            Based on your highest-rated bottles, our sommelier will suggest wines you&apos;re likely to love.
          </p>
          <button
            onClick={() => run('/ai/recommendations')}
            disabled={loading}
            className="text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed mb-4"
          >
            {loading ? 'Analyzing your taste profile...' : 'Generate Recommendations'}
          </button>
        </>
      )}

      {error && <p className="text-red-400/70 text-sm mb-4">{error}</p>}

      {text && (
        <div className="border border-[#2e2a25] rounded p-6 bg-[#161412]">
          <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">Recommended For You</p>
          <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{text}</p>
        </div>
      )}
    </div>
  )
}
