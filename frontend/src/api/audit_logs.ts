import type { AuditLog } from '../types/domain'
import api from './axios'

export async function getAuditLogs(): Promise<AuditLog[]> {
  const response = await api.get('/audit-logs/')
  return response.data
}
