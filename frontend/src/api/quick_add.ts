import api from './axios'

export interface TestConnectionRequest {
  ip_address: string
  vendor: string
  username: string
  password: string
  port?: number
  enable_password?: string
}

export interface TestConnectionResponse {
  success: boolean
  message: string
  device_info?: {
    ip_address: string
    vendor: string
    output: string
    version?: string
    model?: string
  }
}

export interface QuickAddDeviceRequest {
  name: string
  ip_address: string
  prefix_id?: number
  site_id?: number
  vendor: string
  username: string
  password: string
  port?: number
  enable_password?: string
  type?: string
  location?: string
  owner?: string
}

export interface QuickAddDeviceResponse {
  success: boolean
  message: string
  device_id?: number
}

export async function testDeviceConnection(data: TestConnectionRequest): Promise<TestConnectionResponse> {
  const response = await api.post('/devices/test-connection', data)
  return response.data
}

export async function quickAddDevice(data: QuickAddDeviceRequest): Promise<QuickAddDeviceResponse> {
  const response = await api.post('/devices/quick-add', data)
  return response.data
}