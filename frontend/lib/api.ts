import axios from 'axios'

const api = axios.create({
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
}

export type BottleInput = Omit<Bottle, 'id'>

export const getBottles = () => api.get<Bottle[]>('/bottles').then(r => r.data)
export const createBottle = (b: BottleInput) => api.post('/bottles', b)
export const updateBottle = (id: number, b: BottleInput) => api.put(`/bottles/${id}`, b)
export const deleteBottle = (id: number) => api.delete(`/bottles/${id}`)
export const getPairing = (id: number) => api.get(`/ai/pairing/${id}`).then(r => r.data)
export const getRecommendations = () => api.get('/ai/recommendations').then(r => r.data)
export const lookupWine = (params: Record<string, string>) => api.get('/ai/lookup', { params }).then(r => r.data)