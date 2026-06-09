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

      // Parse Server-Sent Events: events are separated by a blank line, and
      // each delta rides in a JSON-encoded `data:` field.
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let sep: number
        while ((sep = buffer.indexOf('\n\n')) !== -1) {
          const event = buffer.slice(0, sep)
          buffer = buffer.slice(sep + 2)
          for (const line of event.split('\n')) {
            if (!line.startsWith('data:')) continue
            try {
              const piece = JSON.parse(line.slice(5).trimStart())
              if (piece) setText(prev => prev + piece)
            } catch {
              // ignore keep-alives / malformed partial frames
            }
          }
        }
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
