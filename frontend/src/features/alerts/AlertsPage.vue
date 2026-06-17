<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../../store'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox, ElDialog, ElButton, ElDatePicker, ElTabPane, ElTabs, ElBadge } from 'element-plus'
import { Bell, Clock, Refresh, CircleClose, Warning, DataLine, Connection, DocumentChecked, View, InfoFilled, Calendar, Monitor, DocumentCopy, SetUp, BellFilled, WarningFilled } from '@element-plus/icons-vue'
import AIPrediction from '../../components/AIPrediction.vue'
import { getAlertRecords, type AlertRecord } from '../../api/alerts'
import { getLocale } from '@/i18n'
import { useI18n } from 'vue-i18n'

const { locale, t } = useI18n()
interface Alert {
  type: string
  title: string
  due: string
  days: number
  level: 'danger' | 'warn' | 'ok'
  detail?: string
  ipId?: string | number
  deviceId?: string | number
  circuitId?: string | number
  backupId?: string
  suggestion?: string
}

interface ExpiringIP {
  id: string | number
  address: string
  prefixId: string | number | null
  usage: string
  owner: string
  expireAt: string
  remainingDays: number
}

// AI异常检测接口
interface Anomaly {
  id: string
  type: string
  title: string
  description: string
  level: 'danger' | 'warn' | 'info'
  target: string
  targetId: string
  metric: string
  currentValue: string
  threshold: string
  suggestion: string
  detectedAt: string
}

const router = useRouter()
const store = useAppStore()
const { circuits, devices, backups, prefixes, ipAddresses } = storeToRefs(store)
const { prefixNetwork, updateIPAddress } = store

const today = new Date()
today.setHours(0, 0, 0, 0)

const activeTab = ref('overview')
const showRenewDialog = ref(false)
const editingIP = ref<ExpiringIP | null>(null)
const renewForm = ref({
  expireAt: ''
})

const searchKeyword = ref('')
const selectedLevel = ref('all')

// 告警通知状态
const notifications = ref<{id: string; type: string; title: string; message: string; time: string; read: boolean}[]>([])

async function loadAlertRecords() {
  try {
    const records = await getAlertRecords({ status: 'active', limit: 10 })
    notifications.value = records.map((record: AlertRecord) => {
      const now = new Date()
      const createdAt = new Date(record.created_at)
      const diffMinutes = Math.floor((now.getTime() - createdAt.getTime()) / 60000)
      let timeText = ''
      if (diffMinutes < 1) {
        timeText = t('alerts.justNow')
      } else if (diffMinutes < 60) {
        timeText = t('alerts.minutesAgo', { count: diffMinutes })
      } else if (diffMinutes < 1440) {
        timeText = t('alerts.hoursAgo', { count: Math.floor(diffMinutes / 60) })
      } else {
        timeText = t('alerts.daysAgo', { count: Math.floor(diffMinutes / 1440) })
      }
      
      let title = ''
      if (record.alert_type === 'latency') {
        title = t('alerts.highLatency')
      } else if (record.alert_type === 'packet_loss') {
        title = t('alerts.highPacketLoss')
      } else if (record.alert_type === 'status') {
        title = t('alerts.statusAbnormal')
      } else {
        title = t('alerts.alertTriggered')
      }
      
      return {
        id: String(record.id),
        type: record.severity === 'critical' ? 'danger' : record.severity === 'warning' ? 'warn' : 'info',
        title,
        message: record.message,
        time: timeText,
        read: false
      }
    })
  } catch (error) {
    console.error('加载告警记录失败:', error)
    // 如果API调用失败，显示空列表或提示信息
  }
}

function markAllAsRead() {
  notifications.value.forEach(n => n.read = true)
  ElMessage.success(t('alerts.markedAllAsRead'))
}

onMounted(() => {
  loadAlertRecords()
})

function daysUntilDate(dateText: string): number {
  const date = new Date(`${dateText}T00:00:00+08:00`)
  const diff = date.getTime() - today.getTime()
  return Math.ceil(diff / 86400000)
}

// IP到期预警数据
const expiringIPs = computed((): ExpiringIP[] => {
  const result: ExpiringIP[] = []
  ipAddresses.value.forEach((ip) => {
    if (ip.expireAt && ip.status !== 'available') {
      const days = daysUntilDate(ip.expireAt)
      if (days >= 0 && days <= 30) {
        result.push({
          id: ip.id,
          address: ip.address,
          prefixId: ip.prefixId,
          usage: ip.usage || '-',
          owner: ip.owner || '-',
          expireAt: ip.expireAt,
          remainingDays: days
        })
      }
    }
  })
  return result.sort((a, b) => a.remainingDays - b.remainingDays)
})

const filteredExpiringIPs = computed(() => {
  let result = expiringIPs.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(ip => 
      ip.address.toLowerCase().includes(keyword) ||
      ip.usage.toLowerCase().includes(keyword) ||
      ip.owner.toLowerCase().includes(keyword)
    )
  }
  if (selectedLevel.value === 'danger') {
    result = result.filter(ip => ip.remainingDays <= 7)
  } else if (selectedLevel.value === 'warn') {
    result = result.filter(ip => ip.remainingDays > 7)
  }
  return result
})

const filteredDeviceAlerts = computed(() => {
  let result = deviceAlerts.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(alert => 
      alert.title.toLowerCase().includes(keyword) ||
      (alert.detail && alert.detail.toLowerCase().includes(keyword))
    )
  }
  if (selectedLevel.value !== 'all') {
    result = result.filter(alert => alert.level === selectedLevel.value)
  }
  return result
})

const filteredCircuitAlerts = computed(() => {
  let result = circuitAlerts.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(alert => 
      alert.title.toLowerCase().includes(keyword) ||
      (alert.detail && alert.detail.toLowerCase().includes(keyword))
    )
  }
  if (selectedLevel.value !== 'all') {
    result = result.filter(alert => alert.level === selectedLevel.value)
  }
  return result
})

const filteredBackupAlerts = computed(() => {
  let result = backupAlerts.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(alert => 
      alert.title.toLowerCase().includes(keyword) ||
      (alert.detail && alert.detail.toLowerCase().includes(keyword))
    )
  }
  if (selectedLevel.value !== 'all') {
    result = result.filter(alert => alert.level === selectedLevel.value)
  }
  return result
})

const filteredPrefixAlerts = computed(() => {
  let result = prefixAlerts.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(alert => 
      alert.title.toLowerCase().includes(keyword) ||
      (alert.detail && alert.detail.toLowerCase().includes(keyword))
    )
  }
  if (selectedLevel.value !== 'all') {
    result = result.filter(alert => alert.level === selectedLevel.value)
  }
  return result
})

// 专线合同预警
const circuitAlerts = computed((): Alert[] => {
  const result: Alert[] = []
  circuits.value.forEach((circuit) => {
    const days = daysUntilDate(circuit.contractEnd)
    if (days >= 0 && days <= 30) {
      result.push({
        type: t('alerts.circuitContract'),
        title: circuit.name,
        due: circuit.contractEnd,
        days,
        level: days <= 7 ? 'danger' : 'warn',
        detail: circuit.circuitNo,
        circuitId: circuit.id
      })
    }
  })
  return result.sort((a, b) => a.days - b.days)
})

// 设备保修预警
const deviceAlerts = computed((): Alert[] => {
  const result: Alert[] = []
  devices.value.forEach((device) => {
    const days = daysUntilDate(device.warrantyEnd)
    if (days >= 0 && days <= 30) {
      result.push({
        type: t('alerts.deviceWarranty'),
        title: device.name,
        due: device.warrantyEnd,
        days,
        level: days <= 7 ? 'danger' : 'warn',
        detail: device.sn,
        deviceId: device.id
      })
    }
  })
  return result.sort((a, b) => a.days - b.days)
})

// 备份失败预警
const backupAlerts = computed((): Alert[] => {
  const result: Alert[] = []
  backups.value
    .filter((backup) => backup.status === t('alerts.failed'))
    .forEach((backup) => {
      const device = devices.value.find((d) => d.id === backup.deviceId)
      result.push({
        type: t('alerts.backupFailed'),
        title: device?.name || '-',
        due: backup.createdAt,
        days: 0,
        level: 'danger',
        detail: backup.size ? `${(backup.size / 1024).toFixed(1)} KB` : '-',
        deviceId: backup.deviceId,
        backupId: backup.id
      })
    })
  return result
})

// 子网容量预警
const prefixAlerts = computed((): Alert[] => {
  const result: Alert[] = []
  prefixes.value.forEach((prefix) => {
    const used = ipAddresses.value.filter((ip) => ip.prefixId === prefix.id).length
    const percent = used / 254
    if (percent >= 0.8) {
      result.push({
        type: t('alerts.subnetCapacity'),
        title: prefix.network,
        due: `${Math.round(percent * 100)}%`,
        days: 0,
        level: 'danger',
        detail: `${used}/254`
      })
    }
  })
  return result
})

// ==================== AI异常行为检测 ====================

// AI异常检测 - 设备状态异常
const deviceAnomalies = computed((): Anomaly[] => {
  const anomalies: Anomaly[] = []
  
  devices.value.forEach((device) => {
    if (device.status === 'offline') {
      anomalies.push({
        id: `status-offline-${device.id}`,
        type: t('alerts.statusAbnormal'),
        title: t('alerts.deviceOffline', { name: device.name }),
        description: t('alerts.deviceOfflineDesc'),
        level: 'danger',
        target: t('alerts.device'),
        targetId: String(device.id),
        metric: t('alerts.status'),
        currentValue: t('alerts.offline'),
        threshold: t('alerts.online'),
        suggestion: t('alerts.deviceOfflineSuggestion'),
        detectedAt: new Date().toLocaleString(getLocale() || 'zh-CN')
      })
    } else if (device.status === 'repair') {
      anomalies.push({
        id: `status-repair-${device.id}`,
        type: t('alerts.statusAbnormal'),
        title: t('alerts.deviceRepairing', { name: device.name }),
        description: t('alerts.deviceRepairingDesc'),
        level: 'warn',
        target: t('alerts.device'),
        targetId: String(device.id),
        metric: t('alerts.status'),
        currentValue: t('alerts.repairing'),
        threshold: t('alerts.online'),
        suggestion: t('alerts.deviceRepairingSuggestion'),
        detectedAt: new Date().toLocaleString(locale.value || getLocale() || 'zh-CN')
      })
    }
  })
  
  return anomalies
})

// AI异常检测 - 专线质量异常
const circuitAnomalies = computed((): Anomaly[] => {
  const anomalies: Anomaly[] = []
  
  circuits.value.forEach((circuit) => {
    if (circuit.status === 'down') {
      anomalies.push({
        id: `circuit-down-${circuit.id}`,
        type: t('alerts.connectionAbnormal'),
        title: t('alerts.circuitDown', { name: circuit.name }),
        description: t('alerts.circuitDownDesc'),
        level: 'danger',
        target: t('alerts.circuit'),
        targetId: String(circuit.id),
        metric: t('alerts.status'),
        currentValue: t('alerts.down'),
        threshold: t('alerts.normal'),
        suggestion: t('alerts.circuitDownSuggestion'),
        detectedAt: new Date().toLocaleString(locale.value || getLocale() || 'zh-CN')
      })
    } else if (circuit.status === 'unstable') {
      anomalies.push({
        id: `circuit-unstable-${circuit.id}`,
        type: t('alerts.connectionAbnormal'),
        title: t('alerts.circuitUnstable', { name: circuit.name }),
        description: t('alerts.circuitUnstableDesc'),
        level: 'warn',
        target: t('alerts.circuit'),
        targetId: String(circuit.id),
        metric: t('alerts.status'),
        currentValue: t('alerts.unstable'),
        threshold: t('alerts.normal'),
        suggestion: t('alerts.circuitUnstableSuggestion'),
        detectedAt: new Date().toLocaleString(locale.value || getLocale() || 'zh-CN')
      })
    }
  })
  
  return anomalies
})

// AI异常检测 - 备份成功率异常
const backupAnomaly = computed((): Anomaly | null => {
  const sevenDaysAgo = new Date()
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
  
  const recentBackups = backups.value.filter((backup) => {
    const backupDate = new Date(backup.createdAt)
    return backupDate >= sevenDaysAgo
  })
  
  if (recentBackups.length === 0) return null
  
  const failedCount = recentBackups.filter((b) => b.status === t('alerts.failed')).length
  const successRate = ((recentBackups.length - failedCount) / recentBackups.length) * 100
  
  if (successRate < 80) {
    return {
      id: 'backup-success-rate',
      type: t('alerts.backupAbnormal'),
      title: t('alerts.backupSuccessRateLow'),
      description: t('alerts.backupSuccessRateDesc', { total: recentBackups.length, success: recentBackups.length - failedCount, rate: successRate.toFixed(1) }),
      level: successRate < 50 ? 'danger' : 'warn',
      target: t('alerts.system'),
      targetId: '',
      metric: t('alerts.backupSuccessRate'),
      currentValue: `${successRate.toFixed(1)}%`,
      threshold: '80%',
      suggestion: t('alerts.backupSuccessRateSuggestion'),
      detectedAt: new Date().toLocaleString(locale.value || getLocale() || 'zh-CN')
    }
  }
  
  return null
})

// AI异常检测 - IP池耗尽预测
const ipPoolAnomaly = computed((): Anomaly | null => {
  const anomalies: Anomaly[] = []
  
  prefixes.value.forEach((prefix) => {
    const used = ipAddresses.value.filter((ip) => ip.prefixId === prefix.id && ip.status !== 'available').length
    const percent = (used / 254) * 100
    
    if (percent >= 70) {
      const daysToExhaust = Math.ceil((254 - used) / Math.max(1, used / 30))
      
      anomalies.push({
        id: `ip-pool-${prefix.id}`,
        type: t('alerts.ipPoolWarning'),
        title: t('alerts.ipPoolExhausting', { network: prefix.network }),
        description: t('alerts.ipPoolExhaustingDesc', { used, percent: percent.toFixed(1), days: daysToExhaust }),
        level: percent >= 90 ? 'danger' : 'warn',
        target: t('alerts.subnet'),
        targetId: String(prefix.id),
        metric: t('alerts.ipUsage'),
        currentValue: `${percent.toFixed(1)}%`,
        threshold: '70%',
        suggestion: t('alerts.ipPoolSuggestion', { days: daysToExhaust }),
        detectedAt: new Date().toLocaleString(locale?.value || getLocale() || 'zh-CN')
      })
    }
  })
  
  return anomalies.sort((a, b) => (b.level === 'danger' ? 1 : 0) - (a.level === 'danger' ? 1 : 0))[0] || null
})

// 合并所有AI异常检测
const aiAnomalies = computed((): Anomaly[] => {
  const all: Anomaly[] = [
    ...deviceAnomalies.value,
    ...circuitAnomalies.value
  ]
  
  if (backupAnomaly.value) all.push(backupAnomaly.value)
  if (ipPoolAnomaly.value) all.push(ipPoolAnomaly.value)
  
  return all
})

// 所有预警
const allAlerts = computed((): Alert[] => {
  const result: Alert[] = []
  
  expiringIPs.value.forEach((ip) => {
    result.push({
      type: t('alerts.ipExpiring'),
      title: ip.address,
      due: ip.expireAt,
      days: ip.remainingDays,
      level: ip.remainingDays <= 7 ? 'danger' : 'warn',
      detail: ip.usage,
      ipId: ip.id
    })
  })
  
  result.push(...circuitAlerts.value)
  result.push(...deviceAlerts.value)
  result.push(...backupAlerts.value)
  result.push(...prefixAlerts.value)
  
  return result.sort((a, b) => a.days - b.days)
})

const dangerAlerts = computed(() => allAlerts.value.filter(a => a.level === 'danger'))
const warnAlerts = computed(() => allAlerts.value.filter(a => a.level === 'warn'))
const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

function getAlertIcon(type: string) {
  const map: Record<string, any> = {
    [t('alerts.circuitContract')]: Connection,
    [t('alerts.deviceWarranty')]: Monitor,
    [t('alerts.backupFailed')]: DocumentCopy,
    [t('alerts.subnetCapacity')]: SetUp,
    [t('alerts.ipExpiring')]: Calendar
  }
  return map[type] || Bell
}

function getLevelType(level: string) {
  const map: Record<string, string> = {
    'danger': 'danger',
    'warn': 'warning',
    'ok': 'success'
  }
  return map[level] || 'info'
}

function openRenewDialog(ip: ExpiringIP) {
  editingIP.value = ip
  renewForm.value = {
    expireAt: ''
  }
  showRenewDialog.value = true
}

function handleRenew() {
  if (!renewForm.value.expireAt) {
    ElMessage.warning(t('alerts.selectNewExpireDate'))
    return
  }
  if (!editingIP.value) return
  
  updateIPAddress(String(editingIP.value.id), { expireAt: renewForm.value.expireAt })
  ElMessage.success(t('alerts.ipRenewed'))
  showRenewDialog.value = false
  editingIP.value = null
}

function closeRenewDialog() {
  showRenewDialog.value = false
  editingIP.value = null
}

const handleReleaseIP = async (ip: ExpiringIP) => {
  try {
    await ElMessageBox.confirm(
      t('alerts.confirmReleaseIP', { address: ip.address }),
      t('common.confirm'),
      { confirmButtonText: t('alerts.release'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
    updateIPAddress(String(ip.id), {
      deviceId: null,
      usage: '',
      owner: '',
      status: 'available',
      expireAt: ''
    })
    ElMessage.success(t('alerts.ipReleased'))
  } catch {
    // 用户取消
  }
}

const handleViewDevice = (deviceId: string | number | undefined) => {
  if (deviceId) {
    router.push(`/devices?id=${deviceId}`)
  }
}

const handleViewCircuit = (circuitId: string | number | undefined) => {
  if (circuitId) {
    router.push(`/circuits?id=${circuitId}`)
  }
}

const handleViewAnomalyTarget = (anomaly: Anomaly) => {
  if (anomaly.target === t('alerts.device')) {
    router.push(`/devices?id=${anomaly.targetId}`)
  } else if (anomaly.target === t('alerts.circuit')) {
    router.push(`/circuits?id=${anomaly.targetId}`)
  } else if (anomaly.target === t('alerts.subnet')) {
    router.push('/ipam?tab=prefixes')
  }
}

function goToAISettings() {
  router.push('/system/ai-settings')
}
</script>

<template>
  <div class="alerts-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <p class="description">{{ t('alerts.description') }}</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="goToAISettings">
          <el-icon><Setting /></el-icon>
          {{ t('alerts.aiSettings') }}
        </el-button>
      </div>
    </div>

    <!-- 统计概览卡片 -->
    <div class="overview-cards">
      <div class="overview-card">
        <div class="overview-card-icon"><BellFilled /></div>
        <div class="overview-card-content">
          <div class="overview-card-label">{{ t('alerts.totalAlerts') }}</div>
          <div class="overview-card-value">{{ allAlerts.length }}</div>
        </div>
      </div>
      <div class="overview-card overview-card-danger">
        <div class="overview-card-icon"><WarningFilled /></div>
        <div class="overview-card-content">
          <div class="overview-card-label">{{ t('alerts.criticalAlerts') }}</div>
          <div class="overview-card-value">{{ dangerAlerts.length }}</div>
        </div>
      </div>
      <div class="overview-card overview-card-warning">
        <div class="overview-card-icon"><Warning /></div>
        <div class="overview-card-content">
          <div class="overview-card-label">{{ t('alerts.warningAlerts') }}</div>
          <div class="overview-card-value">{{ warnAlerts.length }}</div>
        </div>
      </div>
      <div class="overview-card overview-card-success">
        <div class="overview-card-icon"><DataLine /></div>
        <div class="overview-card-content">
          <div class="overview-card-label">{{ t('alerts.aiAnomalyDetection') }}</div>
          <div class="overview-card-value">{{ aiAnomalies.length }}</div>
        </div>
      </div>
    </div>

    <!-- 告警通知面板 -->
    <el-card class="notifications-card" shadow="never">
      <template #header>
        <div class="table-header">
          <div class="card-title">
            <el-icon><Bell /></el-icon>
            {{ t('alerts.alertNotifications') }}
            <el-badge v-if="unreadCount > 0" :value="unreadCount" class="notification-badge" />
          </div>
          <el-button v-if="unreadCount > 0" text @click="markAllAsRead">
            {{ t('alerts.markAllAsRead') }}
          </el-button>
        </div>
      </template>
      
      <div class="notifications-list">
        <div 
          v-for="notification in notifications" 
          :key="notification.id" 
          :class="['notification-item', { 'unread': !notification.read }]"
        >
          <div class="notification-icon" :class="`notification-${notification.type}`">
            <el-icon><component :is="notification.type === 'danger' ? WarningFilled : Warning" /></el-icon>
          </div>
          <div class="notification-content">
            <div class="notification-title">
              <el-tag :type="notification.type === 'danger' ? 'danger' : 'warning'" size="small">
                {{ notification.type === 'danger' ? t('alerts.critical') : t('alerts.warning') }}
              </el-tag>
              {{ notification.title }}
            </div>
            <div class="notification-message">{{ notification.message }}</div>
          </div>
          <div class="notification-time">{{ notification.time }}</div>
        </div>
      </div>
    </el-card>

    <!-- 搜索和筛选栏 -->
    <el-card class="table-card" shadow="never">
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          :placeholder="t('alerts.searchPlaceholder')"
          class="search-input"
          clearable
          prefix-icon="Search"
        />
        <el-select
          v-model="selectedLevel"
          :placeholder="t('alerts.filterByLevel')"
          clearable
          class="level-select"
        >
          <el-option label="全部" value="all" />
          <el-option :label="t('alerts.critical')" value="danger" />
          <el-option :label="t('alerts.warning')" value="warn" />
        </el-select>
        <el-button
          v-if="searchKeyword || selectedLevel !== 'all'"
          text
          @click="searchKeyword = ''; selectedLevel = 'all'"
        >
          {{ t('alerts.resetFilter') }}
        </el-button>
      </div>
    </el-card>

    <!-- Tab页签内容 -->
    <el-tabs v-model="activeTab" type="card" class="alerts-tabs">
      <!-- 概览 -->
      <el-tab-pane :label="t('alerts.overview')" name="overview">
        <!-- AI智能预测中心 -->
        <el-card class="table-card" shadow="never">
          <template #header>
            <div class="table-header">
              <div class="card-title">
                <el-icon><InfoFilled /></el-icon>
                {{ t('alerts.aiPredictionCenter') }}
              </div>
              <el-tag type="primary" effect="light">
                <InfoFilled style="width: 16px; height: 16px; margin-right: 4px;" />
                {{ t('alerts.llmPowered') }}
              </el-tag>
            </div>
          </template>
          <AIPrediction />
        </el-card>

        <!-- AI异常检测 -->
        <el-card v-if="aiAnomalies.length > 0" class="table-card" shadow="never">
          <template #header>
            <div class="table-header">
              <div class="card-title">
                <el-icon><Warning /></el-icon>
                {{ t('alerts.aiAnomalyDetection') }}
              </div>
              <el-tag type="warning" effect="light">
                {{ aiAnomalies.length }} {{ t('alerts.anomalies') }}
              </el-tag>
            </div>
          </template>

          <div class="anomaly-list">
            <div 
              v-for="anomaly in aiAnomalies" 
              :key="anomaly.id" 
              class="anomaly-item"
              :class="`anomaly-${anomaly.level}`"
            >
              <div class="anomaly-icon">
                <el-icon>
                  <component :is="anomaly.type.includes(t('alerts.device')) ? Monitor : anomaly.type.includes(t('alerts.circuit')) ? Connection : anomaly.type.includes(t('alerts.backup')) ? DocumentChecked : DataLine" />
                </el-icon>
              </div>
              <div class="anomaly-content">
                <div class="anomaly-header">
                  <el-tag :type="anomaly.level === 'danger' ? 'danger' : 'warning'" effect="dark" size="small">
                    {{ anomaly.type }}
                  </el-tag>
                  <span class="anomaly-title">{{ anomaly.title }}</span>
                </div>
                <div class="anomaly-description">{{ anomaly.description }}</div>
                <div class="anomaly-metrics">
                  <span class="metric-item">
                    <span class="metric-label">{{ t('alerts.currentValue') }}：</span>
                    <span class="metric-value">{{ anomaly.currentValue }}</span>
                  </span>
                  <span class="metric-item">
                    <span class="metric-label">{{ t('alerts.threshold') }}：</span>
                    <span class="metric-value">{{ anomaly.threshold }}</span>
                  </span>
                </div>
                <div class="anomaly-suggestion">
                  <el-icon><Clock /></el-icon>
                  {{ anomaly.suggestion }}
                </div>
                <div class="anomaly-footer">
                  <span class="anomaly-detected-at">
                    <el-icon><Clock /></el-icon>
                    {{ t('alerts.detectedAt') }}：{{ anomaly.detectedAt }}
                  </span>
                </div>
              </div>
              <div class="anomaly-action">
                <el-button type="primary" link @click="handleViewAnomalyTarget(anomaly)">
                  <el-icon><View /></el-icon>
                  {{ t('common.viewDetail') }}
                </el-button>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 快速预警列表 -->
        <el-card v-if="allAlerts.length > 0" class="table-card" shadow="never">
          <template #header>
            <div class="table-header">
              <div class="card-title">
                <el-icon><Bell /></el-icon>
                {{ t('alerts.alertOverview') }}
              </div>
            </div>
          </template>

          <div class="quick-alert-list">
            <div 
              v-for="(alert, index) in allAlerts.slice(0, 5)" 
              :key="index" 
              class="quick-alert-item" 
              :class="`alert-${alert.level}`"
            >
              <div class="quick-alert-icon">
                <el-icon><component :is="getAlertIcon(alert.type)" /></el-icon>
              </div>
              <div class="quick-alert-content">
                <div class="quick-alert-title">{{ alert.title }}</div>
                <div class="quick-alert-meta">{{ alert.type }} · {{ alert.due }}</div>
              </div>
              <el-tag :type="getLevelType(alert.level)" effect="light" size="small">
                {{ alert.days > 0 ? `${alert.days}${t('alerts.days')}` : t('alerts.immediately') }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- IP到期预警 -->
      <el-tab-pane :label="t('alerts.ipExpiring')" name="ip-expire">
        <el-card class="table-card" shadow="never">
          <template #header>
            <div class="table-header">
              <div class="card-title">
                <el-icon><Calendar /></el-icon>
                {{ t('alerts.ipExpiringAlerts') }}
              </div>
              <el-tag :type="expiringIPs.length > 0 ? 'warning' : 'success'" effect="light">
                {{ expiringIPs.length }} {{ t('alerts.alerts') }}
              </el-tag>
            </div>
          </template>

          <div v-if="filteredExpiringIPs.length === 0" class="empty-state">
            <el-empty :description="searchKeyword || selectedLevel !== 'all' ? t('alerts.noMatchingResults') : t('alerts.noExpiringIPs')" />
          </div>

          <el-table
            v-else
            :data="filteredExpiringIPs"
            style="width: 100%"
            stripe
            border
          >
            <el-table-column prop="address" :label="t('alerts.ipAddress')" min-width="120">
              <template #default="{ row }">
                <code class="ip-address">{{ row.address }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="prefixId" :label="t('alerts.subnet')" min-width="140">
              <template #default="{ row }">{{ prefixNetwork(row.prefixId) }}</template>
            </el-table-column>
            <el-table-column prop="usage" :label="t('alerts.usage')" min-width="100" />
            <el-table-column prop="owner" :label="t('alerts.owner')" min-width="80" />
            <el-table-column prop="expireAt" :label="t('alerts.expireDate')" min-width="110" />
            <el-table-column :label="t('alerts.daysRemaining')" min-width="100" align="center">
              <template #default="{ row }">
                <el-tag 
                  :type="row.remainingDays <= 7 ? 'danger' : 'warning'" 
                  effect="light"
                  :class="{ 'bold': row.remainingDays <= 7 }"
                >
                  {{ row.remainingDays }} {{ t('alerts.days') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" min-width="140" align="center">
              <template #default="{ row }">
                <el-button 
                  link 
                  type="primary" 
                  size="small" 
                  @click="openRenewDialog(row)"
                >
                  <el-icon><Refresh /></el-icon>
                  {{ t('alerts.renew') }}
                </el-button>
                <el-button 
                  link 
                  type="danger" 
                  size="small" 
                  @click="handleReleaseIP(row)"
                >
                  <el-icon><CircleClose /></el-icon>
                  {{ t('alerts.release') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 设备预警 -->
      <el-tab-pane :label="t('alerts.deviceAlerts')" name="device">
        <el-card class="table-card" shadow="never">
          <template #header>
            <div class="table-header">
              <div class="card-title">
                <el-icon><Monitor /></el-icon>
                {{ t('alerts.deviceWarrantyAlerts') }}
              </div>
              <el-tag :type="deviceAlerts.length > 0 ? 'warning' : 'success'" effect="light">
                {{ deviceAlerts.length }} {{ t('alerts.alerts') }}
              </el-tag>
            </div>
          </template>

          <div v-if="filteredDeviceAlerts.length === 0" class="empty-state">
            <el-empty :description="searchKeyword || selectedLevel !== 'all' ? t('alerts.noMatchingResults') : t('alerts.noDeviceWarrantyAlerts')" />
          </div>

          <el-table v-else :data="filteredDeviceAlerts" style="width: 100%" stripe border>
            <el-table-column :label="t('alerts.alertType')" min-width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" effect="dark" size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('alerts.device')" min-width="150">
              <template #default="{ row }">{{ row.title }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.serialNumber')" min-width="100">
              <template #default="{ row }">{{ row.detail || '-' }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.warrantyExpire')" min-width="110">
              <template #default="{ row }">{{ row.due }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.daysRemaining')" min-width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" effect="light" size="small">
                  {{ row.days > 0 ? `${row.days} ${t('alerts.days')}` : t('alerts.expired') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" min-width="100" align="center">
              <template #default="{ row }">
                <el-button v-if="row.deviceId" type="primary" link size="small" @click="handleViewDevice(row.deviceId)">
                  <el-icon><View /></el-icon>
                  {{ t('common.viewDetail') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 专线预警 -->
      <el-tab-pane :label="t('alerts.circuitAlerts')" name="circuit">
        <el-card class="table-card" shadow="never">
          <template #header>
            <div class="table-header">
              <div class="card-title">
                <el-icon><Connection /></el-icon>
                {{ t('alerts.circuitContractAlerts') }}
              </div>
              <el-tag :type="circuitAlerts.length > 0 ? 'warning' : 'success'" effect="light">
                {{ circuitAlerts.length }} {{ t('alerts.alerts') }}
              </el-tag>
            </div>
          </template>

          <div v-if="filteredCircuitAlerts.length === 0" class="empty-state">
            <el-empty :description="searchKeyword || selectedLevel !== 'all' ? t('alerts.noMatchingResults') : t('alerts.noCircuitContractAlerts')" />
          </div>

          <el-table v-else :data="filteredCircuitAlerts" style="width: 100%" stripe border>
            <el-table-column :label="t('alerts.alertType')" min-width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" effect="dark" size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('alerts.circuit')" min-width="150">
              <template #default="{ row }">{{ row.title }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.circuitNo')" min-width="100">
              <template #default="{ row }">{{ row.detail || '-' }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.contractExpire')" min-width="110">
              <template #default="{ row }">{{ row.due }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.daysRemaining')" min-width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" effect="light" size="small">
                  {{ row.days > 0 ? `${row.days} ${t('alerts.days')}` : t('alerts.expired') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" min-width="100" align="center">
              <template #default="{ row }">
                <el-button v-if="row.circuitId" type="primary" link size="small" @click="handleViewCircuit(row.circuitId)">
                  <el-icon><View /></el-icon>
                  {{ t('common.viewDetail') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 备份预警 -->
      <el-tab-pane :label="t('alerts.backupAlerts')" name="backup">
        <el-card class="table-card" shadow="never">
          <template #header>
            <div class="table-header">
              <div class="card-title">
                <el-icon><DocumentCopy /></el-icon>
                {{ t('alerts.backupFailedAlerts') }}
              </div>
              <el-tag :type="backupAlerts.length > 0 ? 'danger' : 'success'" effect="light">
                {{ backupAlerts.length }} {{ t('alerts.failures') }}
              </el-tag>
            </div>
          </template>

          <div v-if="filteredBackupAlerts.length === 0" class="empty-state">
            <el-empty :description="searchKeyword || selectedLevel !== 'all' ? t('alerts.noMatchingResults') : t('alerts.noBackupFailures')" />
          </div>

          <el-table v-else :data="filteredBackupAlerts" style="width: 100%" stripe border>
            <el-table-column :label="t('alerts.alertType')" min-width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" effect="dark" size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('alerts.device')" min-width="150">
              <template #default="{ row }">{{ row.title }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.backupSize')" min-width="100">
              <template #default="{ row }">{{ row.detail || '-' }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.failureTime')" min-width="130">
              <template #default="{ row }">{{ row.due }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.severity')" min-width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" effect="light" size="small">
                  {{ row.level === 'danger' ? t('alerts.critical') : t('alerts.warning') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" min-width="100" align="center">
              <template #default="{ row }">
                <el-button v-if="row.deviceId" type="primary" link size="small" @click="handleViewDevice(row.deviceId)">
                  <el-icon><View /></el-icon>
                  {{ t('common.viewDetail') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 子网预警 -->
      <el-tab-pane :label="t('alerts.subnetAlerts')" name="prefix">
        <el-card class="table-card" shadow="never">
          <template #header>
            <div class="table-header">
              <div class="card-title">
                <el-icon><SetUp /></el-icon>
                {{ t('alerts.subnetCapacityAlerts') }}
              </div>
              <el-tag :type="prefixAlerts.length > 0 ? 'danger' : 'success'" effect="light">
                {{ prefixAlerts.length }} {{ t('alerts.alerts') }}
              </el-tag>
            </div>
          </template>

          <div v-if="filteredPrefixAlerts.length === 0" class="empty-state">
            <el-empty :description="searchKeyword || selectedLevel !== 'all' ? t('alerts.noMatchingResults') : t('alerts.noSubnetCapacityAlerts')" />
          </div>

          <el-table v-else :data="filteredPrefixAlerts" style="width: 100%" stripe border>
            <el-table-column :label="t('alerts.alertType')" min-width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" effect="dark" size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('alerts.subnet')" min-width="150">
              <template #default="{ row }">{{ row.title }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.ipUsage')" min-width="100">
              <template #default="{ row }">{{ row.detail || '-' }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.currentUsage')" min-width="100">
              <template #default="{ row }">{{ row.due }}</template>
            </el-table-column>
            <el-table-column :label="t('alerts.severity')" min-width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" effect="light" size="small">
                  {{ row.level === 'danger' ? t('alerts.critical') : t('alerts.warning') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('common.actions')" min-width="100" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="router.push('/ipam?tab=prefixes')">
                  <el-icon><View /></el-icon>
                  {{ t('alerts.manageSubnet') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- IP续期对话框 -->
    <ElDialog
      v-model="showRenewDialog"
      :title="t('alerts.ipRenewal')"
      width="480px"
      :close-on-click-modal="false"
    >
      <div v-if="editingIP" class="renew-form">
        <div class="form-row">
          <label>{{ t('alerts.ipAddress') }}</label>
          <code>{{ editingIP.address }}</code>
        </div>
        <div class="form-row">
          <label>{{ t('alerts.originalExpireDate') }}</label>
          <span>{{ editingIP.expireAt }}</span>
        </div>
        <div class="form-row">
          <label>{{ t('alerts.newExpireDate') }} *</label>
          <el-date-picker
            v-model="renewForm.expireAt"
            type="date"
            :placeholder="t('alerts.selectNewExpireDate')"
            style="width: 100%"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="closeRenewDialog">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleRenew">{{ t('alerts.confirmRenew') }}</el-button>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.alerts-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left h1 {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 8px 0;
}

.header-left .description {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.overview-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.overview-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #d9d9d9, transparent);
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.overview-card-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #e6f7ff, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #1890ff;
  transition: transform 0.3s ease;
}

.overview-card:hover .overview-card-icon {
  transform: scale(1.1);
}

.overview-card-danger {
  border-color: #ffccc7;
}

.overview-card-danger::before {
  background: linear-gradient(90deg, #ff4d4f, #ff7875);
}

.overview-card-danger .overview-card-icon {
  background: linear-gradient(135deg, #fff2f0, #fff);
  color: #ff4d4f;
}

.overview-card-danger .overview-card-value {
  color: #ff4d4f;
}

.overview-card-warning {
  border-color: #ffe58f;
}

.overview-card-warning::before {
  background: linear-gradient(90deg, #faad14, #ffc53d);
}

.overview-card-warning .overview-card-icon {
  background: linear-gradient(135deg, #fffbe6, #fff);
  color: #faad14;
}

.overview-card-warning .overview-card-value {
  color: #faad14;
}

.overview-card-success {
  border-color: #b7eb8f;
}

.overview-card-success::before {
  background: linear-gradient(90deg, #52c41a, #73d13d);
}

.overview-card-success .overview-card-icon {
  background: linear-gradient(135deg, #f6ffed, #fff);
  color: #52c41a;
}

.overview-card-success .overview-card-value {
  color: #52c41a;
}

.overview-card-content {
  flex: 1;
}

.overview-card-label {
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 6px;
}

.overview-card-value {
  font-size: 32px;
  font-weight: 700;
  color: #262626;
  line-height: 1.2;
}

.table-card {
  border-radius: 8px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-input {
  width: 300px;
}

.level-select {
  width: 160px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.card-title .el-icon {
  color: #1890ff;
}

.notification-badge {
  margin-left: 8px;
}

.notifications-card {
  border-radius: 8px;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #d9d9d9;
  transition: all 0.2s ease;
}

.notification-item.unread {
  background: #fffbe6;
  border-left-color: #faad14;
}

.notification-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #8c8c8c;
}

.notification-icon.notification-danger {
  background: #fff2f0;
  color: #ff4d4f;
}

.notification-icon.notification-warning {
  background: #fffbe6;
  color: #faad14;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 13px;
  color: #8c8c8c;
}

.notification-time {
  font-size: 12px;
  color: #bfbfbf;
}

.alerts-tabs {
  background: transparent;
}

.alerts-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
  background: #fff;
  padding: 0 16px;
  border-radius: 8px 8px 0 0;
  border: 1px solid #e8e8e8;
}

.alerts-tabs :deep(.el-tabs__content) {
  padding: 0;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.ip-address {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  color: #1890ff;
  background: #e6f7ff;
  padding: 4px 8px;
  border-radius: 4px;
}

.bold {
  font-weight: bold;
}

.anomaly-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.anomaly-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%);
  border-radius: 12px;
  border: 1px solid #ffe58f;
  transition: all 0.2s ease;
}

.anomaly-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.anomaly-item.anomaly-danger {
  background: linear-gradient(135deg, #fff2f0 0%, #fff0f0 100%);
  border-color: #ffccc7;
}

.anomaly-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #faad14;
  flex-shrink: 0;
}

.anomaly-danger .anomaly-icon {
  color: #ff4d4f;
}

.anomaly-content {
  flex: 1;
  min-width: 0;
}

.anomaly-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.anomaly-title {
  font-size: 15px;
  font-weight: 600;
  color: #262626;
}

.anomaly-description {
  font-size: 14px;
  color: #595959;
  margin-bottom: 12px;
  line-height: 1.5;
}

.anomaly-metrics {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
}

.metric-item {
  font-size: 13px;
}

.metric-label {
  color: #8c8c8c;
}

.metric-value {
  color: #262626;
  font-weight: 500;
}

.anomaly-suggestion {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: #52c41a;
  padding: 10px 14px;
  background: #f6ffed;
  border-radius: 6px;
  margin-bottom: 12px;
}

.anomaly-suggestion .el-icon {
  color: #52c41a;
  font-size: 14px;
  margin-top: 1px;
}

.anomaly-footer {
  display: flex;
  justify-content: flex-end;
}

.anomaly-detected-at {
  font-size: 12px;
  color: #bfbfbf;
}

.anomaly-action {
  flex-shrink: 0;
}

.quick-alert-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #d9d9d9;
}

.quick-alert-item.alert-danger {
  background: #fff2f0;
  border-left-color: #ff4d4f;
}

.quick-alert-item.alert-warn {
  background: #fffbe6;
  border-left-color: #faad14;
}

.quick-alert-icon {
  font-size: 20px;
  color: #8c8c8c;
}

.quick-alert-content {
  flex: 1;
  min-width: 0;
}

.quick-alert-title {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.quick-alert-meta {
  font-size: 12px;
  color: #8c8c8c;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #d9d9d9;
}

.alert-item.alert-danger {
  background: #fff2f0;
  border-left-color: #ff4d4f;
}

.alert-item.alert-warn {
  background: #fffbe6;
  border-left-color: #faad14;
}

.alert-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #8c8c8c;
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.alert-title {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.alert-detail {
  font-size: 13px;
  color: #8c8c8c;
}

.alert-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.alert-due {
  font-size: 13px;
  color: #8c8c8c;
}

.alert-action {
  display: flex;
  gap: 8px;
}

.renew-form {
  padding: 16px 0;
}

.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.form-row label {
  font-size: 14px;
  font-weight: 500;
  color: #595959;
}

.form-row code {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  color: #1890ff;
  background: #e6f7ff;
  padding: 4px 8px;
  border-radius: 4px;
}

.form-row span {
  font-size: 14px;
  color: #262626;
}

@media (max-width: 1200px) {
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .quick-alert-list {
    grid-template-columns: 1fr;
  }
  
  .anomaly-item {
    flex-direction: column;
  }
  
  .anomaly-action {
    width: 100%;
    margin-top: 12px;
  }
}
</style>