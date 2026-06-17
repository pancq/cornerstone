import api from './axios'

export interface VlanGroupResponse {
  id: number
  name: string
  site_id: number | null
  description: string | null
  created_at: string
  updated_at: string | null
}

export interface VlanResponse {
  id: number
  vid: number
  name: string | null
  group_id: number | null
  site_id: number | null
  status: string
  description: string | null
  created_at: string
  updated_at: string | null
}

export interface VlanGroupCreate {
  name: string
  site_id: number | null
  description: string | null
}

export interface VlanCreate {
  vid: number
  name: string | null
  group_id: number | null
  site_id: number | null
  status: string
  description: string | null
}

// VLAN Group API
export async function getVlanGroups(): Promise<VlanGroupResponse[]> {
  const response = await api.get('/ipam/vlans/groups/')
  return response.data
}

export async function createVlanGroup(data: VlanGroupCreate): Promise<VlanGroupResponse> {
  const response = await api.post('/ipam/vlans/groups/', data)
  return response.data
}

export async function updateVlanGroup(id: number, data: Partial<VlanGroupCreate>): Promise<VlanGroupResponse> {
  const response = await api.put(`/ipam/vlans/groups/${id}`, data)
  return response.data
}

export async function deleteVlanGroup(id: number): Promise<void> {
  await api.delete(`/ipam/vlans/groups/${id}`)
}

// VLAN API
export async function getVlans(): Promise<VlanResponse[]> {
  const response = await api.get('/ipam/vlans/')
  return response.data
}

export async function createVlan(data: VlanCreate): Promise<VlanResponse> {
  const response = await api.post('/ipam/vlans/', data)
  return response.data
}

export async function updateVlan(id: number, data: Partial<VlanCreate>): Promise<VlanResponse> {
  const response = await api.put(`/ipam/vlans/${id}`, data)
  return response.data
}

export async function deleteVlan(id: number): Promise<void> {
  await api.delete(`/ipam/vlans/${id}`)
}
