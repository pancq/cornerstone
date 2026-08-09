<template>
  <div class="reports-page">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p class="page-desc">{{ t('reports.description') }}</p>
    </div>

    <div class="report-toolbar">
      <el-button type="primary" @click="handleGenerate" :loading="generating">
        <el-icon><Document /></el-icon>
        {{ t('reports.generateCurrent') }}
      </el-button>
      <el-button @click="fetchReports" :loading="loading">
        <el-icon><Refresh /></el-icon>
        {{ t('common.refresh') }}
      </el-button>
    </div>

    <el-card class="report-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ t('reports.reportList') }}</span>
          <span class="report-count">{{ reports.length }} {{ t('reports.items') }}</span>
        </div>
      </template>

      <div v-if="reports.length === 0 && !loading" class="empty-state">
        <el-icon class="empty-icon"><Document /></el-icon>
        <p>{{ t('reports.empty') }}</p>
      </div>

      <div v-else class="report-list">
        <div class="report-item" v-for="item in reports" :key="item.id">
          <el-icon class="report-icon"><Document /></el-icon>
          <div class="report-info">
            <span class="report-name">{{ item.year }}{{ t('reports.year') }}{{ item.month }}{{ t('reports.month') }}{{ t('reports.monthlyReport') }}</span>
            <span class="report-meta">{{ formatFileSize(item.file_size) }} · {{ formatTime(item.generated_at) }} · {{ t('reports.generatedBy') }}: {{ item.generated_by }}</span>
          </div>
          <div class="report-actions">
            <el-button type="primary" plain size="small" @click="handleDownload(item)">
              <el-icon><Download /></el-icon>
              {{ t('reports.download') }}
            </el-button>
            <el-button type="danger" plain size="small" @click="handleDelete(item)">
              <el-icon><Delete /></el-icon>
              {{ t('common.delete') }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Refresh, Download, Delete } from '@element-plus/icons-vue'
import {
  listMonthlyReports,
  generateMonthlyReport,
  downloadMonthlyReport,
  deleteMonthlyReport,
  type ReportItem
} from '@/api/reports'

const { t } = useI18n()

const reports = ref<ReportItem[]>([])
const loading = ref(false)
const generating = ref(false)

async function fetchReports() {
  loading.value = true
  try {
    reports.value = await listMonthlyReports()
  } catch (error) {
    console.error('Failed to load reports:', error)
    ElMessage.error(t('reports.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  generating.value = true
  try {
    const now = new Date()
    await generateMonthlyReport(now.getFullYear(), now.getMonth() + 1)
    ElMessage.success(t('reports.generateSuccess'))
    await fetchReports()
  } catch (error: any) {
    console.error('Failed to generate report:', error)
    ElMessage.error(error.response?.data?.detail || t('reports.generateFailed'))
  } finally {
    generating.value = false
  }
}

async function handleDownload(item: ReportItem) {
  try {
    const blob = await downloadMonthlyReport(item.year, item.month)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = item.filename || `report_${item.year}_${item.month}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error: any) {
    console.error('Failed to download report:', error)
    ElMessage.error(error.response?.data?.detail || t('reports.downloadFailed'))
  }
}

async function handleDelete(item: ReportItem) {
  try {
    await ElMessageBox.confirm(
      t('reports.confirmDelete', { name: `${item.year}${t('reports.year')}${item.month}${t('reports.month')}${t('reports.monthlyReport')}` }),
      t('common.confirmDelete'),
      { type: 'warning' }
    )
    await deleteMonthlyReport(item.year, item.month)
    ElMessage.success(t('reports.deleteSuccess'))
    await fetchReports()
  } catch (error: any) {
    if (error === 'cancel') return
    console.error('Failed to delete report:', error)
    ElMessage.error(error.response?.data?.detail || t('reports.deleteFailed'))
  }
}

function formatFileSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

function formatTime(time: string): string {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(fetchReports)
</script>

<style scoped>
.reports-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
}

.page-desc {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.report-toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.report-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-count {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--el-text-color-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.report-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  transition: background-color 0.2s;
}

.report-item:hover {
  background-color: var(--el-fill-color-light);
}

.report-icon {
  font-size: 24px;
  color: var(--el-color-primary);
}

.report-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.report-name {
  font-size: 14px;
  font-weight: 500;
}

.report-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.report-actions {
  display: flex;
  gap: 8px;
}
</style>
