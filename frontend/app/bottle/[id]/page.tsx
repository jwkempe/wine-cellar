'use client'

import { useQuery } from '@tanstack/react-query'
import { getBottles } from '@/lib/api'
import { isReady } from '@/lib/wine'
import { useStreamingCompletion } from '@/lib/useStream'
import { useParams } from 'next/navigation'
import Link from 'next/link'

function money(n: number | null): string {
  return n != null ? `$${n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}` : '—'
}

function formatDate(dateStr: string | null): string | null {
  if (!dateStr) return null
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-1">{label}</p>
      <p className="text-[#f0ead8]/80 text-sm">{children}</p>
    </div>
  )
}

export default function BottleDetail() {
  const params = useParams()
  const id = parseInt(params.id as string)

  const { data: bottles, isLoading, isError } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })
  const bottle = bottles?.find(b => b.id === id)

  const pairing = useStreamingCompletion()

  if (isLoading) return <p className="text-[#f0ead8]/40 text-sm">Loading...</p>
  if (isError) return <p className="text-red-400/70 text-sm">Could not load this bottle. Please go back and try again.</p>
  if (!bottle) return <p className="text-[#f0ead8]/40 text-sm">Bottle not found.</p>

  const valueUpdated = formatDate(bottle.market_value_updated)

  return (
    <div className="max-w-2xl">
      <Link href="/" className="text-xs text-[#f0ead8]/30 hover:text-[#f0ead8]/60 transition-colors">← Back to cellar</Link>

      <div className="flex items-start justify-between gap-4 mt-4 mb-8">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold text-[#f0ead8] tracking-tight">
            {bottle.winery}{bottle.wine_name ? ` ${bottle.wine_name}` : ''}
          </h1>
          <p className="text-sm text-[#f0ead8]/40 mt-1">
            {bottle.vintage ?? 'Non-Vintage'}
            {bottle.varietal ? ` · ${bottle.varietal}` : ''}
            {isReady(bottle) && (
              <span className="ml-3 text-xs text-[#5a8a5a] border border-[#5a8a5a]/40 rounded px-1.5 py-0.5 align-middle">
                Ready to drink
              </span>
            )}
          </p>
        </div>
        <Link
          href={`/edit/${bottle.id}`}
          className="shrink-0 text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors"
        >
          Edit
        </Link>
      </div>

      {/* Details */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-5 border-t border-[#2e2a25] pt-6 mb-6">
        <Field label="Region">{bottle.region || '—'}</Field>
        <Field label="Appellation">{bottle.appellation || '—'}</Field>
        <Field label="Quantity">{bottle.quantity}</Field>
        <Field label="Drink Window">
          {bottle.drink_from && bottle.drink_by ? `${bottle.drink_from}–${bottle.drink_by}` : '—'}
        </Field>
        <Field label="Your Rating">{bottle.your_rating != null ? bottle.your_rating : '—'}</Field>
        <Field label="Paid (per bottle)">{money(bottle.purchase_price)}</Field>
        <Field label="Est. Value (per bottle)">
          {money(bottle.market_value)}
          {valueUpdated && bottle.market_value != null && (
            <span className="block text-xs text-[#f0ead8]/25 mt-0.5">est. {valueUpdated}</span>
          )}
        </Field>
      </div>

      {bottle.your_notes && (
        <div className="border-t border-[#2e2a25] pt-6 mb-6">
          <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-2">Your Notes</p>
          <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{bottle.your_notes}</p>
        </div>
      )}

      {bottle.expert_notes && (
        <div className="border-t border-[#2e2a25] pt-6 mb-6">
          <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-2">Expert Notes</p>
          <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{bottle.expert_notes}</p>
        </div>
      )}

      {/* Inline pairing */}
      <div className="border-t border-[#2e2a25] pt-6">
        <button
          onClick={() => pairing.run(`/ai/pairing/${bottle.id}`)}
          disabled={pairing.loading}
          className="text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {pairing.loading ? 'Consulting the sommelier...' : 'Suggest food pairings'}
        </button>
        {pairing.error && <p className="text-red-400/70 text-sm mt-4">{pairing.error}</p>}
        {pairing.text && (
          <div className="border border-[#2e2a25] rounded p-6 bg-[#161412] mt-4">
            <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">Pairing Suggestions</p>
            <p className="text-[#f0ead8]/70 text-sm leading-relaxed whitespace-pre-wrap">{pairing.text}</p>
          </div>
        )}
      </div>
    </div>
  )
}
