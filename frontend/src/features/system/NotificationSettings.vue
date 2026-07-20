<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Message, Postcard, Edit } from '@element-plus/icons-vue'
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
const editingChannel = ref<string | null>(null)
const modalVisible = ref(false)
const showPassword = ref(false)

const channels = ref([
  { 
    key: 'dingtalk', 
    name: '钉钉', 
    icon: Message, 
    color: '#268AF7',
    enabled: false
  },
  { 
    key: 'wechat', 
    name: '企业微信', 
    icon: Message, 
    color: '#07C160',
    enabled: false
  },
  { 
    key: 'feishu', 
    name: '飞书', 
    icon: Message, 
    color: '#007DFF',
    enabled: false
  },
  { 
    key: 'email', 
    name: '邮件通知', 
    icon: Postcard, 
    color: '#722ED1',
    enabled: false
  }
])

const editingForm = reactive({
  key: '',
  name: '',
  webhook_url: '',
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_from_email: '',
})

const isConfigured = (channelKey: string) => {
  switch (channelKey) {
    case 'dingtalk':
      return !!form.value.dingtalk_webhook_url
    case 'wechat':
      return !!form.value.wechat_webhook_url
    case 'feishu':
      return !!form.value.feishu_webhook_url
    case 'email':
      return !!form.value.smtp_host && !!form.value.smtp_username && !!form.value.smtp_password
    default:
      return false
  }
}

const getCurrentValue = () => {
  const key = editingForm.key
  switch (key) {
    case 'dingtalk':
      editingForm.webhook_url = form.value.dingtalk_webhook_url || ''
      break
    case 'wechat':
      editingForm.webhook_url = form.value.wechat_webhook_url || ''
      break
    case 'feishu':
      editingForm.webhook_url = form.value.feishu_webhook_url || ''
      break
    case 'email':
      editingForm.smtp_host = form.value.smtp_host || ''
      editingForm.smtp_port = form.value.smtp_port || 587
      editingForm.smtp_username = form.value.smtp_username || ''
      editingForm.smtp_password = form.value.smtp_password || ''
      editingForm.smtp_from_email = form.value.smtp_from_email || ''
      break
  }
}

const openEditModal = (channel: any) => {
  editingChannel.value = channel.key
  editingForm.key = channel.key
  editingForm.name = channel.name
  getCurrentValue()
  showPassword.value = false
  modalVisible.value = true
}

const closeModal = () => {
  modalVisible.value = false
  editingChannel.value = null
}

const saveEdit = async () => {
  const key = editingForm.key
  
  switch (key) {
    case 'dingtalk':
      form.value.dingtalk_webhook_url = editingForm.webhook_url
      break
    case 'wechat':
      form.value.wechat_webhook_url = editingForm.webhook_url
      break
    case 'feishu':
      form.value.feishu_webhook_url = editingForm.webhook_url
      break
    case 'email':
      form.value.smtp_host = editingForm.smtp_host
      form.value.smtp_port = editingForm.smtp_port
      form.value.smtp_username = editingForm.smtp_username
      form.value.smtp_password = editingForm.smtp_password
      form.value.smtp_from_email = editingForm.smtp_from_email
      break
  }

  await handleSubmit()
  closeModal()
}

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
  try {
    const result = await testNotification(channel)
    ElMessage.success(result.message)
  } catch (error: any) {
    console.error('Test notification failed:', error)
    ElMessage.error(error.response?.data?.detail || t('system.notification.testFailed'))
  }
}

const getWebhookValue = (key: string) => {
  switch (key) {
    case 'dingtalk': return form.value.dingtalk_webhook_url
    case 'wechat': return form.value.wechat_webhook_url
    case 'feishu': return form.value.feishu_webhook_url
    default: return ''
  }
}

const getDisplayValue = (channelKey: string) => {
  switch (channelKey) {
    case 'dingtalk':
    case 'wechat':
    case 'feishu': {
      const val = getWebhookValue(channelKey)
      return val ? (val.length > 40 ? val.substring(0, 40) + '...' : val) : '未配置'
    }
    case 'email': {
      if (!form.value.smtp_host) return '未配置'
      return `${form.value.smtp_host}:${form.value.smtp_port}`
    }
    default:
      return '未配置'
  }
}
</script>

<template>
  <div class="notification-settings-page">
    <div class="page-header">
      <h1>通知管理</h1>
      <p class="description">配置通知渠道，接收系统告警和运维通知</p>
    </div>

    <div class="config-list-container">
      <div class="list-header">
        <span class="list-title">通知渠道配置</span>
      </div>

      <div class="config-list">
        <div
          v-for="channel in channels"
          :key="channel.key"
          class="config-card"
          :class="{ active: editingChannel === channel.key }"
        >
          <div class="config-header">
            <div class="config-name">
              <div class="channel-icon" :style="{ background: channel.color }">
                <component :is="channel.icon" />
              </div>
              <span class="name-text">{{ channel.name }}</span>
              <el-tag v-if="isConfigured(channel.key)" type="success" size="small">已配置</el-tag>
              <el-tag v-else type="danger" size="small">未配置</el-tag>
            </div>
            <div class="config-actions">
              <el-button type="text" @click="openEditModal(channel)">
                <el-icon><Edit /></el-icon>
                配置
              </el-button>
            </div>
          </div>
          <div class="config-body">
            <div class="config-row">
              <span class="label">Webhook 地址</span>
              <span class="value" v-if="channel.key !== 'email'">{{ getDisplayValue(channel.key) }}</span>
              <span class="value" v-else>{{ getDisplayValue(channel.key) }}</span>
            </div>
            <div v-if="channel.key === 'email' && form.smtp_username" class="config-row">
              <span class="label">用户名</span>
              <span class="value">{{ form.smtp_username }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="form-actions">
        <el-button @click="resetForm">重置</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="isLoading">保存配置</el-button>
      </div>
    </div>

    <el-dialog
      :title="`配置 ${editingForm.name}`"
      v-model="modalVisible"
      width="600px"
    >
      <div class="modal-form" v-if="editingForm.key !== 'email'">
        <div class="form-row">
          <div class="form-group full-width">
            <label class="form-label required">Webhook URL</label>
            <el-input
              v-model="editingForm.webhook_url"
              type="textarea"
              :rows="4"
              placeholder="请输入机器人 Webhook 地址"
            />
            <p class="form-hint">在对应平台的群聊中添加机器人，复制 Webhook 地址</p>
          </div>
        </div>
        <div class="form-actions">
          <el-button type="primary" @click="handleTest(editingForm.key as any)" :loading="isLoading">
            测试发送
          </el-button>
        </div>
      </div>

      <div class="modal-form" v-if="editingForm.key === 'email'">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label required">SMTP 服务器</label>
            <el-input
              v-model="editingForm.smtp_host"
              placeholder="smtp.example.com"
            />
          </div>
          <div class="form-group">
            <label class="form-label">SMTP 端口</label>
            <el-input
              v-model.number="editingForm.smtp_port"
              type="number"
              placeholder="587"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <el-input
              v-model="editingForm.smtp_username"
              placeholder="邮箱账号"
            />
          </div>
          <div class="form-group">
            <label class="form-label">发件人邮箱</label>
            <el-input
              v-model="editingForm.smtp_from_email"
              placeholder="sender@example.com"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group full-width api-key-group">
            <label class="form-label required">密码 / 授权码</label>
            <div class="input-with-icon">
              <el-input
                v-model="editingForm.smtp_password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码或授权码"
              />
              <el-button type="text" @click="showPassword = !showPassword" class="eye-btn">
                <el-icon><Postcard /></el-icon>
              </el-button>
            </div>
            <p class="form-hint">建议使用邮箱授权码而非密码，例如 Gmail 使用 App Password</p>
          </div>
        </div>
        <div class="form-actions">
          <el-button type="primary" @click="handleTest('email')" :loading="isLoading">
            测试发送
          </el-button>
        </div>
      </div>

      <template #footer>
        <el-button @click="closeModal">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="isLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts">
</script>

<style scoped>
.notification-settings-page {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 8px 0;
}

.page-header .description {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

.config-list-container {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.list-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.config-list {
  display: grid;
  gap: 16px;
  margin-bottom: 24px;
}

.config-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.config-card:hover {
  border-color: #1890ff;
}

.config-card.active {
  border-color: #1890ff;
  background: #f0f5ff;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.config-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.channel-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 18px;
  color: #fff;
}

.name-text {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.config-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-body {
  display: grid;
  gap: 8px;
}

.config-row {
  display: flex;
  gap: 8px;
}

.config-row .label {
  font-size: 12px;
  color: #8c8c8c;
  min-width: 80px;
}

.config-row .value {
  font-size: 12px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.modal-form {
  padding: 8px 0;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  flex: 1;
  min-width: 150px;
}

.form-group.full-width {
  flex: 100;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-label.required::before {
  content: '*';
  color: #ff4d4f;
  margin-right: 4px;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin: 6px 0 0 0;
  padding-left: 4px;
}

.api-key-group {
  position: relative;
}

.input-with-icon {
  display: flex;
  align-items: center;
}

.input-with-icon .eye-btn {
  margin-left: -40px;
  z-index: 10;
  padding: 0 10px;
}

.modal-form .form-actions {
  border-top: none;
  padding-top: 0;
  justify-content: flex-start;
}
</style>
