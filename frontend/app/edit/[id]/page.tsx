'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getBottles, updateBottle, deleteBottle, drinkBottle, lookupWine, BottleInput } from '@/lib/api'
import { useRouter, useParams } from 'next/navigation'

export default function EditBottle() {
  const router = useRouter()
  const params = useParams()
  const id = parseInt(params.id as string)
  const queryClient = useQueryClient()

  const { data: bottles, isLoading, isError } = useQuery({
    queryKey: ['bottles'],
    queryFn: getBottles,
  })

  const bottle = bottles?.find(b => b.id === id)

  const [form, setForm] = useState<Partial<BottleInput>>({})
  const [isNV, setIsNV] = useState(false)
  const [notTried, setNotTried] = useState(true)
  const [drinkQty, setDrinkQty] = useState(1)
  const [drinkDate, setDrinkDate] = useState(new Date().toISOString().slice(0, 10))
  const [drinkNotes, setDrinkNotes] = useState('')
  const [drinkSuccess, setDrinkSuccess] = useState(false)
  const [lookingUp, setLookingUp] = useState(false)
  const [lookupError, setLookupError] = useState<string | null>(null)

  useEffect(() => {
    if (bottle) {
      setForm(bottle)
      setIsNV(bottle.vintage === null)
      setNotTried(bottle.your_rating === null)
    }
  }, [bottle])

  const updateMutation = useMutation({
    mutationFn: (data: BottleInput) => updateBottle(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bottles'] })
      router.push('/')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteBottle(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bottles'] })
      router.push('/')
    },
  })

  const drinkMutation = useMutation({
    mutationFn: () => drinkBottle(id, { quantity: drinkQty, consumed_on: drinkDate, notes: drinkNotes || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bottles'] })
      queryClient.invalidateQueries({ queryKey: ['log'] })
      setDrinkSuccess(true)
      setTimeout(() => router.push('/'), 800)
    },
  })

  function set(field: keyof BottleInput, value: any) {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  async function handleLookup() {
    if (!form.winery || !form.varietal || !form.region) return
    setLookingUp(true)
    setLookupError(null)
    try {
      const params: Record<string, string> = {
        winery: form.winery,
        varietal: form.varietal,
        region: form.region,
      }
      if (form.vintage) params.vintage = String(form.vintage)
      if (form.appellation) params.appellation = form.appellation
      const data = await lookupWine(params)
      const lines = data.result.split('\n')
      for (const line of lines) {
        if (line.startsWith('DRINK_FROM:')) set('drink_from', parseInt(line.replace('DRINK_FROM:', '').trim()))
        if (line.startsWith('DRINK_BY:')) set('drink_by', parseInt(line.replace('DRINK_BY:', '').trim()))
        if (line.startsWith('EXPERT_NOTES:')) set('expert_notes', line.replace('EXPERT_NOTES:', '').trim())
      }
    } catch {
      setLookupError('Could not reach the sommelier. Please try again or fill in the details manually.')
    } finally {
      setLookingUp(false)
    }
  }

  function handleSubmit() {
    const data: BottleInput = {
      winery: form.winery || '',
      wine_name: form.wine_name || null,
      region: form.region || '',
      appellation: form.appellation || null,
      varietal: form.varietal || '',
      vintage: isNV ? null : (form.vintage ?? null),
      quantity: form.quantity ?? 1,
      drink_from: form.drink_from ?? null,
      drink_by: form.drink_by ?? null,
      your_notes: form.your_notes || null,
      your_rating: notTried ? null : (form.your_rating ?? null),
      expert_notes: form.expert_notes || null,
      purchase_price: form.purchase_price ?? null,
    }
    updateMutation.mutate(data)
  }

  if (isLoading) return <p className="text-[#f0ead8]/40">Loading...</p>
  if (isError) return <p className="text-red-400/70 text-sm">Could not load bottle. Please go back and try again.</p>
  if (!bottle) return <p className="text-[#f0ead8]/40">Bottle not found.</p>

  const inputClass = "w-full bg-[#0f0d0b] border border-[#2e2a25] rounded px-3 py-2 text-[#f0ead8] text-sm placeholder-[#f0ead8]/20 focus:outline-none focus:border-[#c9a84c]/50"
  const labelClass = "block text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-1.5"

  return (
    <div className="max-w-2xl">
      <h1 className="text-3xl font-light text-[#f0ead8] mb-1">
        Edit Bottle
      </h1>
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-8">Update your records</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <label className={labelClass}>Winery</label>
          <input className={inputClass} value={form.winery || ''} onChange={e => set('winery', e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Wine Name</label>
          <input className={inputClass} value={form.wine_name || ''} onChange={e => set('wine_name', e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Region</label>
          <input className={inputClass} value={form.region || ''} onChange={e => set('region', e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Appellation</label>
          <input className={inputClass} value={form.appellation || ''} onChange={e => set('appellation', e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>Varietal</label>
          <input className={inputClass} value={form.varietal || ''} onChange={e => set('varietal', e.target.value)} />
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
          disabled={lookingUp || !form.winery || !form.varietal || !form.region}
          className="text-sm border border-[#c9a84c]/40 text-[#c9a84c] px-4 py-2 rounded hover:bg-[#c9a84c]/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed mb-1"
        >
          {lookingUp ? 'Consulting the sommelier...' : 'Lookup Drink Window & Tasting Notes'}
        </button>
        {(!form.winery || !form.varietal || !form.region) && (
          <p className="text-xs text-[#f0ead8]/25 mb-4">Fill in Winery, Varietal, and Region to enable</p>
        )}
        {(form.winery && form.varietal && form.region) && <div className="mb-4" />}
        {lookupError && (
          <p className="text-red-400/70 text-sm mb-4">{lookupError}</p>
        )}
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
        <textarea className={inputClass + ' h-24 resize-none mb-4'} value={form.your_notes || ''} onChange={e => set('your_notes', e.target.value)} />
        <div className="flex items-center gap-3 mb-4">
          <input type="checkbox" id="notTried" checked={notTried} onChange={e => setNotTried(e.target.checked)} className="accent-[#c9a84c]" />
          <label htmlFor="notTried" className="text-sm text-[#f0ead8]/50">I haven't tried this wine yet</label>
        </div>
        {!notTried && (
          <div>
            <label className={labelClass}>Your Rating (0–100)</label>
            <input className={inputClass} type="number" min={0} max={100} step={0.5} value={form.your_rating ?? 90} onChange={e => set('your_rating', parseFloat(e.target.value))} />
          </div>
        )}
      </div>

      <div className="border-t border-[#2e2a25] pt-6 mb-6">
        <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">Log a Drink</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className={labelClass}>Bottles Consumed</label>
            <input className={inputClass} type="number" min={1} max={form.quantity ?? 1} value={drinkQty} onChange={e => setDrinkQty(parseInt(e.target.value))} />
          </div>
          <div>
            <label className={labelClass}>Date</label>
            <input className={inputClass} type="date" value={drinkDate} onChange={e => setDrinkDate(e.target.value)} />
          </div>
        </div>
        <div className="mb-4">
          <label className={labelClass}>Notes (optional)</label>
          <input className={inputClass} placeholder="e.g. Great with dinner" value={drinkNotes} onChange={e => setDrinkNotes(e.target.value)} />
        </div>
        {drinkMutation.isError && (
          <p className="text-red-400/70 text-sm mb-3">Failed to log drink. Please try again.</p>
        )}
        {drinkSuccess && (
          <p className="text-[#5a8a5a] text-sm mb-3">Logged! Redirecting...</p>
        )}
        <button
          onClick={() => drinkMutation.mutate()}
          disabled={drinkMutation.isPending || drinkSuccess}
          className="border border-[#5a8a5a]/50 text-[#5a8a5a] px-5 py-2 rounded text-sm tracking-widest uppercase hover:bg-[#5a8a5a]/10 transition-colors disabled:opacity-50"
        >
          {drinkMutation.isPending ? 'Logging...' : 'Log a Drink'}
        </button>
      </div>

      {updateMutation.isError && (
        <p className="text-red-400/70 text-sm mb-4">Failed to save changes. Please try again.</p>
      )}
      {deleteMutation.isError && (
        <p className="text-red-400/70 text-sm mb-4">Failed to delete bottle. Please try again.</p>
      )}

      <div className="flex gap-3">
        <button
          onClick={handleSubmit}
          disabled={updateMutation.isPending}
          className="bg-[#c9a84c]/20 border border-[#c9a84c]/40 text-[#c9a84c] px-6 py-2.5 rounded text-sm tracking-widest uppercase hover:bg-[#c9a84c]/30 transition-colors disabled:opacity-50"
        >
          {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
        </button>
        <button
          onClick={() => {
            if (confirm('Delete this bottle from your cellar?')) deleteMutation.mutate()
          }}
          disabled={deleteMutation.isPending}
          className="border border-red-900/50 text-red-400/70 px-6 py-2.5 rounded text-sm tracking-widest uppercase hover:bg-red-900/20 transition-colors disabled:opacity-50"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
