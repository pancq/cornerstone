import api from './axios'

export interface CircuitResponse {
  id: number
  name: string
  type: string
  provider: string
  site_id: number | null
  bandwidth: number | null
  monthly_cost: number | null
  contract_start: string | null
  contract_end: string | null
  circuit_no: string | null
  support_phone: string | null
  public_ip: string | null
  status: string
  note: string | null
  updated_by: string | null
  updated_at: string | null
}

export interface CircuitCreate {
  name: string
  type: string
  provider: string
  bandwidth: string
  a_site_id: number | null
  z_site_id: number | null
  a_end_ip: string | null
  z_end_ip: string | null
  status: string
  contract_no: string | null
  contract_begin: string | null
  contract_end: string | null
  cost: number | null
  note: string | null
}

export async function getCircuits(): Promise<CircuitResponse[]> {
  const response = await api.get('/circuits/')
  return response.data
}

export async function getCircuit(id: number): Promise<CircuitResponse> {
  const response = await api.get(`/circuits/${id}`)
  return response.data
}

export async function createCircuit(data: CircuitCreate): Promise<CircuitResponse> {
  const response = await api.post('/circuits/', data)
  return response.data
}

export async function updateCircuit(id: number, data: Partial<CircuitCreate>): Promise<CircuitResponse> {
  const response = await api.put(`/circuits/${id}`, data)
  return response.data
}

export async function deleteCircuit(id: number): Promise<void> {
  await api.delete(`/circuits/${id}`)
}

export interface CircuitChange {
  id: number
  circuit_id: number
  change_type: string
  field_name: string
  old_value: string
  new_value: string
  operator: string
  remark: string
  created_at: string
}

export async function getCircuitChanges(circuitId: number): Promise<CircuitChange[]> {
  const response = await api.get(`/circuits/${circuitId}/changes`)
  return response.data
}
