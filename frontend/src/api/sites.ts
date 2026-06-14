import api from './axios'

export interface SiteResponse {
  id: number
  name: string
  location: string | null
  city: string | null
  room: string | null
  contact: string | null
  contact_phone: string | null
  status: string
  alert_count: number
  created_at: string
  updated_at: string | null
}

export async function getSites(): Promise<SiteResponse[]> {
  const response = await api.get('/sites/')
  return response.data
}

export async function getSite(id: number): Promise<SiteResponse> {
  const response = await api.get(`/sites/${id}`)
  return response.data
}

export async function createSite(data: Omit<SiteResponse, 'id' | 'created_at' | 'updated_at'>): Promise<SiteResponse> {
  const response = await api.post('/sites/', data)
  return response.data
}

export async function updateSite(id: number, data: Partial<SiteResponse>): Promise<SiteResponse> {
  const response = await api.put(`/sites/${id}`, data)
  return response.data
}

export async function deleteSite(id: number): Promise<void> {
  await api.delete(`/sites/${id}`)
}
