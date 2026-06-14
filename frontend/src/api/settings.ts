import api from './axios'

export interface NotificationSettings {
  dingtalk_webhook_url?: string
  wechat_webhook_url?: string
  feishu_webhook_url?: string
  smtp_host?: string
  smtp_port?: number
  smtp_username?: string
  smtp_password?: string
  smtp_from_email?: string
}

export const getNotificationSettings = async (): Promise<NotificationSettings> => {
  const response = await api.get('/settings/notification')
  return response.data
}

export const updateNotificationSettings = async (settings: NotificationSettings): Promise<NotificationSettings> => {
  const response = await api.put('/settings/notification', settings)
  return response.data
}

export const testNotification = async (channel: 'dingtalk' | 'wechat' | 'feishu' | 'email'): Promise<{ success: boolean; message: string }> => {
  const response = await api.post('/settings/notification/test', { channel })
  return response.data
}