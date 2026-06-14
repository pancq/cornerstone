import api from './axios'

export interface InspectionTask {
  id: number
  name: string
  scan_type: string
  is_enabled: boolean
  cron_expr: string
  target_type: string
  site_id: number | null
  ip_range: string | null
  snmp_community: string
  snmp_version: string
  snmp_timeout: number
  snmp_retries: number
  tcp_ports: number[]
  tcp_timeout_ms: number
  max_concurrent: number
  alert_on_offline: boolean
  alert_on_new_device: boolean
  alert_on_fingerprint_change: boolean
  last_run_at: string | null
  last_run_status: string | null
  created_at: string
  updated_at: string | null
}

export interface InspectionTaskCreate {
  name: string
  scan_type?: string
  is_enabled?: boolean
  cron_expr?: string
  target_type?: string
  site_id?: number
  ip_range?: string
  snmp_community?: string
  snmp_version?: string
  snmp_timeout?: number
  snmp_retries?: number
  tcp_ports?: number[]
  tcp_timeout_ms?: number
  max_concurrent?: number
  alert_on_offline?: boolean
  alert_on_new_device?: boolean
  alert_on_fingerprint_change?: boolean
}

export interface InspectionTaskUpdate {
  name?: string
  scan_type?: string
  is_enabled?: boolean
  cron_expr?: string
  target_type?: string
  site_id?: number
  ip_range?: string
  snmp_community?: string
  snmp_version?: string
  snmp_timeout?: number
  snmp_retries?: number
  tcp_ports?: number[]
  tcp_timeout_ms?: number
  max_concurrent?: number
  alert_on_offline?: boolean
  alert_on_new_device?: boolean
  alert_on_fingerprint_change?: boolean
}

export interface InspectionRecord {
  id: number
  task_id: number
  scan_type: string
  trigger: string
  operator: string
  status: string
  total_targets: number
  online_count: number
  offline_count: number
  new_device_count: number
  change_count: number
  error_message: string | null
  started_at: string
  finished_at: string | null
  duration_seconds: number | null
}

export interface DeviceFingerprint {
  id: number
  ip_address: string
  device_id: number | null
  sys_descr: string | null
  sys_name: string | null
  sys_object_id: string | null
  sys_location: string | null
  vendor: string | null
  last_seen_online: string
  last_full_scan_at: string
  updated_at: string | null
}

export interface InspectionDeviceResult {
  id: number
  result_id: number
  ip_address: string
  device_id: number | null
  is_online: boolean
  detection_method: string
  open_ports: number[] | null
  sys_descr: string | null
  sys_name: string | null
  sys_object_id: string | null
  sys_up_time: number | null
  sys_location: string | null
  vendor: string | null
  cpu_usage: number | null
  memory_usage: number | null
  is_new_device: boolean
  has_fingerprint_change: boolean
  change_detail: Record<string, string[]> | null
  scan_duration_ms: number
  error_message: string | null
  scanned_at: string
}

export interface AlertCount {
  total: number
  unresolved: number
  new_device: number
  missing_device: number
  changed_device: number
}

export interface ExecuteResponse {
  result_id: number
}

// 巡检任务相关API
export async function getTasks(): Promise<InspectionTask[]> {
  const response = await api.get('/inspection/tasks')
  return response.data
}

export async function getTask(taskId: number): Promise<InspectionTask> {
  const response = await api.get(`/inspection/tasks/${taskId}`)
  return response.data
}

export async function createTask(data: InspectionTaskCreate): Promise<InspectionTask> {
  const response = await api.post('/inspection/tasks', data)
  return response.data
}

export async function updateTask(taskId: number, data: InspectionTaskUpdate): Promise<InspectionTask> {
  const response = await api.put(`/inspection/tasks/${taskId}`, data)
  return response.data
}

export async function deleteTask(taskId: number): Promise<void> {
  await api.delete(`/inspection/tasks/${taskId}`)
}

export async function toggleTask(taskId: number): Promise<{ message: string; is_enabled: boolean }> {
  const response = await api.patch(`/inspection/tasks/${taskId}/toggle`)
  return response.data
}

export async function executeTask(taskId: number, scanType?: string): Promise<ExecuteResponse> {
  const params: Record<string, unknown> = {}
  if (scanType) params.scan_type = scanType
  const response = await api.post(`/inspection/tasks/${taskId}/run`, undefined, { params })
  return response.data
}

// 巡检记录相关API
export async function getRecords(taskId?: number, scanType?: string, status?: string, limit = 20): Promise<InspectionRecord[]> {
  const params: Record<string, unknown> = { limit }
  if (taskId) params.task_id = taskId
  if (scanType) params.scan_type = scanType
  if (status) params.status = status
  const response = await api.get('/inspection/results', { params })
  return response.data
}

export async function getRecord(recordId: number): Promise<InspectionRecord> {
  const response = await api.get(`/inspection/results/${recordId}`)
  return response.data
}

export async function getDeviceResults(recordId: number, filters?: {
  is_online?: boolean
  is_new_device?: boolean
  has_fingerprint_change?: boolean
}): Promise<InspectionDeviceResult[]> {
  const params: Record<string, unknown> = {}
  if (filters?.is_online !== undefined) params.is_online = filters.is_online
  if (filters?.is_new_device !== undefined) params.is_new_device = filters.is_new_device
  if (filters?.has_fingerprint_change !== undefined) params.has_fingerprint_change = filters.has_fingerprint_change
  const response = await api.get(`/inspection/results/${recordId}/devices`, { params })
  return response.data
}

// 设备指纹相关API
export async function getFingerprints(vendor?: string, ip?: string): Promise<DeviceFingerprint[]> {
  const params: Record<string, unknown> = {}
  if (vendor) params.vendor = vendor
  if (ip) params.ip = ip
  const response = await api.get('/inspection/fingerprints', { params })
  return response.data
}

export async function getFingerprint(ip: string): Promise<DeviceFingerprint> {
  const response = await api.get(`/inspection/fingerprints/${ip}`)
  return response.data
}

// 告警统计
export async function getAlertCount(): Promise<AlertCount> {
  const response = await api.get('/inspection/alerts/count')
  return response.data
}
