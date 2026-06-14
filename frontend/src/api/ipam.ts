import api from '@/api/axios'
import type { Prefix, IPAddress } from '../types/domain'
import { snakeToCamel } from '../lib/utils'

// Prefix API
export async function getPrefixes(): Promise<Prefix[]> {
  const response = await api.get('/ipam/prefixes/')
  return snakeToCamel(response.data)
}

export async function createPrefix(prefix: Omit<Prefix, 'id'>): Promise<Prefix> {
  const payload = {
    ...prefix,
    aggregate_id: prefix.aggregateId,
    site_id: prefix.siteId,
  }
  delete (payload as any).aggregateId
  delete (payload as any).siteId
  const response = await api.post('/ipam/prefixes/', payload)
  return snakeToCamel(response.data)
}

export async function updatePrefix(id: string | number, data: Partial<Prefix>): Promise<Prefix> {
  const payload: any = { ...data }
  if (data.aggregateId !== undefined) {
    payload.aggregate_id = data.aggregateId ? Number(data.aggregateId) : null
    delete payload.aggregateId
  }
  if (data.siteId !== undefined) {
    payload.site_id = data.siteId ? Number(data.siteId) : null
    delete payload.siteId
  }
  const response = await api.put(`/ipam/prefixes/${id}`, payload)
  return snakeToCamel(response.data)
}

export async function deletePrefix(id: string | number): Promise<void> {
  await api.delete(`/ipam/prefixes/${id}`)
}

// IP Address API
export async function getIPAddresses(): Promise<IPAddress[]> {
  const response = await api.get('/ipam/addresses/')
  return snakeToCamel(response.data)
}

export async function createIPAddress(ip: Omit<IPAddress, 'id'>): Promise<IPAddress> {
  const payload = {
    ...ip,
    prefix_id: ip.prefixId,
    device_id: ip.deviceId,
  }
  delete (payload as any).prefixId
  delete (payload as any).deviceId
  const response = await api.post('/ipam/addresses/', payload)
  return snakeToCamel(response.data)
}

export async function updateIPAddress(id: string | number, data: Partial<IPAddress>): Promise<IPAddress> {
  const payload: any = { ...data }
  if (data.prefixId !== undefined) {
    payload.prefix_id = data.prefixId
    delete payload.prefixId
  }
  if (data.deviceId !== undefined) {
    payload.device_id = data.deviceId
    delete payload.deviceId
  }
  const response = await api.put(`/ipam/addresses/${id}`, payload)
  return snakeToCamel(response.data)
}

export async function deleteIPAddress(id: string | number): Promise<void> {
  await api.delete(`/ipam/addresses/${id}`)
}