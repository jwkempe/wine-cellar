'use client'

import { useAuth } from '@clerk/nextjs'
import { useCallback, useEffect, useRef, useState } from 'react'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Streams a text response from a backend AI endpoint, appending tokens to
 * `text` as they arrive so the UI can render the answer live instead of
 * waiting for the whole completion.
 *
 * The backend frames responses as Server-Sent Events with JSON-encoded
 * `data:` payloads; `event: error` frames carry a user-facing failure
 * message. In-flight requests are aborted on re-run and on unmount, which
 * also stops the backend's generation.
 */
export function useStreamingCompletion() {
  const { getToken } = useAuth()
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const run = useCallback(async (path: string, params?: Record<string, string>) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

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
        signal: controller.signal,
      })
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)

      // Parse Server-Sent Events: events are separated by a blank line; each
      // frame has an optional `event:` name and a JSON-encoded `data:` field.
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let sep: number
        while ((sep = buffer.indexOf('\n\n')) !== -1) {
          const frame = buffer.slice(0, sep)
          buffer = buffer.slice(sep + 2)
          let eventName = 'message'
          const dataLines: string[] = []
          for (const line of frame.split('\n')) {
            if (line.startsWith('event:')) eventName = line.slice(6).trim()
            else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
          }
          for (const data of dataLines) {
            try {
              const piece = JSON.parse(data)
              if (eventName === 'error') setError(piece)
              else if (piece) setText(prev => prev + piece)
            } catch {
              // ignore keep-alives / malformed partial frames
            }
          }
        }
      }
    } catch (err) {
      if (controller.signal.aborted) return // unmounted or superseded — not an error
      console.error('Stream error:', err)
      setError('Could not reach the sommelier. Please try again.')
    } finally {
      if (!controller.signal.aborted) setLoading(false)
    }
  }, [getToken])

  const reset = useCallback(() => {
    setText('')
    setError(null)
  }, [])

  return { text, loading, error, run, reset }
}
