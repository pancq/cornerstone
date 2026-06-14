<script setup lang="ts">
import { ref, computed } from 'vue'
import { useLocaleStore } from '../store/locale'
import { SUPPORTED_LOCALES, type LocaleType } from '../i18n'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const localeStore = useLocaleStore()

const currentLocale = computed(() => localeStore.locale)
const isDropdownOpen = ref(false)

const currentLocaleLabel = computed(() => {
  if (currentLocale.value === 'zh-CN') {
    return t('languages.chinese')
  }
  return t('languages.english')
})

function getLocaleLabel(locale: LocaleType): string {
  if (locale === 'zh-CN') {
    return t('languages.chinese')
  }
  return t('languages.english')
}

function handleLocaleChange(locale: LocaleType) {
  localeStore.markAsManual()
  localeStore.setLocale(locale)
  isDropdownOpen.value = false
}

function toggleDropdown() {
  isDropdownOpen.value = !isDropdownOpen.value
}

function closeDropdown() {
  isDropdownOpen.value = false
}

// 点击外部关闭下拉菜单
import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  document.addEventListener('click', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})
</script>

<template>
  <div class="language-switcher-wrapper" @click.stop>
    <div 
      class="language-switcher" 
      @click="toggleDropdown"
    >
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M2 12h20"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      <span class="label">{{ currentLocaleLabel }}</span>
      <svg 
        class="arrow" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        stroke-width="2"
        :class="{ 'open': isDropdownOpen }"
      >
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </div>
    
    <div v-if="isDropdownOpen" class="dropdown-menu">
      <button
        v-for="locale in SUPPORTED_LOCALES"
        :key="locale.value"
        class="dropdown-item"
        :class="{ 'is-active': currentLocale === locale.value }"
        @click="handleLocaleChange(locale.value)"
      >
        {{ getLocaleLabel(locale.value) }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.language-switcher-wrapper {
  position: relative;
  display: inline-block;
}

.language-switcher {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--el-text-color-regular, #64748b);
  background-color: var(--el-fill-color-blank, transparent);
}

.language-switcher:hover {
  background-color: var(--el-fill-color-light, #f1f5f9);
  color: var(--el-text-color-primary, #1e293b);
}

.icon {
  width: 18px;
  height: 18px;
}

.label {
  font-size: 14px;
  font-weight: 500;
}

.arrow {
  width: 14px;
  height: 14px;
  opacity: 0.6;
  transition: transform 0.2s;
}

.arrow.open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  min-width: 120px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 4px 0;
  z-index: 1000;
  border: 1px solid var(--el-border-color-light, #e2e8f0);
}

.dropdown-item {
  width: 100%;
  padding: 10px 16px;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: var(--el-text-color-regular, #64748b);
  transition: all 0.2s;
}

.dropdown-item:hover {
  background-color: var(--el-fill-color-light, #f1f5f9);
  color: var(--el-text-color-primary, #1e293b);
}

.dropdown-item.is-active {
  color: var(--el-color-primary, #3b82f6);
  background-color: var(--el-color-primary-light-9, #f0f9ff);
}

/* 深色模式适配 */
:deep(.login-wrapper) .language-switcher {
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.08);
}

:deep(.login-wrapper) .language-switcher:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

:deep(.login-wrapper) .dropdown-menu {
  background: rgba(30, 41, 59, 0.95);
  border-color: rgba(255, 255, 255, 0.1);
}

:deep(.login-wrapper) .dropdown-item {
  color: rgba(255, 255, 255, 0.85);
}

:deep(.login-wrapper) .dropdown-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

:deep(.login-wrapper) .dropdown-item.is-active {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.15);
}
</style>
