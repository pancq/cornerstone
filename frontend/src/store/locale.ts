import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setLocale as setI18nLocale, getLocale, type LocaleType } from '../i18n'
import api from '../api/axios'

export const useLocaleStore = defineStore('locale', () => {
  // 状态
  const locale = ref<LocaleType>(getLocale())
  const isInitialized = ref(false)
  const isSyncing = ref(false)

  // 计算属性
  const currentLocale = computed(() => locale.value)
  const isZhCN = computed(() => locale.value === 'zh-CN')
  const isEnUS = computed(() => locale.value === 'en-US')

  // 初始化语言设置
  async function initialize() {
    if (isInitialized.value) return

    // 从 LocalStorage 获取已保存的语言设置
    const stored = localStorage.getItem('locale') as LocaleType | null
    if (stored && (stored === 'zh-CN' || stored === 'en-US')) {
      locale.value = stored
      setI18nLocale(stored)
    }

    // 如果已登录，同步服务器设置
    const token = localStorage.getItem('access_token')
    if (token) {
      await syncFromServer()
    }

    isInitialized.value = true
  }

  // 设置语言
  async function setLocale(newLocale: LocaleType) {
    if (locale.value === newLocale) return

    locale.value = newLocale
    setI18nLocale(newLocale)

    // 同步到服务器
    const token = localStorage.getItem('access_token')
    if (token) {
      await syncToServer()
    }
  }

  // 从服务器同步语言设置
  async function syncFromServer() {
    if (isSyncing.value) return

    isSyncing.value = true
    try {
      const response = await api.get('/users/me/settings')
      if (response.data.locale) {
        const serverLocale = response.data.locale as LocaleType
        // 如果服务器有设置，且本地没有手动设置过，优先使用服务器设置
        if (!localStorage.getItem('locale_manual')) {
          locale.value = serverLocale
          setI18nLocale(serverLocale)
        }
      }
    } catch (error) {
      // 忽略错误，使用本地设置
      console.warn('Failed to sync locale from server:', error)
    } finally {
      isSyncing.value = false
    }
  }

  // 同步语言设置到服务器
  async function syncToServer() {
    if (isSyncing.value) return

    isSyncing.value = true
    try {
      await api.put('/users/me/settings', {
        locale: locale.value
      })
    } catch (error) {
      // 忽略错误，不影响本地使用
      console.warn('Failed to sync locale to server:', error)
    } finally {
      isSyncing.value = false
    }
  }

  // 标记用户已手动选择语言
  function markAsManual() {
    localStorage.setItem('locale_manual', 'true')
  }

  // 重置为自动检测
  function resetToAuto() {
    localStorage.removeItem('locale')
    localStorage.removeItem('locale_manual')
    
    // 重新检测浏览器语言
    const browserLocale = navigator.language?.startsWith('en') ? 'en-US' : 'zh-CN'
    locale.value = browserLocale
    setI18nLocale(browserLocale)
  }

  return {
    // 状态
    locale,
    isInitialized,
    isSyncing,
    // 计算属性
    currentLocale,
    isZhCN,
    isEnUS,
    // 方法
    initialize,
    setLocale,
    syncFromServer,
    syncToServer,
    markAsManual,
    resetToAuto
  }
})
