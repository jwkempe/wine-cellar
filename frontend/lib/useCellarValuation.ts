'use client'

import { useAuth } from '@clerk/nextjs'
import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useRef, useState } from 'react'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Drives the bulk "estimate my cellar" flow. The backend streams one SSE event
 * per bottle it prices (and persists as it goes), then a final `done` summary.
 * We refetch the cellar as each result lands so values appear live, and expose
 * a count + summary for progress UI.
 */
export function useCellarValuation() {
  const { getToken } = useAuth()
  const queryClient = useQueryClient()
  const [running, setRunning] = useState(false)
  const [processed, setProcessed] = useState(0)
  const [result, setResult] = useState<{ valued: number; remaining: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const run = useCallback(async () => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setRunning(true)
    setError(null)
    setProcessed(0)
    setResult(null)
    try {
      const token = await getToken()
      const res = await fetch(`${BASE}/ai/estimate-cellar`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      })
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let count = 0
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let sep: number
        while ((sep = buffer.indexOf('\n\n')) !== -1) {
          const frame = buffer.slice(0, sep)
          buffer = buffer.slice(sep + 2)
          let event = 'message'
          const dataLines: string[] = []
          for (const line of frame.split('\n')) {
            if (line.startsWith('event:')) event = line.slice(6).trim()
            else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
          }
          if (event === 'done') {
            try { setResult(JSON.parse(dataLines[0])) } catch { /* ignore */ }
          } else if (dataLines.length) {
            count++
            setProcessed(count)
            // Refetch so newly-priced bottles show up as the run progresses.
            queryClient.invalidateQueries({ queryKey: ['bottles'] })
          }
        }
      }
    } catch (err) {
      if (controller.signal.aborted) return
      console.error('Valuation error:', err)
      setError('Valuation was interrupted. Some bottles may not have been priced.')
    } finally {
      if (!controller.signal.aborted) setRunning(false)
    }
  }, [getToken, queryClient])

  return { running, processed, result, error, run }
}
