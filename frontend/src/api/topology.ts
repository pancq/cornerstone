import request from './axios'

export interface TopologyNode {
  id: string
  site_id: number
  name: string
  city: string
  status: string
  device_count: number
  circuit_count: number
  contact: string
  phone: string
  location: string
  room: string
}

export interface TopologyEdge {
  id: string
  circuit_id: number
  source: string
  target: string
  name: string
  provider: string
  type: string
  bandwidth: number
  bandwidth_label: string
  status: string
  monthly_cost: number | null
  contract_end: string | null
  days_to_expire: number | null
}

export interface DeviceNode {
  id: string
  device_id: number
  name: string
  ip_address: string
  type: string
  vendor: string
  status: string
  site_id: number | null
  site_name: string | null
  latency: number | null
  packet_loss: number | null
  // 互联网出口专线字段
  circuit_id?: number
  provider?: string
  bandwidth?: number
}

export interface SiteGraphResponse {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
}

export interface DeviceLink {
  id: number
  source_device_id: number | null
  source_interface: string | null
  target_device_id: number | null
  target_interface: string | null
  link_type: string
  confidence: number | null
  discovered_at: string | null
  verified_at: string | null
  note: string | null
  source_circuit_id: number | null
  target_circuit_id: number | null
}

export interface DeviceLinkCreate {
  source_device_id?: number | null
  source_interface?: string | null
  target_device_id?: number | null
  target_interface?: string | null
  link_type?: string
  confidence?: number | null
  note?: string | null
  source_circuit_id?: number | null
  target_circuit_id?: number | null
}

export interface DeviceLinkUpdate {
  source_device_id?: number | null
  source_interface?: string | null
  target_device_id?: number | null
  target_interface?: string | null
  link_type?: string
  confidence?: number | null
  verified_at?: string | null
  note?: string | null
  source_circuit_id?: number | null
  target_circuit_id?: number | null
}

export interface DeviceGraphResponse {
  nodes: DeviceNode[]
  edges: DeviceEdge[]
}

export interface DeviceEdge {
  id: string
  link_id: number
  source: string
  target: string
  source_interface: string | null
  target_interface: string | null
  link_type: string
  confidence: number | null
}

// 站点设备选项（用于专线连接设置）
export interface SiteDeviceOption {
  id: number
  name: string
  type: string
  ip_address: string | null
}

// 更新专线连接
export interface CircuitConnectionUpdate {
  connected_device_id: number | null
}

export async function getSiteGraph(): Promise<SiteGraphResponse> {
  const response = await request.get('/topology/site-graph')
  return response.data
}

export async function getDeviceGraph(siteId?: number): Promise<DeviceGraphResponse> {
  const params = siteId ? { site_id: siteId } : {}
  const response = await request.get('/topology/device-graph', { params })
  return response.data
}

export async function getDeviceLinks(skip = 0, limit = 100): Promise<DeviceLink[]> {
  const response = await request.get('/topology/device-links', { params: { skip, limit } })
  return response.data
}

export async function getDeviceLink(linkId: number): Promise<DeviceLink> {
  const response = await request.get(`/topology/device-links/${linkId}`)
  return response.data
}

export async function createDeviceLink(link: DeviceLinkCreate): Promise<DeviceLink> {
  const response = await request.post('/topology/device-links', link)
  return response.data
}

export async function updateDeviceLink(linkId: number, link: DeviceLinkUpdate): Promise<DeviceLink> {
  const response = await request.put(`/topology/device-links/${linkId}`, link)
  return response.data
}

export async function deleteDeviceLink(linkId: number): Promise<void> {
  await request.delete(`/topology/device-links/${linkId}`)
}

export async function discoverLldpNeighbors(): Promise<void> {
  await request.post('/topology/discover-lldp')
}

// 获取站点设备列表
export async function getSiteDevices(siteId: number): Promise<SiteDeviceOption[]> {
  const response = await request.get('/topology/site-devices', { params: { site_id: siteId } })
  return response.data
}

// 更新专线连接设备
export async function updateCircuitConnection(
  circuitId: number,
  connectedDeviceId: number | null
): Promise<any> {
  const response = await request.put(
    `/topology/circuits/${circuitId}/connect`,
    null,
    { params: { connected_device_id: connectedDeviceId } }
  )
  return response.data
}
