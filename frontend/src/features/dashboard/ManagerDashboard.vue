<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import {
  getManagerStats,
  getRisks,
  getCircuitCostTrend,
  getDeviceLifecycle,
  getMonthlyIncidents,
  downloadMonthlyReport,
  type ManagerStats,
  type RisksResponse,
  type CircuitCostTrend,
  type DeviceLifecycle,
  type MonthlyIncidents,
  type RiskItem,
  type Incident,
  type AgeDistribution,
  type OldDevice,
  type ExpiringItem
} from '@/api/dashboard'
import {
  TrendCharts,
  Warning,
  Money,
  Clock,
  CircleCheck,
  CircleClose,
  ArrowUp,
  ArrowDown,
  Document,
  Download,
  Check,
  Close,
  ArrowRight
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const managerStats = ref<ManagerStats | null>(null)
const risksData = ref<RisksResponse | null>(null)
const costTrendData = ref<CircuitCostTrend | null>(null)
const lifecycleData = ref<DeviceLifecycle | null>(null)
const monthlyIncidents = ref<MonthlyIncidents | null>(null)
const showExpiringDialog = ref(false)

const isAdmin = computed(() => authStore.user?.role === 'super_admin')

function formatMoney(amount: number): string {
  if (amount >= 10000) {
    return `¥${(amount / 10000).toFixed(1)}万`
  }
  return `¥${amount.toLocaleString()}`
}

function getTrendIcon(trend: string | null) {
  if (trend === 'up') return ArrowUp
  if (trend === 'down') return ArrowDown
  return null
}

function getTrendColor(trend: string | null): string {
  return trend === 'up' ? '#67C23A' : trend === 'down' ? '#F56C6C' : '#909399'
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'high': return '#F56C6C'
    case 'medium': return '#E6A23C'
    case 'low': return '#67C23A'
    default: return '#909399'
  }
}

function getSeverityIcon(severity: string): string {
  switch (severity) {
    case 'high': return '🔴'
    case 'medium': return '🟡'
    case 'low': return '🟢'
    default: return '⚪'
  }
}

function getSeverityLabel(severity: string): string {
  switch (severity) {
    case 'high': return '高风险'
    case 'medium': return '中风险'
    case 'low': return '低风险'
    default: return severity
  }
}

function getSeverityBorderColor(severity: string): string {
  switch (severity) {
    case 'high': return '#F56C6C'
    case 'medium': return '#E6A23C'
    case 'low': return '#67C23A'
    default: return '#909399'
  }
}

function navigateTo(url: string) {
  router.push(url)
}

function initCostChart() {
  if (!costTrendData.value) return
  
  const chartDom = document.getElementById('cost-trend-chart')
  if (!chartDom) return
  
  const myChart = echarts.init(chartDom)
  
  const months = costTrendData.value.months.map(m => m.slice(5) + '月')
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = params[0].name + '<br/>'
        params.forEach((p: any) => {
          result += `${p.seriesName}: ¥${p.value.toLocaleString()}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['总费用', '互联网专线', 'MPLS', 'SD-WAN'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: months
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => {
          if (value >= 10000) return `${value / 10000}万`
          return value.toString()
        }
      }
    },
    series: [
      {
        name: '总费用',
        type: 'line',
        data: costTrendData.value.total_costs,
        smooth: true,
        lineStyle: { width: 3 },
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '互联网专线',
        type: 'line',
        data: costTrendData.value.by_type['互联网专线'],
        smooth: true,
        lineStyle: { width: 2 }
      },
      {
        name: 'MPLS',
        type: 'line',
        data: costTrendData.value.by_type['MPLS'],
        smooth: true,
        lineStyle: { width: 2 }
      },
      {
        name: 'SD-WAN',
        type: 'line',
        data: costTrendData.value.by_type['SD-WAN'],
        smooth: true,
        lineStyle: { width: 2 }
      }
    ]
  }
  
  myChart.setOption(option)
}

function initLifecycleChart() {
  if (!lifecycleData.value) return
  
  const chartDom = document.getElementById('lifecycle-chart')
  if (!chartDom) return
  
  const myChart = echarts.init(chartDom)
  
  const data = lifecycleData.value.age_distribution
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: data.map(d => d.range),
      axisLabel: { fontSize: 12 }
    },
    series: [
      {
        type: 'bar',
        data: data.map(d => ({
          value: d.count,
          itemStyle: {
            color: d.color === 'green' ? '#67C23A' : d.color === 'yellow' ? '#E6A23C' : '#F56C6C'
          }
        })),
        barWidth: 30,
        label: {
          show: true,
          position: 'right',
          formatter: '{c}台'
        }
      }
    ]
  }
  
  myChart.setOption(option)
}

async function loadData() {
  loading.value = true
  try {
    const [stats, risks, costTrend, lifecycle, incidents] = await Promise.all([
      getManagerStats(),
      getRisks(),
      getCircuitCostTrend(),
      getDeviceLifecycle(),
      getMonthlyIncidents()
    ])
    
    managerStats.value = stats
    risksData.value = risks
    costTrendData.value = costTrend
    lifecycleData.value = lifecycle
    monthlyIncidents.value = incidents
    
    setTimeout(() => {
      initCostChart()
      initLifecycleChart()
    }, 100)
  } catch (error) {
    console.error('Failed to load manager dashboard data:', error)
  } finally {
    loading.value = false
  }
}

async function downloadReport(month: string) {
  try {
    const blob = await downloadMonthlyReport(month)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report_${month}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download report:', error)
  }
}

function getCurrentMonth(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function getSeverityRisks(severity: string): RiskItem[] {
  if (!risksData.value) return []
  return risksData.value.risks.filter(r => r.severity === severity)
}

function getAgeColor(range: string): string {
  if (range.includes('>')) return '#F56C6C'
  if (range.includes('3-5')) return '#E6A23C'
  return '#67C23A'
}

function getOldDevicesWarning(): string | null {
  if (!lifecycleData.value) return null
  const oldCount = lifecycleData.value.age_distribution.find(d => d.range === '> 5年')?.count || 0
  if (oldCount > 0) {
    return `当前有 ${oldCount} 台设备使用年限超过5年，建议制定更换计划`
  }
  return null
}

function getExpiringDisplayCount(): number {
  const stats = managerStats.value?.expiring_soon
  if (!stats) return 0
  return stats.urgent_count > 0 ? stats.urgent_count : stats.warning_count
}

function getExpiringIconStyle(): Record<string, string> {
  const stats = managerStats.value?.expiring_soon
  if (!stats || stats.total_count === 0) {
    return { background: '#f6ffed', color: '#52c41a' }
  }
  if (stats.urgent_count > 0) {
    return { background: '#fff2f0', color: '#F56C6C' }
  }
  return { background: '#fff7e6', color: '#E6A23C' }
}

function getExpiringTrendColor(): string {
  const stats = managerStats.value?.expiring_soon
  if (!stats || stats.total_count === 0) return '#67C23A'
  if (stats.urgent_count > 0) return '#F56C6C'
  return '#E6A23C'
}

function getExpiringTrendText(): string {
  const stats = managerStats.value?.expiring_soon
  if (!stats || stats.total_count === 0) return '无到期事项 ✓'
  const parts = []
  if (stats.urgent_count > 0) parts.push(`🔴${stats.urgent_count}项紧急`)
  if (stats.warning_count > 0) parts.push(`🟡${stats.warning_count}项即将到期`)
  return parts.join(' ')
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="manager-dashboard" v-loading="loading">
    <div class="page-header">
      <h1>管理看板</h1>
    </div>

    <!-- 第一行：四个核心指标卡片 -->
    <div class="overview-cards">
      <!-- 本月网络可用性 -->
      <div class="overview-card" @click="navigateTo('/circuits')">
        <div class="card-icon" style="background: #e6f7ff; color: #409EFF">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">本月网络可用性</div>
          <div class="card-value">
            {{ managerStats?.availability.current !== null ? managerStats?.availability.current + '%' : '暂无数据' }}
            <el-icon v-if="getTrendIcon(managerStats?.availability.trend || null)" :style="{ color: getTrendColor(managerStats?.availability.trend || null) }">
              <component :is="getTrendIcon(managerStats?.availability.trend || null)" />
            </el-icon>
          </div>
          <div class="card-trend" :style="{ color: getTrendColor(managerStats?.availability.trend || null) }">
            {{ managerStats?.availability.trend === 'up' ? '较上月 ↑' : managerStats?.availability.trend === 'down' ? '较上月 ↓' : '与上月持平' }}
          </div>
        </div>
      </div>

      <!-- 专线月租费用 -->
      <div class="overview-card" @click="navigateTo('/circuits')">
        <div class="card-icon" style="background: #f6ffed; color: #52c41a">
          <el-icon><Money /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">专线月租费用</div>
          <div class="card-value">{{ formatMoney(managerStats?.circuit_cost.current || 0) }}</div>
          <div class="card-trend" :style="{ color: getTrendColor(managerStats?.circuit_cost.trend === 'up' ? 'down' : managerStats?.circuit_cost.trend || null) }">
            {{ managerStats?.circuit_cost.trend === 'up' ? '同比 ↑' : managerStats?.circuit_cost.trend === 'down' ? '同比 ↓' : '较稳定' }}
          </div>
        </div>
      </div>

      <!-- 未解决故障 -->
      <div class="overview-card" :class="{ 'has-alert': (managerStats?.open_incidents.count || 0) > 0 }" @click="navigateTo('/alerts?tab=circuit')">
        <div class="card-icon" :style="{ background: (managerStats?.open_incidents.count || 0) > 0 ? '#fff2f0' : '#f6ffed', color: (managerStats?.open_incidents.count || 0) > 0 ? '#F56C6C' : '#52c41a' }">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">未解决故障</div>
          <div class="card-value" :style="{ color: (managerStats?.open_incidents.count || 0) > 0 ? '#F56C6C' : '#67C23A' }">
            {{ managerStats?.open_incidents.count || 0 }}
            <span class="unit">条</span>
          </div>
          <div class="card-trend">
            {{ (managerStats?.open_incidents.count || 0) > 0 ? `最长持续 ${managerStats?.open_incidents.max_duration_hours}h` : '无故障 ✓' }}
          </div>
        </div>
      </div>

      <!-- 即将到期事项（两级预警） -->
      <div class="overview-card" :class="{ 'has-alert': (managerStats?.expiring_soon.urgent_count || 0) > 0, 'has-warning': (managerStats?.expiring_soon.urgent_count || 0) === 0 && (managerStats?.expiring_soon.warning_count || 0) > 0 }" @click="showExpiringDialog = true">
        <div class="card-icon" :style="getExpiringIconStyle()">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-label">即将到期事项</div>
          <div class="card-value" :style="{ color: (managerStats?.expiring_soon.urgent_count || 0) > 0 ? '#F56C6C' : (managerStats?.expiring_soon.warning_count || 0) > 0 ? '#E6A23C' : '#67C23A' }">
            {{ getExpiringDisplayCount() }}
            <span class="unit">项</span>
          </div>
          <div class="card-trend" :style="{ color: getExpiringTrendColor() }">
            {{ getExpiringTrendText() }}
          </div>
        </div>
      </div>
    </div>

    <!-- 🔴🟡 到期预警详情弹窗 -->
    <el-dialog v-model="showExpiringDialog" title="到期事项预警" width="600px" :close-on-click-modal="false">
      <div class="expiring-dialog-body">
        <!-- 🔴 紧急 -->
        <div v-if="(managerStats?.expiring_soon.urgent_items?.length || 0) > 0" class="expiring-section">
          <div class="expiring-section-title urgent">
            🔴 紧急（30天内）
          </div>
          <div v-for="item in managerStats?.expiring_soon.urgent_items" :key="item.name" class="expiring-item urgent-item">
            <div class="expiring-item-main">
              <span class="expiring-item-name">{{ item.name }}</span>
              <span class="expiring-item-type">{{ item.type }}</span>
            </div>
            <div class="expiring-item-meta">
              <span class="expiring-item-date">{{ item.expire_date }} 到期</span>
              <span class="expiring-item-days">还有 {{ item.days_left }} 天</span>
            </div>
          </div>
        </div>
        <!-- 🟡 即将到期 -->
        <div v-if="(managerStats?.expiring_soon.warning_items?.length || 0) > 0" class="expiring-section">
          <div class="expiring-section-title warning">
            🟡 即将到期（31-60天）
          </div>
          <div v-for="item in managerStats?.expiring_soon.warning_items" :key="item.name" class="expiring-item warning-item">
            <div class="expiring-item-main">
              <span class="expiring-item-name">{{ item.name }}</span>
              <span class="expiring-item-type">{{ item.type }}</span>
            </div>
            <div class="expiring-item-meta">
              <span class="expiring-item-date">{{ item.expire_date }} 到期</span>
              <span class="expiring-item-days">还有 {{ item.days_left }} 天</span>
            </div>
          </div>
        </div>
        <div v-if="(managerStats?.expiring_soon.total_count || 0) === 0" class="expiring-empty">
          <el-icon><CircleCheck /></el-icon>
          <span>暂无到期事项，一切正常 ✓</span>
        </div>
      </div>
    </el-dialog>

    <!-- 第二行：IT风险看板 + 专线费用趋势 -->
    <div class="main-grid">
      <!-- 左侧：IT风险看板 -->
      <div class="panel risk-panel">
        <div class="panel-header">
          <h3>IT 风险看板</h3>
          <el-button link type="primary" @click="navigateTo('/alerts')">查看全部</el-button>
        </div>
        <div class="risk-content">
          <!-- 高风险 -->
          <div v-if="getSeverityRisks('high').length > 0" class="risk-section">
            <div class="risk-header">
              <span class="risk-dot high"></span>
              <span class="risk-title">高风险</span>
              <span class="risk-count">{{ risksData?.high_count }}</span>
            </div>
            <div v-for="risk in getSeverityRisks('high')" :key="risk.title" class="risk-item" :style="{ borderLeftColor: getSeverityBorderColor('high') }">
              <div class="risk-item-title">{{ risk.title }}</div>
              <div class="risk-item-desc">{{ risk.description }}</div>
            </div>
          </div>

          <!-- 中风险 -->
          <div v-if="getSeverityRisks('medium').length > 0" class="risk-section">
            <div class="risk-header">
              <span class="risk-dot medium"></span>
              <span class="risk-title">中风险</span>
              <span class="risk-count">{{ risksData?.medium_count }}</span>
            </div>
            <div v-for="risk in getSeverityRisks('medium')" :key="risk.title" class="risk-item" :style="{ borderLeftColor: getSeverityBorderColor('medium') }">
              <div class="risk-item-title">{{ risk.title }}</div>
              <div class="risk-item-desc">{{ risk.description }}</div>
            </div>
          </div>

          <!-- 低风险 -->
          <div v-if="getSeverityRisks('low').length > 0" class="risk-section">
            <div class="risk-header">
              <span class="risk-dot low"></span>
              <span class="risk-title">低风险</span>
              <span class="risk-count">{{ risksData?.low_count }}</span>
            </div>
            <div v-for="risk in getSeverityRisks('low')" :key="risk.title" class="risk-item" :style="{ borderLeftColor: getSeverityBorderColor('low') }">
              <div class="risk-item-title">{{ risk.title }}</div>
              <div class="risk-item-desc">{{ risk.description }}</div>
            </div>
          </div>

          <!-- 无风险 -->
          <div v-if="!risksData || risksData.risks.length === 0" class="no-risk">
            <el-icon><CircleCheck /></el-icon>
            <span>暂无风险项</span>
          </div>
        </div>
      </div>

      <!-- 右侧：专线费用趋势 -->
      <div class="panel chart-panel">
        <div class="panel-header">
          <h3>专线费用趋势（近12个月）</h3>
        </div>
        <div id="cost-trend-chart" class="chart-container"></div>
        <div class="cost-breakdown">
          <div v-for="(costs, type) in costTrendData?.by_type" :key="type" class="cost-item">
            <span class="cost-label">{{ type }}</span>
            <span class="cost-value">¥{{ costs[costs.length - 1]?.toLocaleString() || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 第三行：本月故障汇总 + 设备生命周期 -->
    <div class="main-grid">
      <!-- 左侧：本月故障汇总 -->
      <div class="panel">
        <div class="panel-header">
          <h3>本月故障记录</h3>
          <span class="incident-summary" v-if="monthlyIncidents">
            本月共 {{ monthlyIncidents.total }} 次
            <template v-if="monthlyIncidents.avg_recovery_hours > 0">
              | 平均恢复 {{ monthlyIncidents.avg_recovery_hours }}h
            </template>
          </span>
        </div>
        <div class="incident-content">
          <el-table :data="monthlyIncidents?.incidents || []" style="width: 100%">
            <el-table-column prop="title" label="故障标题" min-width="150" />
            <el-table-column prop="circuit_name" label="专线" min-width="100" />
            <el-table-column prop="severity" label="严重程度" width="80">
              <template #default="{ row }">
                <el-tag :type="row.severity === 'critical' ? 'danger' : row.severity === 'major' ? 'warning' : 'info'" size="small">
                  {{ row.severity }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="started_at" label="开始时间" width="120" />
            <el-table-column prop="duration_hours" label="持续时长" width="80">
              <template #default="{ row }">{{ row.duration_hours }}h</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="70">
              <template #default="{ row }">
                <el-tag :type="row.status === 'open' ? 'danger' : 'success'" size="small">
                  {{ row.status === 'open' ? '未解决' : '已解决' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!monthlyIncidents?.incidents?.length" class="empty-table">
            <span>暂无故障记录 ✓</span>
          </div>
          <div v-if="monthlyIncidents && monthlyIncidents.total > 5" class="view-more">
            <el-button link type="primary" @click="navigateTo('/circuits')">查看全部{{ monthlyIncidents.total }}条</el-button>
          </div>
          <div v-if="monthlyIncidents?.max_duration" class="incident-footer">
            <span>最长中断：{{ monthlyIncidents.max_duration.hours }}h（{{ monthlyIncidents.max_duration.circuit }}，{{ monthlyIncidents.max_duration.date }}）</span>
          </div>
        </div>
      </div>

      <!-- 右侧：设备生命周期 -->
      <div class="panel">
        <div class="panel-header">
          <h3>设备年龄分布</h3>
        </div>
        <div class="lifecycle-content">
          <div id="lifecycle-chart" class="lifecycle-chart"></div>
          <div class="lifecycle-warning" v-if="getOldDevicesWarning()">
            <el-icon><Warning /></el-icon>
            {{ getOldDevicesWarning() }}
          </div>
        </div>
      </div>
    </div>

    <!-- 第四行：月报下载 + 待审批 -->
    <div class="main-grid">
      <!-- 左侧：月报下载 -->
      <div class="panel">
        <div class="panel-header">
          <h3>运营报告</h3>
        </div>
        <div class="report-content">
          <div class="report-list">
            <div class="report-item">
              <el-icon><Document /></el-icon>
              <span class="report-name">2026年6月报告</span>
              <el-button type="primary" plain size="small" @click="downloadReport('2026-06')">
                <el-icon><Download /></el-icon>
                下载PDF
              </el-button>
            </div>
            <div class="report-item">
              <el-icon><Document /></el-icon>
              <span class="report-name">2026年5月报告</span>
              <el-button type="primary" plain size="small" @click="downloadReport('2026-05')">
                <el-icon><Download /></el-icon>
                下载PDF
              </el-button>
            </div>
            <div class="report-item">
              <el-icon><Document /></el-icon>
              <span class="report-name">2026年4月报告</span>
              <el-button type="primary" plain size="small" @click="downloadReport('2026-04')">
                <el-icon><Download /></el-icon>
                下载PDF
              </el-button>
            </div>
          </div>
          <div class="report-actions">
            <el-button type="primary" @click="downloadReport(getCurrentMonth())">
              <el-icon><Document /></el-icon>
              下载本月报告
            </el-button>
          </div>
        </div>
      </div>

      <!-- 右侧：待审批 -->
      <div class="panel" v-if="isAdmin">
        <div class="panel-header">
          <h3>待我审批</h3>
        </div>
        <div class="approval-content">
          <div class="no-approval">
            <el-icon><CircleCheck /></el-icon>
            <span>暂无待审批事项</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.manager-dashboard {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin: 0;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

@media (max-width: 1200px) {
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

.overview-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-label {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 8px;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  color: #262626;
  line-height: 1.2;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-value .unit {
  font-size: 16px;
  font-weight: normal;
  color: #8c8c8c;
}

.card-trend {
  font-size: 12px;
  color: #bfbfbf;
}

.main-grid {
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: 20px;
  margin-bottom: 20px;
}

@media (max-width: 1200px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
}

.panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin: 0;
}

.incident-summary {
  font-size: 12px;
  color: #8c8c8c;
}

/* 风险看板 */
.risk-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.risk-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.risk-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.risk-dot.high { background: #F56C6C; }
.risk-dot.medium { background: #E6A23C; }
.risk-dot.low { background: #67C23A; }

.risk-title {
  font-weight: 600;
  font-size: 14px;
  color: #262626;
}

.risk-count {
  font-size: 12px;
  color: #8c8c8c;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 10px;
}

.risk-item {
  padding: 10px 14px;
  background: #fafafa;
  border-radius: 6px;
  border-left: 3px solid;
}

.risk-item-title {
  font-size: 13px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.risk-item-desc {
  font-size: 12px;
  color: #8c8c8c;
}

.no-risk {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #67C23A;
  font-size: 14px;
  gap: 8px;
}

/* 图表 */
.chart-container {
  height: 250px;
  width: 100%;
}

.cost-breakdown {
  display: flex;
  justify-content: space-around;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  margin-top: 16px;
}

.cost-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.cost-label {
  font-size: 12px;
  color: #8c8c8c;
}

.cost-value {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

/* 故障表格 */
.incident-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-table {
  text-align: center;
  padding: 40px;
  color: #67C23A;
  font-size: 14px;
}

.view-more {
  text-align: center;
}

.incident-footer {
  font-size: 12px;
  color: #8c8c8c;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

/* 到期预警弹窗 */
.expiring-dialog-body {
  max-height: 60vh;
  overflow-y: auto;
}

.expiring-section {
  margin-bottom: 20px;
}

.expiring-section:last-child {
  margin-bottom: 0;
}

.expiring-section-title {
  font-size: 15px;
  font-weight: 600;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.expiring-section-title.urgent {
  background: #fff2f0;
  color: #F56C6C;
}

.expiring-section-title.warning {
  background: #fff7e6;
  color: #E6A23C;
}

.expiring-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.expiring-item:last-child {
  margin-bottom: 0;
}

.urgent-item {
  background: #fff2f0;
  border-left: 3px solid #F56C6C;
}

.warning-item {
  background: #fffbe6;
  border-left: 3px solid #E6A23C;
}

.expiring-item-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expiring-item-name {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.expiring-item-type {
  font-size: 11px;
  color: #8c8c8c;
  background: rgba(0,0,0,0.04);
  padding: 2px 8px;
  border-radius: 4px;
}

.expiring-item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.expiring-item-date {
  font-size: 13px;
  color: #595959;
}

.expiring-item-days {
  font-size: 13px;
  font-weight: 500;
  color: #262626;
}

.expiring-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 8px;
  color: #67C23A;
  font-size: 14px;
}

/* 生命周期图表 */
.lifecycle-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.lifecycle-chart {
  height: 200px;
  width: 100%;
}

.lifecycle-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fff2f0;
  border-radius: 6px;
  color: #F56C6C;
  font-size: 13px;
}

/* 月报下载 */
.report-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.report-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.report-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 6px;
}

.report-item .el-icon {
  font-size: 20px;
  color: #409EFF;
}

.report-name {
  flex: 1;
  font-size: 14px;
  color: #262626;
}

.report-actions {
  display: flex;
  gap: 12px;
}

/* 待审批 */
.approval-content {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-approval {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #67C23A;
  font-size: 14px;
}
</style>
