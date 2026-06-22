<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/store/auth'

import { getDashboardStats, getPrefixesUsage, getRecentLogs, getDeviceTypes, getCircuitTypes, type DashboardStats, type PrefixUsage, type AuditLogItem, type DeviceTypeItem, type CircuitTypeItem } from '@/api/dashboard'

const { t, locale } = useI18n()
const authStore = useAuthStore()

// 用户权限判断
const isAdmin = computed(() => authStore.user?.role === 'super_admin')
const isEngineer = computed(() => authStore.user?.role === 'engineer')
const isViewer = computed(() => authStore.user?.role === 'viewer')

// 根据角色确定可见的概览卡片
const visibleCards = computed(() => {
  const cards = []
  // 所有角色都能看到站点统计
  cards.push('sites', 'devices', 'bandwidth')
  // 工程师和管理员能看到 IP 统计
  if (isAdmin.value || isEngineer.value) cards.push('ipam')
  // 工程师和管理员能看到备份统计
  if (isAdmin.value || isEngineer.value) cards.push('backups')
  // 管理员能看到系统健康状态
  if (isAdmin.value) cards.push('health')
  return cards
})

// 真实数据状态
const dashboardStats = ref<DashboardStats | null>(null)
const prefixesUsage = ref<PrefixUsage[]>([])
const recentLogs = ref<AuditLogItem[]>([])
const deviceTypes = ref<DeviceTypeItem[]>([])
const circuitTypes = ref<CircuitTypeItem[]>([])
const loading = ref(true)
const searchQuery = ref('')

// 设备类型颜色映射
const deviceTypeColors: Record<string, string> = {
  'router': '#409EFF',
  'switch': '#67C23A',
  'firewall': '#E6A23C',
  'server': '#909399',
  'other': '#F56C6C',
  'unknown': '#909399'
}

// 专线类型颜色映射
const circuitTypeColors: Record<string, string> = {
  '互联网专线': '#409EFF',
  'MPLS': '#67C23A',
  'SD-WAN': '#E6A23C',
  '光纤专线': '#9C27B0',
  '云专线': '#00BCD4',
  '未分类': '#909399'
}

const filteredLogs = computed(() => {
  if (!searchQuery.value) return recentLogs.value
  return recentLogs.value.filter(log => 
    log.action.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    log.resource.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    log.detail.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 格式化时间
function formatTime(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleString(locale.value || t('common.locale'), {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

// 操作日志翻译映射
function getActionTranslation(action: string): string {
  const actionMap: Record<string, string> = {
    '用户登录': t('common.userLogin'),
    '登录成功': t('common.loginSuccess'),
    '登录失败': t('common.loginFailed')
  }
  return actionMap[action] || action
}

// 资源类型翻译映射
function getResourceTranslation(resource: string): string {
  const resourceMap: Record<string, string> = {
    '认证': t('common.auth'),
    '系统': t('common.system')
  }
  return resourceMap[resource] || resource
}

// 详情翻译映射
function getDetailTranslation(detail: string): string {
  if (detail.includes('用户 ') && detail.includes(' 登录系统')) {
    const username = detail.replace('用户 ', '').replace(' 登录系统', '')
    return t('common.userLogin') + ' - ' + username
  }
  return detail
}

// 获取健康度颜色
function getHealthColor(score: number): string {
  if (score >= 90) return '#67C23A'
  if (score >= 70) return '#409EFF'
  if (score >= 50) return '#E6A23C'
  return '#F56C6C'
}

// 获取健康度状态文字
function getHealthStatus(status: string): string {
  const statusMap: Record<string, string> = {
    'excellent': t('healthStatus.excellent'),
    'good': t('healthStatus.good'),
    'warning': t('healthStatus.warning'),
    'critical': t('healthStatus.critical')
  }
  return statusMap[status] || status
}

// 获取设备类型颜色
function getDeviceTypeColor(type: string): string {
  return deviceTypeColors[type] || '#909399'
}

// 带宽格式化
function formatBandwidth(mbps: number): string {
  if (mbps >= 1000) {
    return `${(mbps / 1000).toFixed(1)} Gbps`
  }
  return `${mbps} Mbps`
}

async function loadDashboardData() {
  loading.value = true
  try {
    const [stats, prefixes, logs, deviceTypesData, circuitTypesData] = await Promise.all([
      getDashboardStats(),
      getPrefixesUsage(),
      getRecentLogs(8),
      getDeviceTypes(),
      getCircuitTypes()
    ])
    dashboardStats.value = stats
    prefixesUsage.value = prefixes
    recentLogs.value = logs
    deviceTypes.value = deviceTypesData
    circuitTypes.value = circuitTypesData
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<template>
  <div class="dashboard-page">
    <div class="overview-cards" v-loading="loading">
      <!-- 站点统计 - 所有角色可见 -->
      <div v-if="visibleCards.includes('sites')" class="overview-card">
        <div class="overview-card-label">{{ t('sites.title') }}</div>
        <div class="overview-card-value">{{ dashboardStats?.sites.total || 0 }}</div>
        <div class="overview-card-trend">{{ t('topology.deviceCount') }}</div>
      </div>
      <!-- 设备统计 - 所有角色可见 -->
      <div v-if="visibleCards.includes('devices')" class="overview-card overview-card-purple">
        <div class="overview-card-label">{{ t('devices.title') }}</div>
        <div class="overview-card-value">{{ dashboardStats?.devices.total || 0 }}</div>
        <div class="overview-card-trend">{{ dashboardStats?.devices.online || 0 }} {{ t('dashboard.onlineDevices') }}</div>
      </div>
      <!-- 带宽统计 - 所有角色可见 -->
      <div v-if="visibleCards.includes('bandwidth')" class="overview-card overview-card-success">
        <div class="overview-card-label">{{ t('circuits.bandwidth') }}</div>
        <div class="overview-card-value">{{ formatBandwidth(dashboardStats?.circuits.bandwidth || 0) }}</div>
        <div class="overview-card-trend">{{ dashboardStats?.circuits.normal || 0 }} {{ t('monitor.normal') }}</div>
      </div>
      <!-- IPAM统计 - 工程师和管理员可见 -->
      <div v-if="visibleCards.includes('ipam')" class="overview-card overview-card-blue">
        <div class="overview-card-label">{{ t('ipam.usage') }}</div>
        <div class="overview-card-value">{{ dashboardStats?.ip.percent || 0 }}%</div>
        <div class="overview-card-trend">{{ dashboardStats?.ip.used || 0 }}/{{ dashboardStats?.ip.total || 0 }} {{ t('ipam.used') }}</div>
      </div>
      <!-- 备份统计 - 工程师和管理员可见 -->
      <div v-if="visibleCards.includes('backups')" class="overview-card overview-card-warning">
        <div class="overview-card-label">{{ t('backups.title') }}</div>
        <div class="overview-card-value">{{ dashboardStats?.backups.successful || 0 }}/{{ dashboardStats?.backups.failed || 0 }}</div>
        <div class="overview-card-trend">{{ t('backups.backupSuccess') }} / {{ t('backups.backupFailed') }}</div>
      </div>
      <!-- 系统健康 - 仅管理员可见 -->
      <div v-if="visibleCards.includes('health')" class="overview-card" :style="{ borderLeftColor: getHealthColor(dashboardStats?.health.score || 0) }">
        <div class="overview-card-label">{{ t('dashboard.systemStatus') }}</div>
        <div class="overview-card-value">{{ dashboardStats?.health.score || 0 }}</div>
        <div class="overview-card-trend" :style="{ color: getHealthColor(dashboardStats?.health.score || 0) }">
          {{ getHealthStatus(dashboardStats?.health.status || 'unknown') }}
        </div>
      </div>
    </div>

    <!-- 专线类型分布 - 工程师和管理员可见 -->
    <div v-if="isAdmin || isEngineer" class="circuit-types-card">
      <div class="card-title">
        <el-icon><Connection /></el-icon>
        {{ t('circuits.type') }}{{ t('common.distribution') }}
      </div>
      <div class="circuit-types-section">
        <div v-for="circuitType in circuitTypes" :key="circuitType.type" class="circuit-type-card" :style="{ borderColor: circuitType.color }">
          <div class="circuit-type-header">
            <span class="circuit-type-dot" :style="{ backgroundColor: circuitType.color }"></span>
            <span class="circuit-type-name">{{ circuitType.name }}</span>
          </div>
          <div class="circuit-type-stats">
            <div class="circuit-stat">
              <span class="circuit-stat-label">{{ t('common.total') }}</span>
              <span class="circuit-stat-value">{{ circuitType.value }} {{ t('circuits.title') }}</span>
            </div>
            <div class="circuit-stat">
              <span class="circuit-stat-label">{{ t('circuits.bandwidth') }}</span>
              <span class="circuit-stat-value">{{ formatBandwidth(circuitType.bandwidth) }}</span>
            </div>
          </div>
        </div>
        <el-empty v-if="circuitTypes.length === 0" :description="t('common.noData')" />
      </div>
    </div>

    <div class="grid-layout">
      <!-- IP子网使用情况 - 工程师和管理员可见 -->
      <el-card v-if="isAdmin || isEngineer" class="table-card" shadow="never">
        <template #header>
          <div class="card-title">
            <el-icon><Monitor /></el-icon>
            {{ t('ipam.subnet') }}{{ t('ipam.usage') }}
          </div>
        </template>
        <div class="usage-section">
          <div v-for="prefix in prefixesUsage" :key="prefix.id" class="usage-row">
            <div class="usage-name">
              <strong>{{ prefix.network }}</strong>
              <span class="usage-tag">{{ prefix.usage }}</span>
            </div>
            <div class="usage-bar-wrapper">
              <div class="usage-bar">
                <div 
                  class="usage-fill" 
                  :class="{ 'danger': prefix.usage_percent > 80 }"
                  :style="{ width: `${prefix.usage_percent}%` }"
                ></div>
              </div>
              <span class="usage-percent">{{ prefix.usage_percent }}%</span>
            </div>
          </div>
          <el-empty v-if="prefixesUsage.length === 0" :description="t('common.noData')" />
        </div>
      </el-card>

      <el-card class="table-card" shadow="never">
        <template #header>
          <div class="card-title">
            <el-icon><Cpu /></el-icon>
            {{ t('devices.deviceType') }}{{ t('common.type') }}
          </div>
        </template>
        <div class="device-types-section">
          <div v-for="deviceType in deviceTypes" :key="deviceType.type" class="device-type-row">
            <div class="device-type-info">
              <span class="device-type-dot" :style="{ backgroundColor: getDeviceTypeColor(deviceType.type) }"></span>
              <span class="device-type-name">{{ deviceType.name }}</span>
            </div>
            <div class="device-type-count">{{ deviceType.value }}</div>
          </div>
          <el-empty v-if="deviceTypes.length === 0" :description="t('common.noData')" />
        </div>
      </el-card>

      <!-- 操作日志 - 工程师和管理员可见 -->
      <el-card v-if="isAdmin || isEngineer" class="table-card" shadow="never">
        <template #header>
          <div class="card-title">
            <el-icon><Clock /></el-icon>
            {{ t('dashboard.recentActivity') }}
          </div>
        </template>
        <el-input
          v-model="searchQuery"
          :placeholder="t('common.search') + '...'"
          prefix-icon="Search"
          clearable
          style="margin-bottom: 16px"
        />
        <div class="activity-list">
          <div v-for="log in filteredLogs" :key="log.id" class="activity-item">
            <div class="activity-icon">
              <el-icon>
                <Document />
              </el-icon>
            </div>
            <div class="activity-content">
              <div class="activity-header">
                <strong>{{ getActionTranslation(log.action) }}</strong>
                <span class="activity-resource">· {{ getResourceTranslation(log.resource) }}</span>
              </div>
              <div class="activity-detail">{{ getDetailTranslation(log.detail) }}</div>
              <div class="activity-time">{{ log.created_at ? formatTime(log.created_at) : '-' }}</div>
            </div>
          </div>
          <el-empty v-if="filteredLogs.length === 0" :description="t('common.noData')" />
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.overview-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border-left: 3px solid #8c8c8c;
  transition: all 0.2s ease;
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.overview-card-success { border-left-color: #52c41a; }
.overview-card-warning { border-left-color: #faad14; }
.overview-card-blue { border-left-color: #1890ff; }
.overview-card-purple { border-left-color: #722ed1; }

.overview-card-label {
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 6px;
}

.overview-card-value {
  font-size: 28px;
  font-weight: 700;
  color: #262626;
  line-height: 1.2;
  margin-bottom: 4px;
}

.overview-card-trend {
  font-size: 12px;
  color: #bfbfbf;
}

.grid-layout {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.circuit-types-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.circuit-types-section {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
}

.circuit-type-card {
  flex: 1;
  min-width: 180px;
  border-radius: 8px;
  padding: 16px;
  border: 2px solid #e8e8e8;
  background: #fafafa;
  transition: all 0.2s ease;
}

.circuit-type-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.circuit-type-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.circuit-type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.circuit-type-name {
  font-weight: 600;
  color: #262626;
  font-size: 14px;
}

.circuit-type-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.circuit-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.circuit-stat-label {
  font-size: 12px;
  color: #8c8c8c;
}

.circuit-stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.table-card {
  border-radius: 8px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #262626;
  font-size: 15px;
}

.usage-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.usage-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.usage-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.usage-tag {
  font-size: 12px;
  color: #8c8c8c;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.usage-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.usage-bar {
  flex: 1;
  height: 10px;
  background: #f0f0f0;
  border-radius: 999px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  background: linear-gradient(90deg, #1890ff, #36cfc9);
  border-radius: inherit;
  transition: width 0.3s ease;
}

.usage-fill.danger {
  background: linear-gradient(90deg, #ff4d4f, #faad14);
}

.usage-percent {
  font-weight: 600;
  color: #262626;
  width: 48px;
  text-align: right;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  gap: 14px;
  padding: 14px;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.15s ease;
}

.activity-item:hover {
  background: #f5f7fa;
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #e6f7ff;
  color: #1890ff;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.activity-header strong {
  font-size: 14px;
  color: #262626;
}

.activity-resource {
  font-size: 13px;
  color: #595959;
}

.activity-detail {
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.activity-time {
  font-size: 12px;
  color: #bfbfbf;
}

@media (max-width: 1200px) {
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .grid-layout {
    grid-template-columns: 1fr;
  }
}

.device-types-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-type-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 6px;
  transition: background 0.2s;
}

.device-type-row:hover {
  background: #f0f0f0;
}

.device-type-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.device-type-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.device-type-name {
  font-size: 14px;
  color: #262626;
}

.device-type-count {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}
</style>
