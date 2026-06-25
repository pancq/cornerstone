import api from './axios'

export interface TimelineEvent {
  id: string
  event_type: string
  severity: string
  title: string
  description: string
  resource_type: string
  resource_id: number | null
  resource_name: string
  occurred_at: string | null
  detail_url: string | null
  source: string
}

export interface TimelineResponse {
  events: TimelineEvent[]
  total: number
  has_more: boolean
}

export async function getTimelineEvents(
  start_time?: string,
  end_time?: string,
  event_types?: string,
  limit: number = 100
): Promise<TimelineResponse> {
  const params: Record<string, string | number> = { limit }
  if (start_time) params.start_time = start_time
  if (end_time) params.end_time = end_time
  if (event_types) params.event_types = event_types
  
  const response = await api.get('/timeline/events', { params })
  return response.data
}