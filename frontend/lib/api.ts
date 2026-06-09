import axios from 'axios'

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
})

export type Bottle = {
  id: number
  winery: string
  wine_name: string | null
  varietal: string
  region: string
  appellation: string | null
  vintage: number | null
  quantity: number
  drink_from: number | null
  drink_by: number | null
  your_notes: string | null
  your_rating: number | null
  expert_notes: string | null
  purchase_price: number | null
}

export type BottleInput = Omit<Bottle, 'id'>

export type LogEntry = {
  id: number
  bottle_id: number | null
  winery: string | null
  wine_name: string | null
  vintage: number | null
  varietal: string | null
  region: string | null
  quantity: number
  consumed_on: string | null
  notes: string | null
}

export type DrinkEntryInput = {
  quantity: number
  consumed_on: string
  notes?: string | null
}

export const getBottles = () => api.get<Bottle[]>('/bottles').then(r => r.data)
export const createBottle = (b: BottleInput) => api.post('/bottles', b)
export const updateBottle = (id: number, b: BottleInput) => api.put(`/bottles/${id}`, b)
export const deleteBottle = (id: number) => api.delete(`/bottles/${id}`)
export const drinkBottle = (id: number, entry: DrinkEntryInput) => api.post(`/bottles/${id}/drink`, entry)
export const getLog = () => api.get<LogEntry[]>('/log').then(r => r.data)
export const lookupWine = (params: Record<string, string>) => api.get('/ai/lookup', { params }).then(r => r.data)

// The AI free-text endpoints (pairing, recommendations, meal-pairing) stream
// their responses — see lib/useStream.ts, which consumes them via fetch.

export type WineLookupFields = {
  drink_from?: number
  drink_by?: number
  expert_notes?: string
}

// Parse the sommelier lookup response (DRINK_FROM / DRINK_BY / EXPERT_NOTES lines).
export function parseLookupResult(result: string): WineLookupFields {
  const fields: WineLookupFields = {}
  for (const line of result.split('\n')) {
    if (line.startsWith('DRINK_FROM:')) {
      const year = parseInt(line.replace('DRINK_FROM:', '').trim())
      if (!Number.isNaN(year)) fields.drink_from = year
    } else if (line.startsWith('DRINK_BY:')) {
      const year = parseInt(line.replace('DRINK_BY:', '').trim())
      if (!Number.isNaN(year)) fields.drink_by = year
    } else if (line.startsWith('EXPERT_NOTES:')) {
      fields.expert_notes = line.replace('EXPERT_NOTES:', '').trim()
    }
  }
  return fields
}
