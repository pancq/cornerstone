import api from './axios'

export interface CircuitIncident {
  id: number
  circuit_id: number
  title: string
  severity: string
  status: string
  started_at: string
  resolved_at: string | null
  duration_minutes: number | null
  symptom: string
  root_cause: string | null
  resolution: string | null
  affected_sites: string[]
  reported_by: string | null
  ticket_no: string | null
  created_at: string
  updated_at: string
}

export interface CircuitIncidentCreate {
  title: string
  severity?: string
  started_at: string
  symptom: string
  affected_sites?: string[]
  ticket_no?: string | null
}

export interface CircuitIncidentUpdate {
  title?: string
  severity?: string
  symptom?: string
  root_cause?: string | null
  resolution?: string | null
  affected_sites?: string[]
  ticket_no?: string | null
}

export interface CircuitIncidentResolve {
  root_cause?: string | null
  resolution?: string | null
}

export interface CircuitIncidentLog {
  id: number
  incident_id: number
  content: string
  operator: string | null
  created_at: string
}

export interface CircuitIncidentLogCreate {
  content: string
}

export interface CircuitIncidentStats {
  current_count: number
  monthly_count: number
  avg_duration_hours: number
  last_incident_at: string | null
}

export async function getCircuitIncidents(circuitId: number): Promise<CircuitIncident[]> {
  const response = await api.get(`/circuits/${circuitId}/incidents`)
  return response.data
}

export async function createCircuitIncident(circuitId: number, data: CircuitIncidentCreate): Promise<CircuitIncident> {
  const response = await api.post(`/circuits/${circuitId}/incidents`, data)
  return response.data
}

export async function getIncident(incidentId: number): Promise<CircuitIncident> {
  const response = await api.get(`/incidents/${incidentId}`)
  return response.data
}

export async function updateIncident(incidentId: number, data: CircuitIncidentUpdate): Promise<CircuitIncident> {
  const response = await api.put(`/incidents/${incidentId}`, data)
  return response.data
}

export async function resolveIncident(incidentId: number, data: CircuitIncidentResolve): Promise<CircuitIncident> {
  const response = await api.post(`/incidents/${incidentId}/resolve`, data)
  return response.data
}

export async function addIncidentLog(incidentId: number, data: CircuitIncidentLogCreate): Promise<CircuitIncidentLog> {
  const response = await api.post(`/incidents/${incidentId}/logs`, data)
  return response.data
}

export async function getIncidentLogs(incidentId: number): Promise<CircuitIncidentLog[]> {
  const response = await api.get(`/incidents/${incidentId}/logs`)
  return response.data
}

export async function getAllIncidents(status?: string, severity?: string): Promise<CircuitIncident[]> {
  const params: Record<string, string> = {}
  if (status) params.status = status
  if (severity) params.severity = severity
  const response = await api.get('/incidents/', { params })
  return response.data
}

export async function getCircuitIncidentStats(circuitId: number): Promise<CircuitIncidentStats> {
  const response = await api.get(`/circuits/${circuitId}/incidents/stats`)
  return response.data
}