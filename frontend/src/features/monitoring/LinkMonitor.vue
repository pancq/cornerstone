<template>
  <div class="link-monitor">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <span class="subtitle">{{ $t('monitor.subtitle') }}</span>
      </div>
      <div class="header-actions">
        <el-button type="primary" plain @click="goToAlertManagement">
          <el-icon><Bell /></el-icon>
          {{ t('monitor.alertManagement') }}
        </el-button>
        <el-select 
          v-model="schedulerInterval" 
          :placeholder="t('monitor.selectInterval')"
          style="width: 120px; margin-right: 10px;"
          @change="handleIntervalChange"
        >
          <el-option :label="t('monitor.interval1min')" :value="1" />
          <el-option :label="t('monitor.interval5min')" :value="5" />
          <el-option :label="t('monitor.interval10min')" :value="10" />
        </el-select>
        <el-button 
          :type="schedulerRunning ? 'warning' : 'success'" 
          @click="toggleScheduler"
        >
          <el-icon>
            <VideoPause v-if="schedulerRunning" />
            <VideoPlay v-else />
          </el-icon>
          {{ schedulerRunning ? t('monitor.stopScheduler') : t('monitor.startScheduler') }}
        </el-button>
        <el-button type="primary" @click="handleRefresh" :loading="isRefreshing">
          <el-icon><Refresh /></el-icon>
          {{ t('monitor.refreshMonitor') }}
        </el-button>
      </div>
    </div>

    <!-- 监控概览 -->
    <div class="monitor-summary">
      <el-card class="summary-card summary-card-success" shadow="never">
        <div class="card-content">
          <div class="card-icon">
            <el-icon><Check /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-value">{{ summary.normal }}</div>
            <div class="card-label">{{ t('monitor.normal') }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="summary-card summary-card-warning" shadow="never">
        <div class="card-content">
          <div class="card-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-value">{{ summary.warning }}</div>
            <div class="card-label">{{ t('monitor.warning') }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="summary-card summary-card-danger" shadow="never">
        <div class="card-content">
          <div class="card-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-value">{{ summary.critical }}</div>
            <div class="card-label">{{ t('monitor.critical') }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 设备监控列表 -->
    <el-card class="monitor-card" shadow="never">
      <template #header>
        <div class="card-title">
          <el-icon><Monitor /></el-icon>
          {{ t('monitor.deviceStatus') }}
        </div>
      </template>
      <el-table :data="monitorStatus" :row-key="(row: any) => row.device_id" border>
        <el-table-column prop="device_name" :label="t('monitor.deviceName')" />
        <el-table-column prop="target_ip" :label="t('monitor.targetIp')" />
        <el-table-column prop="latency" :label="t('monitor.latency')">
          <template #default="scope">
            <span :class="getStatusClass(scope.row.status)">
              {{ scope.row.latency || '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="packet_loss" :label="t('monitor.packetLoss')">
          <template #default="scope">
            <span :class="getStatusClass(scope.row.status)">
              {{ scope.row.packet_loss !== null ? scope.row.packet_loss + '%' : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('monitor.status')">
          <template #default="scope">
            <el-tag :type="getStatusTagType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" :label="t('monitor.updatedAt')">
          <template #default="scope">
            {{ formatTime(scope.row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('common.actions')">
          <template #default="{ row }">
            <el-button size="small" @click="handleHistoryClick(row)">
              <el-icon><Clock /></el-icon>
              {{ t('monitor.history') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 历史图表弹窗 -->
    <el-dialog :title="t('monitor.historyTitle', { name: selectedDeviceName })" :visible.sync="historyDialogVisible" width="800px">
      <div v-if="historyData.length > 0">
        <div ref="chartRef" class="history-chart"></div>
      </div>
      <div v-else class="empty-state">
        <el-icon class="empty-icon"><DataBoard /></el-icon>
        <p>{{ t('monitor.noHistory') }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { locale, t } = useI18n()
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Check, Warning, CircleClose, Clock, DataBoard, Monitor, VideoPlay, VideoPause, Bell } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { 
  getDeviceMonitorStatus, 
  getMonitorSummary, 
  getDeviceMonitorHistory, 
  runMonitor,
  getSchedulerStatus,
  setSchedulerInterval,
  startScheduler,
  stopScheduler
} from '../../api/monitoring'
import type { MonitorStatus, MonitorSummary, MonitorHistory } from '../../api/monitoring'
import { ElMessage } from 'element-plus'

const router = useRouter()
const isRefreshing = ref(false)
const monitorStatus = ref<MonitorStatus[]>([])
const summary = ref<MonitorSummary>({ normal: 0, warning: 0, critical: 0 })
const historyDialogVisible = ref(false)
const selectedDeviceId = ref<number>(0)
const schedulerInterval = ref(5)
const schedulerRunning = ref(false)
const selectedDeviceName = ref('')
const historyData = ref<MonitorHistory[]>([])
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const goToAlertManagement = () => {
  router.push('/monitor/alerts')
}

const handleRefresh = async () => {
  isRefreshing.value = true
  try {
    await runMonitor()
    await loadMonitorData()
    ElMessage.success(t('monitor.refreshSuccess'))
  } catch (error: any) {
    console.error('Refresh error:', error)
    ElMessage.error(t('common.error'))
  } finally {
    isRefreshing.value = false
  }
}

const loadSchedulerStatus = async () => {
  try {
    const status = await getSchedulerStatus()
    schedulerRunning.value = status.running
    schedulerInterval.value = status.interval_minutes
  } catch (error) {
    console.error('Load scheduler status error:', error)
  }
}

const handleIntervalChange = async () => {
  try {
    await setSchedulerInterval(schedulerInterval.value)
    ElMessage.success(t('monitor.intervalSet', { interval: schedulerInterval.value }))
  } catch (error: any) {
    console.error('Set interval error:', error)
    ElMessage.error(t('common.error'))
  }
}

const toggleScheduler = async () => {
  try {
    if (schedulerRunning.value) {
      await stopScheduler()
      schedulerRunning.value = false
      ElMessage.success(t('monitor.schedulerStopped'))
    } else {
      await startScheduler(schedulerInterval.value)
      schedulerRunning.value = true
      ElMessage.success(t('monitor.schedulerStarted', { interval: schedulerInterval.value }))
    }
  } catch (error: any) {
    console.error('Toggle scheduler error:', error)
    ElMessage.error(t('common.error'))
  }
}

const loadMonitorData = async () => {
  try {
    const [status, summaryData] = await Promise.all([
      getDeviceMonitorStatus(),
      getMonitorSummary()
    ])
    monitorStatus.value = status
    summary.value = summaryData
  } catch (error) {
    console.error('Load monitor data error:', error)
  }
}

const getStatusClass = (status: string): string => {
  switch (status) {
    case 'normal': return 'status-normal'
    case 'warning': return 'status-warning'
    case 'critical': return 'status-critical'
    default: return ''
  }
}

const getStatusTagType = (status: string): string => {
  switch (status) {
    case 'normal': return 'success'
    case 'warning': return 'warning'
    case 'critical': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string): string => {
  switch (status) {
    case 'normal': return t('monitor.normal')
    case 'warning': return t('monitor.warning')
    case 'critical': return t('monitor.critical')
    default: return status
  }
}

const formatTime = (timeStr: string): string => {
  if (!timeStr) return '-'
  // 确保时间字符串是UTC格式（添加Z后缀）
  const utcTimeStr = timeStr.endsWith('Z') ? timeStr : timeStr + 'Z'
  const date = new Date(utcTimeStr)
  return date.toLocaleString(locale.value || 'zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai'
  })
}

const handleHistoryClick = (row: MonitorStatus) => {
  console.log('handleHistoryClick called with row:', row)
  console.log('device_id:', row.device_id)
  showHistory(row.device_id)
}

const showHistory = async (deviceId: number) => {
  console.log('showHistory called with deviceId:', deviceId)
  console.log('monitorStatus:', monitorStatus.value)
  selectedDeviceId.value = deviceId
  const device = monitorStatus.value.find(d => d.device_id === deviceId)
  selectedDeviceName.value = device?.device_name || ''
  console.log('selectedDeviceName:', selectedDeviceName.value)
  try {
    historyData.value = await getDeviceMonitorHistory(deviceId, 60)
    console.log('historyData loaded:', historyData.value.length, 'records')
    historyDialogVisible.value = true
  } catch (error: any) {
    console.error('Load history error:', error)
    ElMessage.error(t('monitor.loadHistoryFailed', { message: error.message || t('common.unknown') }))
  }
}

const renderChart = () => {
  if (!chartRef.value || historyData.value.length === 0) return
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)
  
  const sortedData = [...historyData.value].reverse()
  const times = sortedData.map(d => {
    const date = new Date(d.created_at)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  })
  const latencies = sortedData.map(d => d.latency || null)
  const packetLosses = sortedData.map(d => d.packet_loss || null)
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: [t('monitor.latencyMs'), t('monitor.packetLossPercent')]
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLabel: {
        rotate: 45,
        fontSize: 10
      }
    },
    yAxis: [
      {
        type: 'value',
        name: t('monitor.latencyMs'),
        position: 'left'
      },
      {
        type: 'value',
        name: t('monitor.packetLossPercent'),
        position: 'right',
        min: 0,
        max: 100
      }
    ],
    series: [
      {
        name: t('monitor.latencyMs'),
        type: 'line',
        smooth: true,
        data: latencies,
        lineStyle: {
          color: '#1890ff'
        }
      },
      {
        name: t('monitor.packetLossPercent'),
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: packetLosses,
        lineStyle: {
          color: '#f5222d'
        }
      }
    ]
  }
  chartInstance.setOption(option)
}

onMounted(() => {
  loadMonitorData()
  loadSchedulerStatus()
})

watch(historyDialogVisible, (visible) => {
  if (visible) {
    setTimeout(() => {
      renderChart()
    }, 100)
  }
})
</script>

<style scoped>
.link-monitor {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header-content h2 {
  margin: 0;
  font-size: 20px;
  color: #262626;
  font-weight: 600;
}

.subtitle {
  color: #8c8c8c;
  font-size: 14px;
  margin-left: 12px;
}

.monitor-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.summary-card {
  border-radius: 8px;
}

.summary-card-success {
  border-left: 3px solid #52c41a;
}

.summary-card-warning {
  border-left: 3px solid #faad14;
}

.summary-card-danger {
  border-left: 3px solid #f5222d;
}

.card-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.card-icon {
  font-size: 32px;
}

.summary-card-success .card-icon {
  color: #52c41a;
}

.summary-card-warning .card-icon {
  color: #faad14;
}

.summary-card-danger .card-icon {
  color: #f5222d;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  color: #262626;
  line-height: 1.2;
}

.card-label {
  font-size: 13px;
  color: #8c8c8c;
}

.monitor-card {
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

.status-normal {
  color: #52c41a;
}

.status-warning {
  color: #faad14;
}

.status-critical {
  color: #f5222d;
}

.history-chart {
  height: 400px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #8c8c8c;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
</style>