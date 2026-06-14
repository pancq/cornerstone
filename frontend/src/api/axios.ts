import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 统一把 config.url 规范为相对 baseURL 的路径（去掉重复的 /api/v1 前缀）
function normalizeUrl(url?: string) {
  if (!url) return url
  if (url.startsWith('/api/v1/')) return url.slice('/api/v1'.length)
  if (url === '/api/v1' || url === '/api/v1/') return '/'
  return url
}

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    
    // 关键：始终让 url 相对 baseURL，避免出现 /api/v1/api/v1/... 或不走代理的怪问题
    config.url = normalizeUrl(config.url)

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // token 过期或未认证，强制登出并重定向到登录页
      localStorage.removeItem('access_token')
      // 避免重复重定向
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
