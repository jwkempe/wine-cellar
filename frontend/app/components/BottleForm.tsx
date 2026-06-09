'use client'

import { useState, ReactNode } from 'react'
import { lookupWine, parseLookupResult, BottleInput } from '@/lib/api'

const inputClass = "w-full bg-[#0f0d0b] border border-[#2e2a25] rounded px-3 py-2 text-[#f0ead8] text-sm placeholder-[#f0ead8]/20 focus:outline-none focus:border-[#c9a84c]/50 transition-colors"
const labelClass = "block text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-1.5"

type Props = {
  initial?: Partial<BottleInput>
  onSubmit: (bottle: BottleInput) => void
  submitting: boolean
  submitLabel: string
  submittingLabel: string
  saveError?: boolean
  /** Rendered between the notes section and the action buttons (e.g. Log a Drink). */
  extraSection?: ReactNode
  /** Rendered inline next to the primary submit button (e.g. Delete). */
  secondaryButton?: ReactNode
}

export default function BottleForm({
  initial,
  onSubmit,
  submitting,
  submitLabel,
  submittingLabel,
  saveError,
  extraSection,
  secondaryButton,
}: Props) {
  const [form, setForm] = useState<Partial<BottleInput>>(
    initial ?? { quantity: 1, vintage: 2020 }
  )
  const [isNV, setIsNV] = useState(initial ? initial.vintage === null : false)
  const [notTried, setNotTried] = useState(initial ? initial.your_rating == null : true)
  const [lookingUp, setLookingUp] = useState(false)
  const [lookupError, setLookupError] = useState<string | null>(null)

  function set<K extends keyof BottleInput>(field: K, value: BottleInput[K]) {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  async function handleLookup() {
    if (!form.winery || !form.region) return
    setLookingUp(true)
    setLookupError(null)
    try {
      const params: Record<string, string> = { winery: form.winery, region: form.region }
      if (form.wine_name) params.wine_name = form.wine_name
      if (form.varietal) params.varietal = form.varietal
      if (form.vintage) params.vintage = String(form.vintage)
      if (form.appellation) params.appellation = form.appellation
      const data = await lookupWine(params)
      const fields = parseLookupResult(data.result)
      setForm(prev => ({ ...prev, ...fields }))
    } catch (err) {
      console.error('Lookup error:', err)
      setLookupError('Could not reach the sommelier. Please try again or fill in the details manually.')
    } finally {
      setLookingUp(false)
    }
  }

  // Winery is the one required field (the backend enforces it too).
  const canSubmit = !!form.winery?.trim()

  function handleSubmit() {
    onSubmit({
      winery: (form.winery ?? '').trim(),
      wine_name: form.wine_name?.trim() || null,
      region: (form.region ?? '').trim(),
      appellation: form.appellation?.trim() || null,
      varietal: (form.varietal ?? '').trim(),
      vintage: isNV ? null : (form.vintage ?? null),
      quantity: form.quantity ?? 1,
      drink_from: form.drink_from ?? null,
      drink_by: form.drink_by ?? null,
      your_notes: form.your_notes || null,
      your_rating: notTried ? null : (form.your_rating ?? null),
      expert_notes: form.expert_notes || null,
      purchase_price: form.purchase_price ?? null,
    })
  }

  const lookupDisabled = lookingUp || !form.winery || !form.region

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <label className={labelClass}>Winery</label>
          <input className={inputClass} value={form.winery || ''} onChange={e => set('winery', e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Wine Name</label>
          <input className={inputClass} placeholder="e.g. Reserve" value={form.wine_name || ''} onChange={e => set('wine_name', e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Region</label>
          <input className={inputClass} placeholder="e.g. Napa Valley" value={form.region || ''} onChange={e => set('region', e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Appellation</label>
          <input className={inputClass} placeholder="e.g. Stags Leap District" value={form.appellation || ''} onChange={e => set('appellation', e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Varietal</label>
          <input className={inputClass} placeholder="e.g. Cabernet Sauvignon" value={form.varietal || ''} onChange={e => set('varietal', e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Quantity</label>
          <input className={inputClass} type="number" min={0} value={form.quantity ?? 1} onChange={e => set('quantity', parseInt(e.target.value))} />
        </div>
      </div>

      <div className="mb-4">
        <label className={labelClass}>Purchase Price (per bottle, $)</label>
        <input className={inputClass} type="number" min={0} step={0.01} placeholder="Optional" value={form.purchase_price ?? ''} onChange={e => set('purchase_price', e.target.value ? parseFloat(e.target.value) : null)} />
      </div>

      <div className="flex items-center gap-3 mb-4">
        <input type="checkbox" id="nv" checked={isNV} onChange={e => setIsNV(e.target.checked)} className="accent-[#c9a84c]" />
        <label htmlFor="nv" className="text-sm text-[#f0ead8]/50">Non-Vintage (NV)</label>
      </div>

      {!isNV && (
        <div className="mb-4">
          <label className={labelClass}>Vintage</label>
          <input className={inputClass} type="number" min={1900} max={2100} value={form.vintage ?? 2020} onChange={e => set('vintage', parseInt(e.target.value))} />
        </div>
      )}

      <div className="border-t border-[#2e2a25] pt-6 mt-6 mb-4">
        <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">Drink Window & Tasting Notes</p>
        <button
          onClick={handleLookup}
          disabled={lookupDisabled}
          className="text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed mb-1"
        >
          {lookingUp ? 'Consulting the sommelier...' : 'Lookup Drink Window & Tasting Notes'}
        </button>
        {(!form.winery || !form.region)
          ? <p className="text-xs text-[#f0ead8]/25 mb-4">Fill in Winery and Region to enable</p>
          : <div className="mb-4" />}

        {lookupError && <p className="text-red-400/70 text-sm mb-4">{lookupError}</p>}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className={labelClass}>Drink From</label>
            <input className={inputClass} type="number" value={form.drink_from ?? ''} onChange={e => set('drink_from', parseInt(e.target.value))} />
          </div>
          <div>
            <label className={labelClass}>Drink By</label>
            <input className={inputClass} type="number" value={form.drink_by ?? ''} onChange={e => set('drink_by', parseInt(e.target.value))} />
          </div>
        </div>

        <div>
          <label className={labelClass}>Expert Tasting Notes</label>
          <textarea className={inputClass + ' h-24 resize-none'} value={form.expert_notes || ''} onChange={e => set('expert_notes', e.target.value)} />
        </div>
      </div>

      <div className="border-t border-[#2e2a25] pt-6 mb-6">
        <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">Your Notes</p>
        <textarea className={inputClass + ' h-24 resize-none mb-4'} placeholder="Your tasting notes..." value={form.your_notes || ''} onChange={e => set('your_notes', e.target.value)} />
        <div className="flex items-center gap-3 mb-4">
          <input type="checkbox" id="notTried" checked={notTried} onChange={e => setNotTried(e.target.checked)} className="accent-[#c9a84c]" />
          <label htmlFor="notTried" className="text-sm text-[#f0ead8]/50">I haven&apos;t tried this wine yet</label>
        </div>
        {!notTried && (
          <div>
            <label className={labelClass}>Your Rating (0–100)</label>
            <input className={inputClass} type="number" min={0} max={100} step={0.5} value={form.your_rating ?? 90} onChange={e => set('your_rating', parseFloat(e.target.value))} />
          </div>
        )}
      </div>

      {extraSection}

      {saveError && (
        <p className="text-red-400/70 text-sm mb-4">Failed to save the bottle. Please try again.</p>
      )}

      {!canSubmit && (
        <p className="text-xs text-[#f0ead8]/25 mb-3">Enter a winery to save this bottle</p>
      )}

      <div className="flex gap-3">
        <button
          onClick={handleSubmit}
          disabled={submitting || !canSubmit}
          className="bg-[#c9a84c]/20 border border-[#c9a84c]/40 text-[#c9a84c] px-6 py-2.5 rounded text-sm tracking-widest uppercase hover:bg-[#c9a84c]/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? submittingLabel : submitLabel}
        </button>
        {secondaryButton}
      </div>
    </>
  )
}

export { inputClass, labelClass }
