<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Bell, Message, Postcard, Promotion } from '@element-plus/icons-vue'
import { getNotificationSettings, updateNotificationSettings, testNotification } from '../../api/settings'
import type { NotificationSettings } from '../../api/settings'

const { t } = useI18n()

const form = ref<NotificationSettings>({
  dingtalk_webhook_url: '',
  wechat_webhook_url: '',
  feishu_webhook_url: '',
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_from_email: ''
})

const isLoading = ref(false)
const activeTab = ref<'webhook' | 'email'>('webhook')
const testingChannel = ref<string | null>(null)

onMounted(() => {
  loadSettings()
})

const loadSettings = async () => {
  try {
    const settings = await getNotificationSettings()
    form.value = { ...settings }
  } catch (error) {
    console.error('Load notification settings failed:', error)
    ElMessage.error(t('system.notification.loadFailed'))
  }
}

const handleSubmit = async () => {
  isLoading.value = true
  
  try {
    await updateNotificationSettings(form.value)
    ElMessage.success(t('system.notification.updateSuccess'))
  } catch (error: any) {
    console.error('Update notification settings failed:', error)
    ElMessage.error(error.response?.data?.detail || t('system.notification.updateFailed'))
  } finally {
    isLoading.value = false
  }
}

const resetForm = () => {
  loadSettings()
}

const handleTest = async (channel: 'dingtalk' | 'wechat' | 'feishu' | 'email') => {
  testingChannel.value = channel
  
  try {
    const result = await testNotification(channel)
    ElMessage.success(result.message)
  } catch (error: any) {
    console.error('Test notification failed:', error)
    ElMessage.error(error.response?.data?.detail || t('system.notification.testFailed'))
  } finally {
    testingChannel.value = null
  }
}
</script>

<template>
  <div class="notification-settings-page">
    <div class="settings-section">
      <div class="section-header">
        <el-icon class="section-icon"><Bell /></el-icon>
        <div class="section-info">
          <h2 class="section-title">{{ t('system.notification.channelConfig') }}</h2>
          <p class="section-desc">{{ t('system.notification.channelDesc') }}</p>
        </div>
      </div>
      
      <el-tabs v-model="activeTab" class="notification-tabs">
        <el-tab-pane :label="t('system.notification.imBot')" name="webhook">
          <div class="form-section">
            <div class="form-group">
              <label class="form-label">
                <el-icon class="label-icon"><Message /></el-icon>
                {{ t('system.notification.dingtalkWebhook') }}
              </label>
              <el-input
                v-model="form.dingtalk_webhook_url"
                type="textarea"
                :rows="3"
                :placeholder="t('system.notification.dingtalkPlaceholder')"
                class="form-textarea"
              />
              <p class="form-hint">{{ t('system.notification.dingtalkHint') }}</p>
              <el-button 
                type="primary" 
                size="small" 
                plain
                :loading="testingChannel === 'dingtalk'"
                @click="handleTest('dingtalk')"
                style="margin-top: 8px;"
              >
                {{ t('system.notification.testDingtalk') }}
              </el-button>
            </div>
            
            <div class="form-group">
              <label class="form-label">
                <el-icon class="label-icon"><Message /></el-icon>
                {{ t('system.notification.wechatWebhook') }}
              </label>
              <el-input
                v-model="form.wechat_webhook_url"
                type="textarea"
                :rows="3"
                :placeholder="t('system.notification.wechatPlaceholder')"
                class="form-textarea"
              />
              <p class="form-hint">{{ t('system.notification.wechatHint') }}</p>
              <el-button 
                type="primary" 
                size="small" 
                plain
                :loading="testingChannel === 'wechat'"
                @click="handleTest('wechat')"
                style="margin-top: 8px;"
              >
                {{ t('system.notification.testWechat') }}
              </el-button>
            </div>
            
            <div class="form-group">
              <label class="form-label">
                <el-icon class="label-icon"><Message /></el-icon>
                {{ t('system.notification.feishuWebhook') }}
              </label>
              <el-input
                v-model="form.feishu_webhook_url"
                type="textarea"
                :rows="3"
                :placeholder="t('system.notification.feishuPlaceholder')"
                class="form-textarea"
              />
              <p class="form-hint">{{ t('system.notification.feishuHint') }}</p>
              <el-button 
                type="primary" 
                size="small" 
                plain
                :loading="testingChannel === 'feishu'"
                @click="handleTest('feishu')"
                style="margin-top: 8px;"
              >
                {{ t('system.notification.testFeishu') }}
              </el-button>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane :label="t('system.notification.emailNotification')" name="email">
          <div class="form-section">
            <div class="form-row">
              <div class="form-group flex-1">
                <label class="form-label">
                  <el-icon class="label-icon"><Postcard /></el-icon>
                  {{ t('system.notification.smtpHost') }}
                </label>
                <el-input
                  v-model="form.smtp_host"
                  :placeholder="t('system.notification.smtpHostPlaceholder')"
                />
              </div>
              
              <div class="form-group">
                <label class="form-label">{{ t('system.notification.smtpPort') }}</label>
                <el-input
                  v-model.number="form.smtp_port"
                  type="number"
                  placeholder="587"
                  style="width: 120px;"
                />
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group flex-1">
                <label class="form-label">{{ t('system.notification.smtpUsername') }}</label>
                <el-input
                  v-model="form.smtp_username"
                  :placeholder="t('system.notification.smtpUserPlaceholder')"
                />
              </div>
              
              <div class="form-group flex-1">
                <label class="form-label">{{ t('system.notification.smtpFromEmail') }}</label>
                <el-input
                  v-model="form.smtp_from_email"
                  :placeholder="t('system.notification.smtpFromPlaceholder')"
                />
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">{{ t('system.notification.smtpPassword') }}</label>
              <el-input
                v-model="form.smtp_password"
                type="password"
                :placeholder="t('system.notification.smtpPwdPlaceholder')"
              />
              <p class="form-hint">{{ t('system.notification.smtpPwdHint') }}</p>
            </div>
            
            <div class="form-group">
              <el-button 
                type="primary" 
                size="small" 
                plain
                :loading="testingChannel === 'email'"
                @click="handleTest('email')"
              >
                {{ t('system.notification.testEmail') }}
              </el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      
      <div class="form-actions">
        <el-button type="default" @click="resetForm">
          {{ t('common.reset') }}
        </el-button>
        <el-button type="primary" @click="handleSubmit" :loading="isLoading">
          {{ t('common.save') }}
        </el-button>
      </div>
    </div>
    
    <div class="settings-section">
      <div class="section-header">
        <h2 class="section-title">{{ t('system.notification.usageGuide') }}</h2>
      </div>
      <div class="help-content">
        <h3>{{ t('system.notification.guideImBot') }}</h3>
        <ol>
          <li>{{ t('system.notification.guideStep1') }}</li>
          <li>{{ t('system.notification.guideStep2') }}</li>
          <li>{{ t('system.notification.guideStep3') }}</li>
          <li>{{ t('system.notification.guideStep4') }}</li>
          <li>{{ t('system.notification.guideStep5') }}</li>
        </ol>
        
        <h3>{{ t('system.notification.guideEmail') }}</h3>
        <ol>
          <li>{{ t('system.notification.guideEmail1') }}</li>
          <li>{{ t('system.notification.guideEmail2') }}</li>
          <li>{{ t('system.notification.guideEmail3') }}</li>
          <li>{{ t('system.notification.guideEmail4') }}</li>
        </ol>
        
        <h3>{{ t('system.notification.guideTest') }}</h3>
        <p>{{ t('system.notification.guideTestDesc') }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notification-settings-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 20px;
}

.settings-section {
  background: #fff;
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #f5f5f5;
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.section-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  font-size: 22px;
  color: #fff;
  flex-shrink: 0;
}

.section-info {
  flex: 1;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 6px;
}

.section-desc {
  font-size: 14px;
  color: #8c8c8c;
  line-height: 1.5;
}

.notification-tabs {
  margin-bottom: 24px;
  --el-tabs-header-text-color: #8c8c8c;
  --el-tabs-active-text-color: #1890ff;
  --el-tabs-header-border-color: #f0f0f0;
  --el-tabs-active-bar-color: #1890ff;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-group.flex-1 {
  flex: 1;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #434343;
  display: flex;
  align-items: center;
  gap: 8px;
}

.label-icon {
  color: #1890ff;
  font-size: 15px;
}

.form-textarea {
  resize: vertical;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.form-textarea:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.form-hint {
  font-size: 13px;
  color: #999;
  margin: 0;
  padding-left: 4px;
  line-height: 1.5;
}

.form-actions {
  display: flex;
  gap: 14px;
  justify-content: flex-end;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.help-content {
  font-size: 14px;
  color: #595959;
  line-height: 1.7;
}

.help-content h3 {
  font-size: 15px;
  font-weight: 600;
  color: #262626;
  margin: 20px 0 14px;
  padding-left: 12px;
  border-left: 3px solid #1890ff;
}

.help-content h3:first-child {
  margin-top: 0;
}

.help-content ol {
  margin: 0;
  padding-left: 24px;
}

.help-content li {
  margin-bottom: 10px;
  position: relative;
}

.help-content li::marker {
  color: #1890ff;
  font-weight: 600;
}

.help-content p {
  margin: 10px 0;
  padding-left: 4px;
}

.help-content code {
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
  color: #595959;
}
</style>