<template>
  <div class="alert-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h2>{{ t('monitoring.alertManagement') }}</h2>
        <span class="subtitle">{{ t('monitoring.manageAlertRules') }}</span>
      </div>
    </div>

    <!-- 告警统计卡片 -->
    <div class="alert-summary">
      <el-card class="summary-card summary-card-info" shadow="never">
        <div class="card-content">
          <div class="card-icon">
            <el-icon><InfoFilled /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-value">{{ summary.info }}</div>
            <div class="card-label">{{ t('monitoring.info') }}</div>
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
            <div class="card-label">{{ t('monitoring.warning') }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="summary-card summary-card-danger" shadow="never">
        <div class="card-content">
          <div class="card-icon">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <div class="card-info">
            <div class="card-value">{{ summary.critical }}</div>
            <div class="card-label">{{ t('monitoring.critical') }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 标签页切换 -->
    <el-card class="main-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-tabs v-model="activeTab" @tab-change="handleTabChange">
            <el-tab-pane :label="t('monitoring.alertRules')" name="rules">
              <template #label>
                <el-icon><Setting /></el-icon>
                {{ t('monitoring.alertRules') }}
              </template>
            </el-tab-pane>
            <el-tab-pane :label="t('monitoring.alertRecords')" name="records">
              <template #label>
                <el-icon><Bell /></el-icon>
                {{ t('monitoring.alertRecords') }}
              </template>
            </el-tab-pane>
          </el-tabs>
        </div>
      </template>

      <!-- 告警规则标签页 -->
      <div v-if="activeTab === 'rules'">
        <div class="rules-header">
          <el-button type="primary" @click="showRuleDialog = true">
            <el-icon><Plus /></el-icon>
            {{ t('monitoring.addRule') }}
          </el-button>
        </div>
        
        <el-table :data="rules" :row-key="(row: any) => row.id" border>
          <el-table-column prop="name" :label="t('monitoring.ruleName')" />
          <el-table-column prop="condition_type" :label="t('monitoring.conditionType')">
            <template #default="scope">
              {{ getConditionTypeText(scope.row.condition_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="operator" :label="t('monitoring.operator')">
            <template #default="scope">
              {{ getOperatorText(scope.row.operator) }}
            </template>
          </el-table-column>
          <el-table-column prop="threshold" :label="t('monitoring.threshold')" />
          <el-table-column prop="severity" :label="t('monitoring.severity')">
            <template #default="scope">
              <el-tag :type="getSeverityTagType(scope.row.severity)">
                {{ getSeverityText(scope.row.severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="enabled" :label="t('monitoring.status')">
            <template #default="scope">
              <el-switch 
                :value="scope.row.enabled" 
                @change="handleRuleToggle(scope.row)"
                :disabled="loading"
              />
            </template>
          </el-table-column>
          <el-table-column :label="t('monitoring.actions')">
            <template #default="scope">
              <el-button size="small" @click="editRule(scope.row)">
                <el-icon><Edit /></el-icon>
                {{ t('common.edit') }}
              </el-button>
              <el-button size="small" type="danger" @click="deleteRule(scope.row.id)">
                <el-icon><Delete /></el-icon>
                {{ t('common.delete') }}
              </el-button>
              <el-button size="small" @click="testRule(scope.row.id)">
                <el-icon><VideoPlay /></el-icon>
                {{ t('monitoring.test') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 告警记录标签页 -->
      <div v-else>
        <div class="records-header">
          <el-select v-model="filterSeverity" :placeholder="t('monitoring.filterLevel')" style="width: 120px;">
            <el-option :label="t('monitoring.all')" value="" />
            <el-option :label="t('monitoring.info')" value="info" />
            <el-option :label="t('monitoring.warning')" value="warning" />
            <el-option :label="t('monitoring.critical')" value="critical" />
          </el-select>
          <el-select v-model="filterStatus" :placeholder="t('monitoring.filterStatus')" style="width: 120px;">
            <el-option :label="t('monitoring.all')" value="" />
            <el-option :label="t('monitoring.active')" value="active" />
            <el-option :label="t('monitoring.acknowledged')" value="acknowledged" />
            <el-option :label="t('monitoring.resolved')" value="resolved" />
          </el-select>
        </div>
        
        <el-table :data="records" :row-key="(row: any) => row.id" border>
          <el-table-column prop="device_id" :label="t('monitoring.deviceId')" />
          <el-table-column prop="target_ip" :label="t('monitoring.targetIp')" />
          <el-table-column prop="alert_type" :label="t('monitoring.alertType')" />
          <el-table-column prop="severity" :label="t('monitoring.severity')">
            <template #default="scope">
              <el-tag :type="getSeverityTagType(scope.row.severity)">
                {{ getSeverityText(scope.row.severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" :label="t('monitoring.message')" />
          <el-table-column prop="current_value" :label="t('monitoring.currentValue')" />
          <el-table-column prop="threshold" :label="t('monitoring.threshold')" />
          <el-table-column prop="status" :label="t('monitoring.status')">
            <template #default="scope">
              <el-tag :type="getStatusTagType(scope.row.status)">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" :label="t('monitoring.createdAt')">
            <template #default="scope">
              {{ formatTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column :label="t('monitoring.actions')">
            <template #default="scope">
              <el-button 
                v-if="scope.row.status === 'active'" 
                size="small" 
                type="warning"
                @click="handleAcknowledge(scope.row.id)"
              >
                <el-icon><Check /></el-icon>
                {{ t('monitoring.acknowledge') }}
              </el-button>
              <el-button 
                v-if="scope.row.status !== 'resolved'" 
                size="small" 
                type="success"
                @click="handleResolve(scope.row.id)"
              >
                <el-icon><Check /></el-icon>
                {{ t('monitoring.resolve') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 规则编辑弹窗 -->
    <el-dialog :title="editingRule ? t('monitoring.editRule') : t('monitoring.addRule')" v-model="showRuleDialog" width="500px">
      <el-form :model="ruleForm" label-width="120px">
        <el-form-item :label="t('monitoring.ruleName')" prop="name">
          <el-input v-model="ruleForm.name" :placeholder="t('monitoring.enterRuleName')" />
        </el-form-item>
        <el-form-item :label="t('monitoring.ruleDescription')" prop="description">
          <el-input v-model="ruleForm.description" type="textarea" :placeholder="t('monitoring.enterRuleDescription')" />
        </el-form-item>
        <el-form-item :label="t('monitoring.conditionType')" prop="condition_type">
          <el-select v-model="ruleForm.condition_type" :placeholder="t('monitoring.selectConditionType')">
            <el-option :label="t('monitoring.latency')" value="latency" />
            <el-option :label="t('monitoring.packetLoss')" value="packet_loss" />
            <el-option :label="t('monitoring.status')" value="status" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('monitoring.comparisonOperator')" prop="operator">
          <el-select v-model="ruleForm.operator" :placeholder="t('monitoring.selectOperator')">
            <el-option :label="t('monitoring.greaterThan')" value="gt" />
            <el-option :label="t('monitoring.lessThan')" value="lt" />
            <el-option :label="t('monitoring.equalTo')" value="eq" />
            <el-option :label="t('monitoring.notEqualTo')" value="ne" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('monitoring.threshold')" prop="threshold">
          <el-input-number 
            v-model="ruleForm.threshold" 
            :min="0" 
            :step="ruleForm.condition_type === 'packet_loss' ? 1 : 0.1"
            :placeholder="t('monitoring.enterThreshold')"
            :disabled="ruleForm.condition_type === 'status'"
          />
        </el-form-item>
        <el-form-item :label="t('monitoring.alertLevel')" prop="severity">
          <el-select v-model="ruleForm.severity" :placeholder="t('monitoring.selectAlertLevel')">
            <el-option :label="t('monitoring.info')" value="info" />
            <el-option :label="t('monitoring.warning')" value="warning" />
            <el-option :label="t('monitoring.critical')" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('monitoring.notificationChannels')">
          <el-checkbox-group v-model="ruleForm.notification_channels">
            <el-checkbox label="webhook" />
            <el-checkbox label="email" />
            <el-checkbox label="dingtalk" />
            <el-checkbox label="wechat" />
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showRuleDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveRule">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 测试结果弹窗 -->
    <el-dialog :title="t('monitoring.ruleTestResult')" v-model="showTestDialog" width="400px">
      <div v-if="testResults.length > 0">
        <el-table :data="testResults" border>
          <el-table-column prop="value" :label="t('monitoring.testValue')" />
          <el-table-column prop="matches" :label="t('monitoring.triggered')">
            <template #default="scope">
              <el-tag :type="scope.row.matches ? 'success' : 'info'">
                {{ scope.row.matches ? t('monitoring.yes') : t('monitoring.no') }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else>
        <p class="text-center text-gray">{{ t('monitoring.noTestResults') }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { useI18n } from 'vue-i18n'
  const { locale } = useI18n()
  import { 
  Plus, Edit, Delete, VideoPlay, Setting, Bell, InfoFilled, 
  Warning, WarningFilled, Check 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  createAlertRule,
  getAlertRules,
  updateAlertRule,
  deleteAlertRule,
  getAlertRecords,
  acknowledgeAlert,
  resolveAlert,
  getAlertSummary,
  testAlertRule
} from '../../api/alerts'
import type { AlertRule, AlertRecord, AlertSummary, TestResult } from '../../api/alerts'

const activeTab = ref('rules')
const rules = ref<AlertRule[]>([])
const records = ref<AlertRecord[]>([])
const summary = ref<AlertSummary>({ info: 0, warning: 0, critical: 0 })
const showRuleDialog = ref(false)
const showTestDialog = ref(false)
const testResults = ref<TestResult[]>([])
const editingRule = ref<AlertRule | null>(null)
const loading = ref(false)

const filterSeverity = ref('')
const filterStatus = ref('')

const ruleForm = ref({
  name: '',
  description: '',
  device_id: undefined as number | undefined,
  condition_type: 'latency' as 'latency' | 'packet_loss' | 'status',
  operator: 'gt' as 'gt' | 'lt' | 'eq' | 'ne',
  threshold: 0,
  severity: 'warning' as 'info' | 'warning' | 'critical',
  enabled: true,
  notification_channels: [] as string[]
})

const loadRules = async () => {
  loading.value = true
  try {
    rules.value = await getAlertRules()
  } catch (error) {
    console.error('Load rules error:', error)
    ElMessage.error('加载规则失败')
  } finally {
    loading.value = false
  }
}

const loadRecords = async () => {
  loading.value = true
  try {
    records.value = await getAlertRecords({
      severity: filterSeverity.value as 'info' | 'warning' | 'critical' | undefined,
      status: filterStatus.value as 'active' | 'acknowledged' | 'resolved' | undefined,
      limit: 100
    })
  } catch (error) {
    console.error('Load records error:', error)
    ElMessage.error('加载记录失败')
  } finally {
    loading.value = false
  }
}

const loadSummary = async () => {
  try {
    summary.value = await getAlertSummary()
  } catch (error) {
    console.error('Load summary error:', error)
  }
}

const handleTabChange = () => {
  if (activeTab.value === 'rules') {
    loadRules()
  } else {
    loadRecords()
  }
}

const saveRule = async () => {
  if (!ruleForm.value.name) {
    ElMessage.warning('请输入规则名称')
    return
  }

  try {
    if (editingRule.value) {
      await updateAlertRule(editingRule.value.id, ruleForm.value)
      ElMessage.success('规则更新成功')
    } else {
      await createAlertRule(ruleForm.value)
      ElMessage.success('规则创建成功')
    }
    showRuleDialog.value = false
    loadRules()
    resetForm()
  } catch (error: any) {
    ElMessage.error('保存失败: ' + (error.message || '未知错误'))
  }
}

const editRule = (rule: AlertRule) => {
  editingRule.value = rule
  ruleForm.value = {
    name: rule.name,
    description: rule.description || '',
    device_id: rule.device_id,
    condition_type: rule.condition_type,
    operator: rule.operator,
    threshold: rule.threshold,
    severity: rule.severity,
    enabled: rule.enabled,
    notification_channels: rule.notification_channels || []
  }
  showRuleDialog.value = true
}

const deleteRule = async (ruleId: number) => {
  if (!confirm('确定要删除这条规则吗？')) {
    return
  }

  try {
    await deleteAlertRule(ruleId)
    ElMessage.success('规则删除成功')
    loadRules()
  } catch (error: any) {
    ElMessage.error('删除失败: ' + (error.message || '未知错误'))
  }
}

const testRule = async (ruleId: number) => {
  try {
    testResults.value = await testAlertRule(ruleId)
    showTestDialog.value = true
  } catch (error: any) {
    ElMessage.error('测试失败: ' + (error.message || '未知错误'))
  }
}

const handleRuleToggle = async (rule: AlertRule) => {
  try {
    await updateAlertRule(rule.id, { enabled: !rule.enabled })
    ElMessage.success(`规则已${rule.enabled ? '禁用' : '启用'}`)
    loadRules()
  } catch (error: any) {
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  }
}

const handleAcknowledge = async (recordId: number) => {
  try {
    await acknowledgeAlert(recordId)
    ElMessage.success(t('monitoring.alertAcknowledged'))
    loadRecords()
    loadSummary()
  } catch (error: any) {
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  }
}

const handleResolve = async (recordId: number) => {
  try {
    await resolveAlert(recordId)
    ElMessage.success(t('monitoring.alertResolved'))
    loadRecords()
    loadSummary()
  } catch (error: any) {
    ElMessage.error('操作失败: ' + (error.message || '未知错误'))
  }
}

const resetForm = () => {
  editingRule.value = null
  ruleForm.value = {
    name: '',
    description: '',
    device_id: undefined,
    condition_type: 'latency',
    operator: 'gt',
    threshold: 0,
    severity: 'warning',
    enabled: true,
    notification_channels: []
  }
}

const getConditionTypeText = (type: string): string => {
  const map: Record<string, string> = {
    latency: t('monitoring.latency'),
    packet_loss: t('monitoring.packetLoss'),
    status: t('monitoring.status')
  }
  return map[type] || type
}

const getOperatorText = (operator: string): string => {
  const map: Record<string, string> = {
    gt: t('monitoring.greaterThan'),
    lt: t('monitoring.lessThan'),
    eq: t('monitoring.equalTo'),
    ne: t('monitoring.notEqualTo')
  }
  return map[operator] || operator
}

const getSeverityTagType = (severity: string): string => {
  const map: Record<string, string> = {
    info: 'info',
    warning: 'warning',
    critical: 'danger'
  }
  return map[severity] || 'info'
}

const getSeverityText = (severity: string): string => {
  const map: Record<string, string> = {
    info: t('monitoring.info'),
    warning: t('monitoring.warning'),
    critical: t('monitoring.critical')
  }
  return map[severity] || severity
}

const getStatusTagType = (status: string): string => {
  const map: Record<string, string> = {
    active: 'danger',
    acknowledged: 'warning',
    resolved: 'success'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string): string => {
  const map: Record<string, string> = {
    active: t('monitoring.active'),
    acknowledged: t('monitoring.acknowledged'),
    resolved: t('monitoring.resolved')
  }
  return map[status] || status
}

const formatTime = (timeStr: string): string => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString(locale?.value || 'zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  loadRules()
  loadSummary()
})
</script>

<style scoped>
.alert-management {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.alert-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.summary-card {
  border-radius: 8px;
}

.summary-card-info {
  border-left: 3px solid #1890ff;
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

.summary-card-info .card-icon {
  color: #1890ff;
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

.main-card {
  border-radius: 8px;
}

.card-header {
  width: 100%;
}

.rules-header,
.records-header {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.text-gray {
  color: #8c8c8c;
}

.text-center {
  text-align: center;
}
</style>
