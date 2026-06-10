'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getBottles, updateBottle, deleteBottle, drinkBottle, BottleInput } from '@/lib/api'
import { useRouter, useParams } from 'next/navigation'
import PageHeader from '../../components/PageHeader'
import BottleForm, { inputClass, labelClass } from '../../components/BottleForm'

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

  const [drinkQty, setDrinkQty] = useState(1)
  const [drinkDate, setDrinkDate] = useState(new Date().toISOString().slice(0, 10))
  const [drinkNotes, setDrinkNotes] = useState('')
  const [drinkSuccess, setDrinkSuccess] = useState(false)

  const updateMutation = useMutation({
    mutationFn: (data: BottleInput) => updateBottle(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bottles'] })
      router.push(`/bottle/${id}`)
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

  if (isLoading) return <p className="text-[#f0ead8]/40 text-sm">Loading...</p>
  if (isError) return <p className="text-red-400/70 text-sm">Could not load bottle. Please go back and try again.</p>
  if (!bottle) return <p className="text-[#f0ead8]/40 text-sm">Bottle not found.</p>

  const logADrink = (
    <div className="border-t border-[#2e2a25] pt-6 mb-6">
      <p className="text-xs text-[#f0ead8]/30 tracking-widest uppercase mb-4">Log a Drink</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <label className={labelClass}>Bottles Consumed</label>
          <input className={inputClass} type="number" min={1} max={bottle.quantity} value={drinkQty} onChange={e => setDrinkQty(parseInt(e.target.value))} />
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
  )

  const deleteButton = (
    <button
      onClick={() => {
        if (confirm('Delete this bottle from your cellar?')) deleteMutation.mutate()
      }}
      disabled={deleteMutation.isPending}
      className="border border-red-900/50 text-red-400/70 px-6 py-2.5 rounded text-sm tracking-widest uppercase hover:bg-red-900/20 transition-colors disabled:opacity-50"
    >
      Delete
    </button>
  )

  return (
    <div className="max-w-2xl">
      <PageHeader title="Edit Bottle" subtitle="Update your records" />
      <BottleForm
        initial={bottle}
        onSubmit={data => updateMutation.mutate(data)}
        submitting={updateMutation.isPending}
        submitLabel="Save Changes"
        submittingLabel="Saving..."
        saveError={updateMutation.isError || deleteMutation.isError}
        extraSection={logADrink}
        secondaryButton={deleteButton}
      />
    </div>
  )
}
