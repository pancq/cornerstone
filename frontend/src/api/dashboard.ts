import request from './axios'

export interface DashboardStats {
  sites: {
    total: number
  }
  circuits: {
    total: number
    normal: number
    bandwidth: number
  }
  devices: {
    total: number
    online: number
    offline: number
  }
  ip: {
    total: number
    used: number
    percent: number
  }
  backups: {
    total: number
    successful: number
    failed: number
  }
  health: {
    score: number
    status: 'excellent' | 'good' | 'warning' | 'critical'
  }
}

export interface PrefixUsage {
  id: number
  network: string
  vlan: number | null
  usage: string
  usage_percent: number
}

export interface AuditLogItem {
  id: number
  user: string
  action: string
  resource: string
  detail: string
  success: string
  created_at: string
}

export interface DeviceTypeItem {
  name: string
  value: number
  type: string
}

export interface CircuitTypeItem {
  name: string
  value: number
  bandwidth: number
  type: string
  color: string
}

export async function getDashboardStats(timeRange?: string): Promise<DashboardStats> {
  const response = await request.get('/dashboard/stats', {
    params: timeRange ? { time_range: timeRange } : {}
  })
  return response.data
}

export async function getPrefixesUsage(): Promise<PrefixUsage[]> {
  const response = await request.get('/dashboard/prefixes-usage')
  return response.data
}

export async function getRecentLogs(limit = 8): Promise<AuditLogItem[]> {
  const response = await request.get('/dashboard/recent-logs', { params: { limit } })
  return response.data
}

export async function getDeviceTypes(): Promise<DeviceTypeItem[]> {
  const response = await request.get('/dashboard/device-types')
  return response.data
}

export async function getCircuitTypes(): Promise<CircuitTypeItem[]> {
  const response = await request.get('/dashboard/circuit-types')
  return response.data
}
