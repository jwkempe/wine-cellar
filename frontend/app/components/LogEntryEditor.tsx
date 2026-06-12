'use client'

import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateLogEntry, deleteLogEntry, LogEntry } from '@/lib/api'
import { inputClass, labelClass } from './BottleForm'

export default function LogEntryEditor({ entry, onClose }: { entry: LogEntry; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [consumedOn, setConsumedOn] = useState(entry.consumed_on ?? new Date().toISOString().slice(0, 10))
  const [quantity, setQuantity] = useState(entry.quantity)
  const [rated, setRated] = useState(entry.rating != null)
  const [rating, setRating] = useState(entry.rating ?? 90)
  const [notes, setNotes] = useState(entry.notes ?? '')

  // Close on Escape.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const update = useMutation({
    mutationFn: () => updateLogEntry(entry.id, {
      quantity,
      consumed_on: consumedOn,
      notes: notes.trim() || null,
      rating: rated ? rating : null,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['log'] }); onClose() },
  })

  const remove = useMutation({
    mutationFn: () => deleteLogEntry(entry.id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['log'] }); onClose() },
  })

  const busy = update.isPending || remove.isPending

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative w-full max-w-md bg-[#0f0d0b] border border-[#2e2a25] rounded-lg p-6 shadow-xl">
        <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-1">Edit Drink</p>
        <h2 className="text-lg font-semibold text-[#f0ead8] mb-5">
          {entry.winery}{entry.wine_name ? ` ${entry.wine_name}` : ''}
          <span className="text-[#f0ead8]/40 text-sm font-normal ml-2">{entry.vintage ?? 'NV'}</span>
        </h2>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className={labelClass}>Date</label>
            <input className={inputClass} type="date" value={consumedOn} onChange={e => setConsumedOn(e.target.value)} />
          </div>
          <div>
            <label className={labelClass}>Bottles</label>
            <input className={inputClass} type="number" min={1} value={quantity} onChange={e => setQuantity(parseInt(e.target.value) || 1)} />
          </div>
        </div>

        <div className="flex items-center gap-3 mb-4">
          <input type="checkbox" id="rated" checked={rated} onChange={e => setRated(e.target.checked)} className="accent-[#c9a84c]" />
          <label htmlFor="rated" className="text-sm text-[#f0ead8]/50">Add a rating</label>
        </div>
        {rated && (
          <div className="mb-4">
            <label className={labelClass}>Rating (0–100)</label>
            <input className={inputClass} type="number" min={0} max={100} step={0.5} value={rating} onChange={e => setRating(parseFloat(e.target.value))} />
          </div>
        )}

        <div className="mb-5">
          <label className={labelClass}>Notes</label>
          <input className={inputClass} placeholder="e.g. Great with dinner" value={notes} onChange={e => setNotes(e.target.value)} />
        </div>

        {(update.isError || remove.isError) && (
          <p className="text-red-400/70 text-sm mb-3">Something went wrong. Please try again.</p>
        )}

        <div className="flex items-center justify-between gap-3">
          <div className="flex gap-3">
            <button
              onClick={() => update.mutate()}
              disabled={busy}
              className="bg-[#c9a84c]/20 border border-[#c9a84c]/40 text-[#c9a84c] px-5 py-2 rounded text-sm tracking-widest uppercase hover:bg-[#c9a84c]/30 transition-colors disabled:opacity-50"
            >
              {update.isPending ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={onClose}
              disabled={busy}
              className="text-sm text-[#f0ead8]/50 px-4 py-2 rounded hover:text-[#f0ead8] transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
          <button
            onClick={() => { if (confirm('Delete this drink log entry?')) remove.mutate() }}
            disabled={busy}
            className="border border-red-900/50 text-red-400/70 px-4 py-2 rounded text-sm tracking-widest uppercase hover:bg-red-900/20 transition-colors disabled:opacity-50"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}
