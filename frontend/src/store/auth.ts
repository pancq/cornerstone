import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAppStore } from './index'
import api from '../api/axios'

export interface User {
  id: number
  username: string
  display_name: string
  email: string
  role: string
  role_display_name: string
  permissions: string[]
  is_active: boolean
  is_superuser: boolean
  is_sso_user?: boolean
  last_login_at?: string
  last_login_ip?: string
  avatar?: string
  created_at?: string
  updated_at?: string
}

export interface SSOConfig {
  enabled: boolean
  login_methods: string[]
  has_oauth2: boolean
  has_saml: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => !!token.value)
  const ssoConfig = ref<SSOConfig | null>(null)
  
  function hasPermission(module: string, action?: string): boolean {
    if (!user.value) return false
    if (user.value.is_superuser) return true
    
    const permissionStr = action ? `${module}:${action}` : module
    return user.value.permissions.includes(permissionStr)
  }
  
  function hasRole(role: string): boolean {
    if (!user.value) return false
    return user.value.role === role
  }
  
  function isReadOnly(): boolean {
    return hasRole('viewer')
  }
  
  function isOperator(): boolean {
    return hasRole('engineer')
  }
  
  function isAdmin(): boolean {
    return hasRole('super_admin') || (user.value?.is_superuser ?? false)
  }

  async function login(username: string, password: string) {
    try {
      const response = await api.post('/auth/token', new URLSearchParams({
        username,
        password,
      }))
      
      const data = response.data
      
      token.value = data.access_token
      refreshToken.value = data.refresh_token
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token || '')
      
      // 直接从响应中设置用户信息
      if (data.user) {
        user.value = {
          id: data.user.id,
          username: data.user.username,
          display_name: data.user.display_name,
          email: data.user.email,
          role: data.user.role,
          role_display_name: data.user.role_display_name,
          permissions: data.user.permissions || [],
          is_active: data.user.is_active,
          is_superuser: data.user.is_superuser || false,
        }
      }
      
      // 添加登录日志
      const appStore = useAppStore()
      appStore.addAuditLog({
        user: username,
        action: '用户登录',
        resource: '认证',
        detail: `用户 ${username} 登录系统`,
        ipAddress: null,
        createdAt: new Date().toISOString(),
        success: 'true'
      })
      
      await fetchAuditLogs()
      return { success: true }
    } catch (error: any) {
      console.error('Login failed:', error)
      const errorMsg = error.response?.data?.detail || error.message || '登录失败'
      return { success: false, message: errorMsg }
    }
  }

  async function loginWithCaptcha(username: string, password: string, captchaId: string, captchaCode: string) {
    try {
      const response = await api.post('/auth/login-with-captcha', {
        username,
        password,
        captcha_id: captchaId,
        captcha_code: captchaCode,
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      const data = response.data
      
      token.value = data.access_token
      refreshToken.value = data.refresh_token
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token || '')
      
      // 直接从响应中设置用户信息
      if (data.user) {
        user.value = {
          id: data.user.id,
          username: data.user.username,
          display_name: data.user.display_name,
          email: data.user.email,
          role: data.user.role,
          role_display_name: data.user.role_display_name,
          permissions: data.user.permissions || [],
          is_active: data.user.is_active,
          is_superuser: data.user.is_superuser || false,
        }
      }
      
      // 添加登录日志
      const appStore = useAppStore()
      appStore.addAuditLog({
        user: username,
        action: '用户登录',
        resource: '认证',
        detail: `用户 ${username} 登录系统`,
        ipAddress: null,
        createdAt: new Date().toISOString(),
        success: 'true'
      })
      
      await fetchAuditLogs()
      return { success: true }
    } catch (error: any) {
      console.error('Login failed:', error)
      throw error
    }
  }

  async function fetchAuditLogs() {
    const appStore = useAppStore()
    try {
      const response = await fetch('/api/v1/logs/', {
        headers: {
          Authorization: `Bearer ${token.value}`,
        },
      })
      
      if (response.ok) {
        const logs = await response.json()
        appStore.$patch({ auditLogs: logs })
      }
    } catch (error) {
      console.error('Fetch audit logs failed:', error)
    }
  }

  async function fetchUser(retries = 3) {
    if (!token.value) return
    
    for (let i = 0; i < retries; i++) {
      try {
        const response = await api.get('/auth/me')
        user.value = response.data
        return
      } catch (error: any) {
        // 如果是401错误，尝试刷新token
        if (error.response?.status === 401) {
          await refreshAccessToken()
          return
        }
        // 连接被拒绝时重试
        const isConnectionError = error.code === 'ECONNREFUSED' || 
          error.message?.includes('ECONNREFUSED') ||
          error.errno === 'ECONNREFUSED'
        if (i < retries - 1 && isConnectionError) {
          await new Promise(resolve => setTimeout(resolve, 1000))
          continue
        }
        console.error('Fetch user failed:', error)
      }
    }
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      logout()
      window.location.href = '/login'
      return
    }
    
    try {
      const response = await api.post('/auth/refresh', {}, {
        headers: {
          'X-Refresh-Token': refreshToken.value,
        },
      })
      
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token || '')
      await fetchUser()
    } catch (error) {
      console.error('Refresh token failed:', error)
      logout()
      window.location.href = '/login'
    }
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      token.value = null
      refreshToken.value = null
      user.value = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  async function changePassword(oldPassword: string, newPassword: string) {
    try {
      await api.post('/auth/change-password', { 
        old_password: oldPassword, 
        new_password: newPassword 
      })
      return { success: true }
    } catch (error: any) {
      return { 
        success: false, 
        message: error.response?.data?.detail || (error instanceof Error ? error.message : '修改密码失败') 
      }
    }
  }

  async function fetchSSOConfig() {
    try {
      const response = await api.get('/auth/sso/config')
      ssoConfig.value = response.data
      return response.data
    } catch (error) {
      console.debug('Fetch SSO config failed, using defaults', error)
      ssoConfig.value = {
        enabled: false,
        login_methods: ['local'],
        has_oauth2: false,
        has_saml: false
      }
      return ssoConfig.value
    }
  }

  async function getSSOAuthorizeUrl() {
    try {
      const response = await api.get('/auth/sso/authorize')
      return response.data
    } catch (error) {
      console.error('Get SSO authorize URL failed:', error)
      throw error
    }
  }

  async function ssoCallback(code: string) {
    try {
      const response = await api.post('/auth/sso/callback', null, {
        params: {
          code,
        },
      })
      
      const data = response.data
      
      token.value = data.access_token
      refreshToken.value = data.refresh_token
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token || '')
      
      // 设置用户信息
      if (data.user) {
        user.value = {
          id: data.user.id,
          username: data.user.username,
          display_name: data.user.display_name,
          email: data.user.email,
          role: data.user.role,
          role_display_name: data.user.role_display_name,
          permissions: data.user.permissions || [],
          is_active: data.user.is_active,
          is_superuser: data.user.is_superuser || false,
          is_sso_user: data.user.is_sso_user || false,
        }
      }
      
      // 添加登录日志
      const appStore = useAppStore()
      appStore.addAuditLog({
        user: data.user?.username || 'SSO User',
        action: '用户登录',
        resource: '认证',
        detail: `用户通过SSO登录系统`,
        ipAddress: null,
        createdAt: new Date().toISOString(),
        success: 'true'
      })
      
      await fetchAuditLogs()
      return { success: true }
    } catch (error: any) {
      console.error('SSO login failed:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'SSO登录失败'
      return { success: false, message: errorMsg }
    }
  }

  return {
    token,
    refreshToken,
    user,
    isLoggedIn,
    ssoConfig,
    login,
    loginWithCaptcha,
    logout,
    fetchUser,
    refreshAccessToken,
    changePassword,
    fetchSSOConfig,
    getSSOAuthorizeUrl,
    ssoCallback,
    hasPermission,
    hasRole,
    isReadOnly,
    isOperator,
    isAdmin,
  }
})
