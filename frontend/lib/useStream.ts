'use client'

import { useAuth } from '@clerk/nextjs'
import { useCallback, useState } from 'react'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Streams a text response from a backend AI endpoint, appending tokens to
 * `text` as they arrive so the UI can render the answer live instead of
 * waiting for the whole completion.
 */
export function useStreamingCompletion() {
  const { getToken } = useAuth()
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = useCallback(async (path: string, params?: Record<string, string>) => {
    setText('')
    setError(null)
    setLoading(true)
    try {
      const url = new URL(path, BASE)
      if (params) {
        for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v)
      }
      const token = await getToken()
      const res = await fetch(url.toString(), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        if (chunk) setText(prev => prev + chunk)
      }
    } catch (err) {
      console.error('Stream error:', err)
      setError('Could not reach the sommelier. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [getToken])

  const reset = useCallback(() => {
    setText('')
    setError(null)
  }, [])

  return { text, loading, error, run, reset }
}
