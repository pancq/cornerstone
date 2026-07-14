<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Bell, Message, Postcard as MailIcon, ArrowRight as SendIcon, Check, Close } from '@element-plus/icons-vue'
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
const testingChannel = ref<string | null>(null)
const expandedChannels = ref<Record<string, boolean>>({
  dingtalk: true,
  wechat: true,
  feishu: true,
  email: true
})

const channels = ref([
  { key: 'dingtalk', name: '钉钉', icon: Message, color: '#268AF7' },
  { key: 'wechat', name: '企业微信', icon: Message, color: '#07C160' },
  { key: 'feishu', name: '飞书', icon: Message, color: '#007DFF' },
  { key: 'email', name: '邮件通知', icon: MailIcon, color: '#722ED1' }
])

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

const toggleChannel = (key: string) => {
  expandedChannels.value[key] = !expandedChannels.value[key]
}

const isChannelConfigured = (key: string) => {
  if (key === 'dingtalk') return !!form.value.dingtalk_webhook_url
  if (key === 'wechat') return !!form.value.wechat_webhook_url
  if (key === 'feishu') return !!form.value.feishu_webhook_url
  if (key === 'email') return !!form.value.smtp_host && !!form.value.smtp_username && !!form.value.smtp_password
  return false
}
</script>

<template>
  <div class="notification-settings-page">
    <div class="page-header">
      <div class="header-icon">
        <Bell />
      </div>
      <div class="header-info">
        <h1>通知管理</h1>
        <p>配置通知渠道，接收系统告警和运维通知</p>
      </div>
    </div>

    <div class="channels-grid">
      <div
        v-for="channel in channels"
        :key="channel.key"
        class="channel-card"
      >
        <div class="card-header">
          <div class="channel-info">
            <div class="channel-icon" :style="{ background: channel.color }">
              <component :is="channel.icon" />
            </div>
            <div>
              <h3>{{ channel.name }}</h3>
              <p class="channel-status">
                <span :class="['status-badge', isChannelConfigured(channel.key) ? 'configured' : 'not-configured']">
                  <Check v-if="isChannelConfigured(channel.key)" />
                  <Close v-else />
                  {{ isChannelConfigured(channel.key) ? '已配置' : '未配置' }}
                </span>
              </p>
            </div>
          </div>
          <el-button
            type="text"
            class="expand-btn"
            @click="toggleChannel(channel.key)"
          >
            <el-icon>
              <SendIcon :style="{ transform: expandedChannels[channel.key] ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }" />
            </el-icon>
          </el-button>
        </div>

        <div v-show="expandedChannels[channel.key]" class="card-body">
          <div v-if="channel.key === 'dingtalk'" class="form-content">
            <div class="form-group">
              <label>Webhook URL</label>
              <el-input
                v-model="form.dingtalk_webhook_url"
                type="textarea"
                :rows="3"
                placeholder="请输入钉钉机器人 Webhook 地址"
              />
              <p class="form-hint">在钉钉群中添加自定义机器人，复制 Webhook 地址</p>
            </div>
            <div class="form-actions">
              <el-button
                type="primary"
                :loading="testingChannel === 'dingtalk'"
                @click="handleTest('dingtalk')"
              >
                测试发送
              </el-button>
            </div>
          </div>

          <div v-if="channel.key === 'wechat'" class="form-content">
            <div class="form-group">
              <label>Webhook URL</label>
              <el-input
                v-model="form.wechat_webhook_url"
                type="textarea"
                :rows="3"
                placeholder="请输入企业微信机器人 Webhook 地址"
              />
              <p class="form-hint">在企业微信群中添加机器人，复制 Webhook 地址</p>
            </div>
            <div class="form-actions">
              <el-button
                type="primary"
                :loading="testingChannel === 'wechat'"
                @click="handleTest('wechat')"
              >
                测试发送
              </el-button>
            </div>
          </div>

          <div v-if="channel.key === 'feishu'" class="form-content">
            <div class="form-group">
              <label>Webhook URL</label>
              <el-input
                v-model="form.feishu_webhook_url"
                type="textarea"
                :rows="3"
                placeholder="请输入飞书机器人 Webhook 地址"
              />
              <p class="form-hint">在飞书群中添加机器人，复制 Webhook 地址</p>
            </div>
            <div class="form-actions">
              <el-button
                type="primary"
                :loading="testingChannel === 'feishu'"
                @click="handleTest('feishu')"
              >
                测试发送
              </el-button>
            </div>
          </div>

          <div v-if="channel.key === 'email'" class="form-content">
            <div class="form-row">
              <div class="form-group">
                <label>SMTP 服务器</label>
                <el-input v-model="form.smtp_host" placeholder="smtp.example.com" />
              </div>
              <div class="form-group">
                <label>SMTP 端口</label>
                <el-input v-model.number="form.smtp_port" type="number" placeholder="587" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>用户名</label>
                <el-input v-model="form.smtp_username" placeholder="邮箱账号" />
              </div>
              <div class="form-group">
                <label>发件人邮箱</label>
                <el-input v-model="form.smtp_from_email" placeholder="sender@example.com" />
              </div>
            </div>
            <div class="form-group">
              <label>密码/授权码</label>
              <el-input v-model="form.smtp_password" type="password" placeholder="请输入密码或授权码" />
              <p class="form-hint">建议使用邮箱授权码而非密码，例如 Gmail 使用 App Password</p>
            </div>
            <div class="form-actions">
              <el-button
                type="primary"
                :loading="testingChannel === 'email'"
                @click="handleTest('email')"
              >
                测试发送
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="page-footer">
      <el-button @click="resetForm">重置</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="isLoading">保存配置</el-button>
    </div>
  </div>
</template>

<style scoped>
.notification-settings-page {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.header-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  font-size: 28px;
  color: #fff;
}

.header-info h1 {
  font-size: 22px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 6px 0;
}

.header-info p {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.channel-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
}

.channel-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
}

.channel-info {
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

.channel-info h3 {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px 0;
}

.channel-status {
  font-size: 12px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.status-badge.configured {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.not-configured {
  background: #fff2f0;
  color: #ff4d4f;
}

.expand-btn {
  color: #8c8c8c;
  font-size: 14px;
}

.card-body {
  padding: 20px;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #434343;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin: 0;
  padding-left: 4px;
}

.form-actions {
  display: flex;
  gap: 10px;
  padding-top: 8px;
}

.page-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
</style>
