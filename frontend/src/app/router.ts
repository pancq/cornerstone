import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from '../features/dashboard/DashboardPage.vue'
import CircuitsPage from '../features/circuits/CircuitsPage.vue'
import CircuitDetail from '../features/circuits/CircuitDetail.vue'

import CircuitChanges from '../features/circuits/CircuitChanges.vue'
import IpamPage from '../features/ipam/IpamPage.vue'
import VlanList from '../features/ipam/VlanList.vue'
import DevicesPage from '../features/devices/DevicesPage.vue'
import DeviceLinksList from '../features/devices/DeviceLinksList.vue'
import BackupsPage from '../features/backups/BackupsPage.vue'
import CredentialList from '../features/backups/CredentialList.vue'
import BackupTaskList from '../features/backups/BackupTaskList.vue'
import AlertsPage from '../features/alerts/AlertsPage.vue'
import SystemPage from '../features/system/SystemPage.vue'
import LogsPage from '../features/system/LogsPage.vue'
import SettingsPage from '../features/system/SettingsPage.vue'
import AISettingsPage from '../features/system/AISettingsPage.vue'
import SitesPage from '../features/sites/SitesPage.vue'
import SiteTopology from '../features/topology/SiteTopology.vue'
import DeviceTopology from '../features/topology/DeviceTopology.vue'
import LinkMonitor from '../features/monitoring/LinkMonitor.vue'
import AlertManagement from '../features/monitoring/AlertManagement.vue'
import LoginPage from '../features/auth/LoginPage.vue'
import ForbiddenPage from '../features/errors/ForbiddenPage.vue'
import ProfilePage from '../features/system/ProfilePage.vue'
import InspectionPage from '../features/inspection/InspectionPage.vue'
import UserManagement from '../features/system/UserManagement.vue'
import RoleManagement from '../features/system/RoleManagement.vue'
import SSOSettingsPage from '../features/system/SSOSettingsPage.vue'
import NotificationSettingsPage from '../features/system/NotificationSettingsPage.vue'
import LogsSettingsPage from '../features/system/LogsSettingsPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginPage, meta: { title: '' } },
    { path: '/403', name: 'forbidden', component: ForbiddenPage, meta: { title: '' } },
    { path: '/', name: 'dashboard', component: DashboardPage, meta: { requiresAuth: true, permission: null, titleKey: 'dashboard.title' } },
    { path: '/circuits', name: 'circuits', component: CircuitsPage, meta: { requiresAuth: true, permission: 'circuits:read', titleKey: 'circuits.title' } },
    { path: '/circuits/:id', name: 'circuit-detail', component: CircuitDetail, meta: { requiresAuth: true, permission: 'circuits:read', titleKey: 'circuits.title' } },
    
    { path: '/circuits/:id/changes', name: 'circuit-changes', component: CircuitChanges, meta: { requiresAuth: true, permission: 'circuits:read', titleKey: 'circuits.title' } },
    { path: '/ipam', name: 'ipam', component: IpamPage, meta: { requiresAuth: true, permission: 'ipam:read', titleKey: 'ipam.title' } },
    { path: '/ipam/vlans', name: 'ipam-vlans', component: VlanList, meta: { requiresAuth: true, permission: 'ipam:read', titleKey: 'ipam.vlans' } },
    { path: '/devices', name: 'devices', component: DevicesPage, meta: { requiresAuth: true, permission: 'devices:read', titleKey: 'devices.title' } },
    { path: '/devices/:id(\\d+)', redirect: to => ({ path: '/devices', query: { id: to.params.id } }) },
    { path: '/devices/links', name: 'device-links', component: DeviceLinksList, meta: { requiresAuth: true, permission: 'devices:read', titleKey: 'devices.title' } },
    { path: '/backups', name: 'backups', component: BackupsPage, meta: { requiresAuth: true, permission: 'backups:read', titleKey: 'backups.title' } },
    { path: '/backups/credentials', name: 'backup-credentials', component: CredentialList, meta: { requiresAuth: true, permission: 'backups:read', titleKey: 'backups.credentials' } },
    { path: '/backups/tasks', name: 'backup-tasks', component: BackupTaskList, meta: { requiresAuth: true, permission: 'backups:read', titleKey: 'backups.tasks' } },
    { path: '/monitor', name: 'monitor', component: LinkMonitor, meta: { requiresAuth: true, permission: 'topology:read', titleKey: 'monitor.title' } },
    { path: '/monitor/alerts', name: 'monitor-alerts', component: AlertManagement, meta: { requiresAuth: true, permission: 'topology:read', titleKey: 'monitor.title' } },
    { path: '/alerts', name: 'alerts', component: AlertsPage, meta: { requiresAuth: true, permission: 'alerts:read', titleKey: 'alerts.title' } },
    { path: '/system', name: 'system', component: SystemPage, meta: { requiresAuth: true, permission: 'system:read', titleKey: 'system.title' } },
    { path: '/system/logs', name: 'system-logs', component: LogsPage, meta: { requiresAuth: true, permission: 'logs:read', titleKey: 'system.logs' } },
    { path: '/system/settings', name: 'system-settings', component: SettingsPage, meta: { requiresAuth: true, permission: 'system:read', titleKey: 'system.settings' } },
    { path: '/system/ai-settings', name: 'ai-settings', component: AISettingsPage, meta: { requiresAuth: true, permission: 'system:read', titleKey: 'system.aiSettings' } },
    { path: '/system/logs-settings', name: 'logs-settings', component: LogsSettingsPage, meta: { requiresAuth: true, permission: 'system:admin', titleKey: 'system.logsSettings' } },
    { path: '/system/users', name: 'system-users', component: UserManagement, meta: { requiresAuth: true, permission: 'system:read', titleKey: 'system.userManagement' } },
    { path: '/system/roles', name: 'system-roles', component: RoleManagement, meta: { requiresAuth: true, permission: 'system:admin', titleKey: 'system.roleManagement' } },
    { path: '/system/sso', name: 'system-sso', component: SSOSettingsPage, meta: { requiresAuth: true, permission: 'system:admin', titleKey: 'system.ssoSettings' } },
    { path: '/system/notifications', name: 'system-notifications', component: NotificationSettingsPage, meta: { requiresAuth: true, permission: 'system:read', titleKey: 'system.notifications' } },
    { path: '/profile', name: 'profile', component: ProfilePage, meta: { requiresAuth: true, permission: null, titleKey: 'system.profile' } },
    { path: '/sites', name: 'sites', component: SitesPage, meta: { requiresAuth: true, permission: 'sites:read', titleKey: 'sites.title' } },
    { path: '/topology/sites', name: 'topology-sites', component: SiteTopology, meta: { requiresAuth: true, permission: 'topology:read', titleKey: 'topology.siteTopology' } },
    { path: '/topology/devices', name: 'topology-devices', component: DeviceTopology, meta: { requiresAuth: true, permission: 'topology:read', titleKey: 'topology.deviceTopology' } },
    { path: '/topology', redirect: '/topology/sites' },
    { path: '/inspection', name: 'inspection', component: InspectionPage, meta: { requiresAuth: true, permission: 'system:read', titleKey: 'inspection.title' } }
  ]
})

router.beforeEach(async (to, _from) => {
  const token = localStorage.getItem('access_token')
  const isLoggedIn = !!token
  
  // 如果路由需要认证，用户未登录，且不是登录页面
  if (to.meta.requiresAuth && !isLoggedIn && to.path !== '/login') {
    localStorage.setItem('redirect_after_login', to.fullPath)
    return '/login'
  }
  
  if (to.path === '/login' && isLoggedIn) {
    const redirectPath = localStorage.getItem('redirect_after_login') || '/'
    localStorage.removeItem('redirect_after_login')
    return redirectPath
  }
  
  // 检查权限和token有效性
  if (to.meta.requiresAuth && isLoggedIn) {
    // 动态导入auth store以避免循环依赖
    const { useAuthStore } = await import('../store/auth')
    const authStore = useAuthStore()
    
    // 如果用户信息还未加载，尝试加载
    if (!authStore.user) {
      try {
        await authStore.fetchUser()
      } catch (error) {
        // token无效，清除并重定向到登录页
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.setItem('redirect_after_login', to.fullPath)
        return '/login'
      }
    }
    
    // 检查权限
    if (to.meta.permission && !authStore.hasPermission(to.meta.permission as string)) {
      return { name: 'forbidden' }
    }
  }
  
  return true
}

// 路由切换后更新浏览器标签页标题
router.afterEach(async (to) => {
  const { useBrandStore } = await import('../store/brand')
  const brandStore = useBrandStore()
  const titleKey = to.meta.titleKey as string
  brandStore.updateDocumentTitle(titleKey || undefined)
})

export default router
