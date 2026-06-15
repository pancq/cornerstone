import { createI18n } from 'vue-i18n'
import zhCN from '../locales/zh-CN.json'
import enUS from '../locales/en-US.json'

export type LocaleType = 'zh-CN' | 'en-US'

export const SUPPORTED_LOCALES: { value: LocaleType; label: string }[] = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en-US', label: 'English' }
]

// 检测浏览器语言（默认中文）
function detectBrowserLocale(): LocaleType {
  const browserLang = navigator.language || 'zh-CN'
  
  // 如果明确是中文环境，返回中文
  if (browserLang === 'zh-CN' || browserLang === 'zh' || browserLang.startsWith('zh-')) {
    return 'zh-CN'
  }
  
  // 对于其他语言环境，默认也返回中文（强制默认中文）
  // 如果用户需要英文，可以通过语言切换器手动切换
  return 'zh-CN'
}

// 获取存储的语言设置
function getStoredLocale(): LocaleType | null {
  const stored = localStorage.getItem('locale')
  if (stored === 'zh-CN' || stored === 'en-US') {
    return stored
  }
  return null
}

// 创建 i18n 实例
export const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: 'zh-CN', // 始终默认中文
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  },
  datetimeFormats: {
    'zh-CN': {
      short: {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      },
      long: {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }
    },
    'en-US': {
      short: {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      },
      long: {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }
    }
  },
  numberFormats: {
    'zh-CN': {
      decimal: {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      },
      percent: {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
      }
    },
    'en-US': {
      decimal: {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      },
      percent: {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
      }
    }
  }
})

// 切换语言
export function setLocale(locale: LocaleType) {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  
  // 更新 HTML lang 属性
  document.documentElement.lang = locale
}

// 获取当前语言
export function getLocale(): LocaleType {
  return i18n.global.locale.value as LocaleType
}

export default i18n
