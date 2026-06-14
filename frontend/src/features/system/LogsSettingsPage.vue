<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock, Lock, Document } from '@element-plus/icons-vue'
import api from '../../api/axios'

const { t } = useI18n()
const loading = ref(false)

// 日志保留策略
const retentionSettings = ref({
  log_retention_days: 90,
  login_log_retention_days: 180,
  log_auto_cleanup: true
})

// 登录安全设置
const securitySettings = ref({
  login_max_attempts: 5,
  session_timeout_minutes: 120,
  allow_concurrent_login: true,
  alert_on_foreign_login: false
})

// 记录级别设置
const levelSettings = ref({
  log_query_operations: false,
  log_export_operations: true,
  log_login_operations: true,
  require_confirm_dangerous: true
})

// Session超时选项
const sessionTimeoutOptions = computed(() => [
  { value: 30, label: `30 ${t('system.logs.minutes')}` },
  { value: 60, label: `1 ${t('system.logs.hour')}` },
  { value: 120, label: `2 ${t('system.logs.hours')}` },
  { value: 240, label: `4 ${t('system.logs.hours')}` },
  { value: 480, label: `8 ${t('system.logs.hours')}` },
  { value: -1, label: t('system.logs.neverTimeout') }
])

// 加载设置
const loadSettings = async () => {
  loading.value = true
  try {
    const response = await api.get('/settings/logs')
    if (response.data) {
      // 日志保留策略
      if (response.data.log_retention_days) retentionSettings.value.log_retention_days = response.data.log_retention_days
      if (response.data.login_log_retention_days) retentionSettings.value.login_log_retention_days = response.data.login_log_retention_days
      if (response.data.log_auto_cleanup !== undefined) retentionSettings.value.log_auto_cleanup = response.data.log_auto_cleanup
      
      // 登录安全
      if (response.data.login_max_attempts) securitySettings.value.login_max_attempts = response.data.login_max_attempts
      if (response.data.session_timeout_minutes) securitySettings.value.session_timeout_minutes = response.data.session_timeout_minutes
      if (response.data.allow_concurrent_login !== undefined) securitySettings.value.allow_concurrent_login = response.data.allow_concurrent_login
      if (response.data.alert_on_foreign_login !== undefined) securitySettings.value.alert_on_foreign_login = response.data.alert_on_foreign_login
      
      // 记录级别
      if (response.data.log_query_operations !== undefined) levelSettings.value.log_query_operations = response.data.log_query_operations
      if (response.data.log_export_operations !== undefined) levelSettings.value.log_export_operations = response.data.log_export_operations
      if (response.data.log_login_operations !== undefined) levelSettings.value.log_login_operations = response.data.log_login_operations
      if (response.data.require_confirm_dangerous !== undefined) levelSettings.value.require_confirm_dangerous = response.data.require_confirm_dangerous
    }
  } catch (error) {
    console.error('Failed to load log settings:', error)
  } finally {
    loading.value = false
  }
}

// 保存日志保留策略
const saveRetentionSettings = async () => {
  try {
    await api.put('/settings/logs', retentionSettings.value)
    ElMessage.success(t('common.success'))
  } catch (error) {
    ElMessage.error(t('common.error'))
  }
}

// 保存登录安全设置
const saveSecuritySettings = async () => {
  try {
    await api.put('/settings/logs', securitySettings.value)
    ElMessage.success(t('common.success'))
  } catch (error) {
    ElMessage.error(t('common.error'))
  }
}

// 保存记录级别设置
const saveLevelSettings = async () => {
  try {
    const data = {
      log_query_operations: levelSettings.value.log_query_operations,
      log_export_operations: levelSettings.value.log_export_operations,
      require_confirm_dangerous: levelSettings.value.require_confirm_dangerous
    }
    await api.put('/settings/logs', data)
    ElMessage.success(t('common.success'))
  } catch (error) {
    ElMessage.error(t('common.error'))
  }
}

// 手动清理日志
const handleCleanup = async () => {
  const days = retentionSettings.value.log_retention_days
  try {
    await ElMessageBox.confirm(
      t('system.logs.cleanupConfirm', { days }),
      t('system.logs.confirmCleanup'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    
    const response = await api.post('/settings/logs/cleanup')
    ElMessage.success(t('system.logs.cleanupSuccess', { count: response.data.deleted_count }))
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(t('common.error'))
    }
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<template>
  <div class="logs-settings-page">
    <!-- 日志保留策略 -->
    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon"><Clock /></el-icon>
          <span class="header-title">{{ t('system.logs.retentionPolicy') }}</span>
        </div>
      </template>
      
      <el-form label-position="top" class="settings-form">
        <el-form-item :label="t('system.logs.auditRetentionDays')">
          <el-input-number 
            v-model="retentionSettings.log_retention_days" 
            :min="30" 
            :max="3650" 
            :step="10"
          />
          <span class="unit">{{ t('system.logs.days') }}</span>
          <div class="form-desc">{{ t('system.logs.auditRetentionDesc') }}</div>
        </el-form-item>
        
        <el-form-item :label="t('system.logs.loginRetentionDays')">
          <el-input-number 
            v-model="retentionSettings.login_log_retention_days" 
            :min="30" 
            :max="3650" 
            :step="10"
          />
          <span class="unit">{{ t('system.logs.days') }}</span>
          <div class="form-desc">{{ t('system.logs.loginRetentionDesc') }}</div>
        </el-form-item>
        
        <el-form-item :label="t('system.logs.autoCleanup')">
          <el-switch v-model="retentionSettings.log_auto_cleanup" />
          <div class="form-desc">{{ t('system.logs.autoCleanupDesc') }}</div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="warning" @click="handleCleanup">
            {{ t('system.logs.cleanupNow') }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="card-footer">
        <el-button type="primary" @click="saveRetentionSettings">
          {{ t('common.save') }}
        </el-button>
      </div>
    </el-card>
    
    <!-- 登录安全设置 -->
    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon"><Lock /></el-icon>
          <span class="header-title">{{ t('system.logs.loginSecurity') }}</span>
        </div>
      </template>
      
      <el-form label-position="top" class="settings-form">
        <el-form-item :label="t('system.logs.loginLockout')">
          <el-input-number 
            v-model="securitySettings.login_max_attempts" 
            :min="3" 
            :max="10" 
            :step="1"
          />
          <span class="unit">{{ t('system.logs.attempts') }}</span>
          <div class="form-desc">{{ t('system.logs.loginLockoutDesc') }}</div>
        </el-form-item>
        
        <el-form-item :label="t('system.logs.sessionTimeout')">
          <el-select v-model="securitySettings.session_timeout_minutes" style="width: 200px">
            <el-option 
              v-for="opt in sessionTimeoutOptions" 
              :key="opt.value" 
              :label="opt.label" 
              :value="opt.value"
            />
          </el-select>
          <div class="form-desc">{{ t('system.logs.sessionTimeoutDesc') }}</div>
        </el-form-item>
        
        <el-form-item :label="t('system.logs.concurrentLogin')">
          <el-switch v-model="securitySettings.allow_concurrent_login" />
          <div class="form-desc">{{ t('system.logs.concurrentLoginDesc') }}</div>
        </el-form-item>
        
        <el-form-item :label="t('system.logs.foreignLoginAlert')">
          <el-switch v-model="securitySettings.alert_on_foreign_login" />
          <div class="form-desc">{{ t('system.logs.foreignLoginAlertDesc') }}</div>
        </el-form-item>
      </el-form>
      
      <div class="card-footer">
        <el-button type="primary" @click="saveSecuritySettings">
          {{ t('common.save') }}
        </el-button>
      </div>
    </el-card>
    
    <!-- 操作日志记录级别 -->
    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon"><Document /></el-icon>
          <span class="header-title">{{ t('system.logs.logLevel') }}</span>
        </div>
      </template>
      
      <el-form label-position="top" class="settings-form">
        <el-form-item :label="t('system.logs.logQuery')">
          <el-switch v-model="levelSettings.log_query_operations" />
          <div class="form-desc">{{ t('system.logs.logQueryDesc') }}</div>
        </el-form-item>
        
        <el-form-item :label="t('system.logs.logExport')">
          <el-switch v-model="levelSettings.log_export_operations" />
          <div class="form-desc">{{ t('system.logs.logExportDesc') }}</div>
        </el-form-item>
        
        <el-form-item :label="t('system.logs.logLogin')">
          <el-switch 
            v-model="levelSettings.log_login_operations" 
            disabled
          />
          <div class="form-desc">{{ t('system.logs.logLoginDesc') }}</div>
          <el-tooltip :content="t('system.logs.loginLogDisabled')" placement="top">
            <el-icon class="disabled-tip"><Lock /></el-icon>
          </el-tooltip>
        </el-form-item>
        
        <el-form-item :label="t('system.logs.dangerousConfirm')">
          <el-switch v-model="levelSettings.require_confirm_dangerous" />
          <div class="form-desc">{{ t('system.logs.dangerousConfirmDesc') }}</div>
        </el-form-item>
      </el-form>
      
      <div class="card-footer">
        <el-button type="primary" @click="saveLevelSettings">
          {{ t('common.save') }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.logs-settings-page {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
  border: 1px solid #e4e7ed;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 20px;
  color: #409eff;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.settings-form {
  max-width: 600px;
}

.unit {
  margin-left: 8px;
  color: #606266;
}

.form-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.card-footer {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.disabled-tip {
  margin-left: 8px;
  color: #909399;
  cursor: help;
}
</style>