<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './store/auth'
import { useBrandStore } from './store/brand'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import GlobalSearch from './components/GlobalSearch.vue'
import { useGlobalShortcut } from './lib/shortcuts'
import api from './api/axios'
import { useI18n } from 'vue-i18n'
import { 
  DataBoard, 
  Location, 
  Connection, 
  Monitor, 
  Bell, 
  Setting, 
  Files, 
  SwitchButton, 
  Tools, 
  Minus, 
  Plus,
  User,
  TrendCharts,
  Search
} from '@element-plus/icons-vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const brandStore = useBrandStore()
const searchQuery = ref('')
const companyLogo = ref<string>(localStorage.getItem('companyLogo') || '')
const isLogoLoading = ref(!companyLogo.value)
const ipamMenuOpen = ref(false)
const backupMenuOpen = ref(false)
const topologyMenuOpen = ref(false)
const sidebarCollapsed = ref(false)
const activeTooltip = ref('')
const globalSearchRef = ref<InstanceType<typeof GlobalSearch> | null>(null)
let hideTimer: ReturnType<typeof setTimeout> | null = null
const isRouteReady = ref(false)

useGlobalShortcut(() => globalSearchRef.value?.open())

router.isReady().then(() => {
  setTimeout(() => {
    isRouteReady.value = true
  }, 300)
})

const toggleIpamMenu = () => {
  ipamMenuOpen.value = !ipamMenuOpen.value
}

const toggleBackupMenu = () => {
  backupMenuOpen.value = !backupMenuOpen.value
}

const toggleTopologyMenu = () => {
  topologyMenuOpen.value = !topologyMenuOpen.value
}

const showTooltip = (name: string) => {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
  activeTooltip.value = name
}

const hideTooltip = () => {
  hideTimer = setTimeout(() => {
    activeTooltip.value = ''
    hideTimer = null
  }, 200)
}

onMounted(() => {
  brandStore.loadBrand()
  if (authStore.isLoggedIn) {
    authStore.fetchUser()
  }
  loadLogo()
})

const loadLogo = async () => {
  if (!authStore.isLoggedIn) return
  
  isLogoLoading.value = true
  try {
    const response = await api.get('/settings/logo')
    if (!response.data || !response.data.value) {
      companyLogo.value = ''
      localStorage.removeItem('companyLogo')
      return
    }
    const base64 = response.data.value
    companyLogo.value = `data:image/png;base64,${base64}`
    localStorage.setItem('companyLogo', companyLogo.value)
  } catch (error) {
    console.warn('加载Logo失败:', error)
  } finally {
    isLogoLoading.value = false
  }
}

const pageTitle = computed(() => {
  if (!isRouteReady.value) return ''
  
  const matched = route.matched[route.matched.length - 1]
  if (!matched) return ''
  
  const titleKey = matched.meta.titleKey as string
  if (titleKey) {
    return t(titleKey)
  }
  
  return ''
})

const pageEyebrow = computed(() => {
  const eyebrows: Record<string, string> = {
    '/': t('menuGroups.overview'),
    '/circuits': t('menuGroups.resourceManagement'),
    '/ipam': t('menuGroups.resourceManagement'),
    '/devices': t('menuGroups.resourceManagement'),
    '/backups': t('menuGroups.operationsCenter'),
    '/backups/credentials': t('menuGroups.operationsCenter'),
    '/backups/tasks': t('menuGroups.operationsCenter'),
    '/alerts': t('menuGroups.operationsCenter'),
    '/monitor': t('menuGroups.operationsCenter'),
    '/topology': t('menuGroups.operationsCenter'),
    '/inspection': t('menuGroups.operationsCenter'),
    '/sites': t('menuGroups.resourceManagement'),
    '/system': t('menuGroups.systemManagement'),
    '/system/logs': t('menuGroups.systemManagement'),
    '/system/settings': t('menuGroups.systemManagement'),
    '/system/ai-settings': t('menuGroups.systemManagement'),
    '/profile': t('menuGroups.systemManagement'),
  }
  
  const matched = route.matched[route.matched.length - 1]
  if (matched && matched.meta.eyebrow) {
    return matched.meta.eyebrow as string
  }
  
  return eyebrows[route.path] || ''
})

const showTopSearch = computed(() => {
  return route.path === '/'
})

const isLoginPage = computed(() => {
  return route.path === '/login'
})

// 菜单权限配置
interface MenuItem {
  path?: string
  name: string
  key?: string
  icon: typeof DataBoard
  permission: string | null
  children?: Array<{ path: string; name: string; permission: string | null }>
}

const menuItems = computed((): Array<{ group: string; items: MenuItem[] }> => {
  return [
    {
      group: '',  // 首页无分组标题
      items: [
        { path: '/', name: t('dashboard.title'), icon: DataBoard, permission: null }
      ]
    },
    {
      group: t('menuGroups.resourceManagement'),
      items: [
        { path: '/sites', name: t('sites.title'), icon: Location, permission: 'sites:read' },
        { path: '/circuits', name: t('circuits.title'), icon: Connection, permission: 'circuits:read' },
        { 
          key: 'ipam',
          name: t('ipam.title'), 
          icon: Files,
          children: [
            { path: '/ipam', name: t('ipam.ipAddress'), permission: 'ipam:read' },
            { path: '/ipam/vlans', name: t('ipam.vlans'), permission: 'ipam:read' }
          ],
          permission: 'ipam:read'
        }
      ]
    },
    {
      group: t('menuGroups.operationsCenter'),
      items: [
        { path: '/devices', name: t('devices.title'), icon: DataBoard, permission: 'devices:read' },
        { 
          key: 'topology',
          name: t('topology.title'), 
          icon: Connection,
          children: [
            { path: '/topology/sites', name: t('topology.siteTopology'), permission: 'topology:read' },
            { path: '/topology/devices', name: t('topology.deviceTopology'), permission: 'topology:read' },
            { path: '/monitor', name: t('monitor.title'), permission: 'topology:read' }
          ],
          permission: 'topology:read'
        },
        { 
          key: 'backups',
          name: t('backups.title'), 
          icon: Files,
          children: [
            { path: '/backups', name: t('backups.backupHistory'), permission: 'backups:read' },
            { path: '/backups/credentials', name: t('backups.credentials'), permission: 'backups:read' },
            { path: '/backups/tasks', name: t('backups.tasks'), permission: 'backups:read' }
          ],
          permission: 'backups:read'
        },
        { path: '/alerts', name: t('alerts.title'), icon: Bell, permission: 'alerts:read' },
        { path: '/inspection', name: t('inspection.title'), icon: TrendCharts, permission: 'system:read' }
      ]
    },
    {
      group: t('menuGroups.systemManagement'),
      items: [
        { path: '/system/users', name: t('system.userManagement'), icon: User, permission: 'system:admin' },
        { path: '/system/roles', name: t('system.roleManagement'), icon: Setting, permission: 'system:admin' },
        { path: '/system/sso', name: t('system.ssoSettings'), icon: Connection, permission: 'system:admin' }
      ]
    },
    {
      group: t('menuGroups.systemSettings'),
      items: [
        { path: '/system/settings', name: t('system.settings'), icon: Setting, permission: 'system:read' },
        { path: '/system/notifications', name: t('system.notifications'), icon: Bell, permission: 'system:read' },
        { path: '/system/ai-settings', name: t('system.aiSettings'), icon: SwitchButton, permission: 'system:read' },
        { path: '/system/logs-settings', name: t('system.logsSettings'), icon: Files, permission: 'system:admin' }
      ]
    },
    {
      group: '',  // 审计日志无分组标题
      items: [
        { path: '/system/logs', name: t('system.logs'), icon: Files, permission: 'logs:read' }
      ]
    }
  ]
})

// 检查菜单项是否有权限
function hasMenuPermission(permission: string | null): boolean {
  if (!permission) return true
  return authStore.hasPermission(permission)
}

// 过滤菜单
const filteredMenuItems = computed(() => {
  return menuItems.value.map(group => {
    const filteredItems = group.items.filter(item => {
      // 如果是有子菜单的项目
      if (item.children) {
        // 检查是否有子项有权限
        return item.children.some(child => hasMenuPermission(child.permission))
      }
      return hasMenuPermission(item.permission)
    })
    return {
      ...group,
      items: filteredItems
    }
  }).filter(group => group.items.length > 0)
})

async function handleLogout() {
  await authStore.logout()
  await router.push('/login')
}
</script>

<template>
  <div v-if="isLoginPage" class="login-wrapper">
    <div class="global-language-switcher"><LanguageSwitcher /></div>
    <RouterView />
  </div>
  
  <div v-else class="enterprise-shell">
    <aside class="enterprise-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="enterprise-brand">
        <div v-if="companyLogo" class="enterprise-brand-logo">
          <img :src="companyLogo" alt="Logo" class="brand-logo-image" />
        </div>
        <div v-else-if="!isLogoLoading" class="enterprise-brand-mark">C</div>
        <div v-else class="enterprise-brand-mark loading"></div>
        <div class="enterprise-brand-text" v-show="!sidebarCollapsed">
          <strong>{{ brandStore.brandNameZh }}</strong>
          <span>{{ brandStore.brandNameEn }}</span>
        </div>
      </div>

      <nav class="enterprise-nav">
        <div v-for="group in filteredMenuItems" :key="group.group" class="enterprise-nav-group">
          <div class="enterprise-nav-group-title" v-show="!sidebarCollapsed">{{ group.group }}</div>
          <div class="enterprise-nav-group-items">
            <template v-for="item in group.items" :key="item.name">
              <!-- 普通菜单项 -->
              <RouterLink 
                v-if="item.path && !item.children"
                :to="item.path" 
                class="enterprise-nav-item" 
                active-class="active"
                @mouseenter="showTooltip(item.name)"
                @mouseleave="hideTooltip"
              >
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.name }}</span>
                <div 
                  v-if="sidebarCollapsed && activeTooltip === item.name" 
                  class="nav-tooltip"
                  @mouseenter="showTooltip(item.name)"
                  @mouseleave="hideTooltip"
                >{{ item.name }}</div>
              </RouterLink>
              
              <!-- 带子菜单的项目 -->
              <div
                v-else-if="item.children"
                class="enterprise-nav-item has-children"
                :class="{ 'active': item.children.some(child => route.path.startsWith(child.path)) }"
                @click="item.key === 'ipam' ? toggleIpamMenu() : item.key === 'topology' ? toggleTopologyMenu() : item.key === 'backups' ? toggleBackupMenu() : null"
                @mouseenter="showTooltip(item.name)"
                @mouseleave="hideTooltip"
              >
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.name }}</span>
                <el-icon class="arrow-icon">
                  <Minus v-if="(item.key === 'ipam' && ipamMenuOpen) || (item.key === 'backups' && backupMenuOpen) || (item.key === 'topology' && topologyMenuOpen)" />
                  <Plus v-else />
                </el-icon>
                <div 
                  v-if="sidebarCollapsed && activeTooltip === item.name" 
                  class="nav-tooltip nav-tooltip-submenu"
                  @mouseenter="showTooltip(item.name)"
                  @mouseleave="hideTooltip"
                >
                  <div class="tooltip-title">{{ item.name }}</div>
                  <div class="tooltip-submenu">
                    <RouterLink 
                      v-for="child in item.children" 
                      :key="child.path"
                      :to="child.path" 
                      class="tooltip-subitem"
                    >
                      {{ child.name }}
                    </RouterLink>
                  </div>
                </div>
              </div>
              
              <!-- 子菜单 -->
              <div
                v-if="item.children"
                v-show="!sidebarCollapsed && ((item.key === 'ipam' && ipamMenuOpen) || (item.key === 'backups' && backupMenuOpen) || (item.key === 'topology' && topologyMenuOpen))"
                class="enterprise-nav-submenu"
              >
                <RouterLink 
                  v-for="child in item.children" 
                  :key="child.path"
                  :to="child.path" 
                  class="enterprise-nav-item sub-item" 
                  active-class="active"
                  v-show="hasMenuPermission(child.permission)"
                  :title="child.name"
                >
                  <span>{{ child.name }}</span>
                </RouterLink>
              </div>
            </template>
          </div>
        </div>
      </nav>
      
      <div class="sidebar-footer">
        <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <svg v-if="sidebarCollapsed" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 18l6-6-6-6"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 18l-6-6 6-6"/>
          </svg>
        </button>
      </div>
    </aside>

    <main class="enterprise-workspace" :class="{ 'route-loading': !isRouteReady }">
      <header class="enterprise-topbar">
        <div class="enterprise-topbar-left">
          <h1 class="enterprise-page-title">
            <span v-if="pageTitle">{{ pageTitle }}</span>
            <span v-else class="page-title-loading"></span>
          </h1>
        </div>
        <div class="enterprise-topbar-right">
          <button class="global-search-btn" @click="globalSearchRef?.open()">
            <el-icon><Search /></el-icon>
            <span class="search-btn-text">{{ t('aiSearch.searchOrAsk') }}</span>
            <kbd class="search-btn-kbd">⌘K</kbd>
          </button>
          <LanguageSwitcher />
          <div class="enterprise-user-info">
              <RouterLink to="/profile" class="user-profile-link">
                <el-icon><User /></el-icon>
                <span class="username">{{ authStore.user?.display_name || authStore.user?.username || 'admin' }}</span>
              </RouterLink>
              <el-button link @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                <span class="logout-text">{{ $t('login.logout') }}</span>
              </el-button>
            </div>
        </div>
      </header>
      <section class="enterprise-content">
        <RouterView />
      </section>
    </main>
  </div>
  <GlobalSearch ref="globalSearchRef" />
</template>

<style scoped>
.login-wrapper {
  min-height: 100vh;
}

.enterprise-shell {
  display: flex;
  min-height: 100vh;
  background: var(--bg-secondary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.enterprise-sidebar {
  width: 220px;
  background: linear-gradient(180deg, #001529 0%, #001a33 100%);
  color: rgba(255, 255, 255, 0.85);
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: 
    4px 0 20px rgba(0, 0, 0, 0.3),
    8px 0 40px rgba(0, 0, 0, 0.1);
}

.enterprise-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 0%, transparent 50%);
  pointer-events: none;
}

.enterprise-sidebar.collapsed {
  width: 64px;
}

.enterprise-workspace {
  margin-left: 220px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.collapsed + .enterprise-workspace {
  margin-left: 64px;
}

.enterprise-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  background: #fff;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

.enterprise-topbar-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.enterprise-eyebrow {
  font-size: 12px;
  color: #8c8c8c;
  margin: 0;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.enterprise-page-title {
  font-size: 20px;
  font-weight: 600;
  color: #262626;
  margin: 0;
  min-height: 28px;
}

.enterprise-page-title.loading .page-title-loading {
  display: inline-block;
  width: 120px;
  height: 24px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.enterprise-workspace.route-loading {
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
}

.enterprise-workspace:not(.route-loading) {
  opacity: 1;
  visibility: visible;
  transition: opacity 0.2s ease, visibility 0.2s ease;
}

.enterprise-topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.global-search-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #f8f8f8;
  color: #8c8c8c;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 220px;
}

.global-search-btn:hover {
  border-color: #d9d9d9;
  background: #f0f0f0;
  color: #595959;
}

.global-search-btn .el-icon {
  font-size: 16px;
}

.search-btn-text {
  flex: 1;
  text-align: left;
}

.search-btn-kbd {
  padding: 1px 6px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  font-size: 11px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #bbb;
  background: #fff;
}

.enterprise-search-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.enterprise-user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-profile-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #262626;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.user-profile-link:hover {
  color: #1890ff;
  text-decoration: none;
}

.enterprise-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.logout-text {
  margin-left: 4px;
}

.enterprise-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 64px;
  padding: 0 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  position: relative;
  gap: 12px;
}

.enterprise-brand-logo,
.enterprise-brand-mark {
  flex-shrink: 0;
}

.sidebar-toggle {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  transition: all 0.15s ease;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}


.sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.enterprise-brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  display: grid;
  place-items: center;
  color: white;
  font-weight: 700;
  font-size: 18px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.3);
}

.enterprise-brand-mark.loading {
  background: rgba(24, 144, 255, 0.2);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.enterprise-brand-mark:hover {
  transform: scale(1.05) rotate(2deg);
  box-shadow: 
    0 8px 32px rgba(24, 144, 255, 0.4),
    0 0 20px rgba(24, 144, 255, 0.2);
}

.enterprise-brand-logo {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
}

.brand-logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.enterprise-brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.enterprise-brand-text strong {
  font-size: 15px;
  font-weight: 600;
  color: white;
}

.enterprise-brand-text span {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.enterprise-nav {
  padding: 16px 8px;
  overflow-y: auto;
  flex: 1;
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.enterprise-nav-group {
  margin-bottom: 8px;
}

.enterprise-nav-group-title {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  padding: 8px 16px 4px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.enterprise-nav-group-items {
  display: grid;
  gap: 2px;
}

.enterprise-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.65);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  transform-origin: left center;
}

.enterprise-nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.enterprise-nav-item.active {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.3);
}

.enterprise-nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: white;
  border-radius: 0 2px 2px 0;
}

.enterprise-nav-item .el-icon {
  font-size: 20px;
  width: 20px;
  height: 20px;
  line-height: 20px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.enterprise-nav-item:hover .el-icon {
  transform: scale(1.1);
  filter: drop-shadow(0 0 8px rgba(24, 144, 255, 0.5));
}

.enterprise-nav-item.active .el-icon {
  filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.6));
}

.enterprise-nav-item.has-children {
  cursor: pointer;
}

.enterprise-nav-item.has-children .arrow-icon {
  margin-left: auto;
  font-size: 16px;
  width: 16px;
  height: 16px;
  line-height: 16px;
  transition: transform 0.2s ease;
}

.enterprise-nav-submenu {
  padding-left: 0;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 0 0 6px 6px;
  overflow: hidden;
}

.enterprise-nav-item.sub-item {
  padding-left: 48px;
  font-size: 13px;
}

/* 折叠状态下的样式 */
.enterprise-sidebar.collapsed .enterprise-nav-item span:not(.nav-tooltip) {
  display: none;
}

.enterprise-sidebar.collapsed .enterprise-nav-item {
  justify-content: center;
  padding: 12px;
}

.enterprise-sidebar.collapsed .enterprise-nav-item .el-icon {
  font-size: 20px;
  width: 20px;
  height: 20px;
  line-height: 20px;
}

.enterprise-sidebar.collapsed .enterprise-nav-item.has-children .arrow-icon {
  display: none;
}

.enterprise-sidebar.collapsed .enterprise-nav-item.sub-item {
  padding-left: 12px;
  justify-content: center;
}

.enterprise-sidebar.collapsed .enterprise-nav-group-title {
  display: none;
}

.enterprise-sidebar.collapsed .enterprise-nav {
  padding: 8px 0;
}

.enterprise-sidebar.collapsed .enterprise-nav-group {
  margin-bottom: 0;
}

.enterprise-sidebar.collapsed .enterprise-nav-group-items {
  gap: 6px;
}
</style>
