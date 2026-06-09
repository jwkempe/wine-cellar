'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createBottle, BottleInput } from '@/lib/api'
import { useRouter } from 'next/navigation'
import PageHeader from '../components/PageHeader'
import BottleForm from '../components/BottleForm'

export default function AddBottle() {
  const router = useRouter()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (data: BottleInput) => createBottle(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bottles'] })
      router.push('/')
    },
  })

  return (
    <div className="max-w-2xl">
      <PageHeader title="Add a Bottle" subtitle="Catalog a new wine" />
      <BottleForm
        onSubmit={data => mutation.mutate(data)}
        submitting={mutation.isPending}
        submitLabel="Add to Cellar"
        submittingLabel="Adding..."
        saveError={mutation.isError}
      />
    </div>
  )
}
