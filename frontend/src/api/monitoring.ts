import request from './axios'

export interface MonitorStatus {
  device_id: number
  device_name: string
  target_ip: string
  latency: number | null
  packet_loss: number | null
  status: string
  updated_at: string
}

export interface MonitorHistory {
  latency: number | null
  packet_loss: number | null
  status: string
  created_at: string
}

export interface MonitorSummary {
  normal: number
  warning: number
  critical: number
}

export interface PingResult {
  target_ip: string
  latency: number | null
  packet_loss: number | null
  status: string
}

export async function runMonitor(): Promise<void> {
  await request.post('/monitor/run')
}

export async function getDeviceMonitorStatus(deviceId?: number): Promise<MonitorStatus[]> {
  const params = deviceId ? { device_id: deviceId } : {}
  const response = await request.get('/monitor/devices', { params })
  return response.data
}

export async function getDeviceMonitorHistory(deviceId: number, limit: number = 100): Promise<MonitorHistory[]> {
  const response = await request.get(`/monitor/history/${deviceId}`, { params: { limit } })
  return response.data
}

export async function getMonitorSummary(): Promise<MonitorSummary> {
  const response = await request.get('/monitor/summary')
  return response.data
}

export async function pingTarget(targetIp: string): Promise<PingResult> {
  const response = await request.post(`/monitor/ping/${targetIp}`)
  return response.data
}

export interface SchedulerStatus {
  running: boolean
  interval_minutes: number
}

export async function getSchedulerStatus(): Promise<SchedulerStatus> {
  const response = await request.get('/monitor/scheduler/status')
  return response.data
}

export async function setSchedulerInterval(intervalMinutes: number): Promise<void> {
  await request.post('/monitor/scheduler/interval', { params: { interval_minutes: intervalMinutes } })
}

export async function startScheduler(intervalMinutes: number = 5): Promise<void> {
  await request.post('/monitor/scheduler/start', { params: { interval_minutes: intervalMinutes } })
}

export async function stopScheduler(): Promise<void> {
  await request.post('/monitor/scheduler/stop')
}
