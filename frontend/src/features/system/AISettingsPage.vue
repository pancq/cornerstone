<template>
  <div class="ai-settings-page">
    <div class="config-list-container">
      <div class="list-header">
        <span class="list-title">LLM 配置列表</span>
        <el-button type="primary" @click="openAddModal">+ 添加配置</el-button>
      </div>

      <div v-if="configs.length === 0" class="empty-state">
        <el-icon class="empty-icon"><InfoFilled /></el-icon>
        <p>暂无 AI 配置</p>
        <el-button type="primary" @click="openAddModal">添加配置</el-button>
      </div>

      <div v-else class="config-list">
        <div
          v-for="config in configs"
          :key="config.id"
          class="config-card"
          :class="{ active: editingId === config.id }"
        >
          <div class="config-header">
            <div class="config-name">
              <span class="name-text">{{ config.name }}</span>
              <el-tag v-if="config.is_default" type="primary" size="small">默认</el-tag>
            </div>
            <div class="config-actions">
              <el-switch
                v-model="config.enabled"
                @change="toggleEnabled(config)"
              />
              <el-button type="text" @click="openEditModal(config)">编辑</el-button>
              <el-button type="text" @click="deleteConfig(config)" style="color: #ff4d4f">删除</el-button>
            </div>
          </div>
          <div class="config-body">
            <div class="config-row">
              <span class="label">提供商</span>
              <span class="value">{{ getProviderLabel(config.provider) }}</span>
            </div>
            <div class="config-row">
              <span class="label">模型</span>
              <span class="value">{{ config.model }}</span>
            </div>
            <div class="config-row">
              <span class="label">API URL</span>
              <span class="value">{{ config.api_url }}</span>
            </div>
            <div v-if="config.description" class="config-row">
              <span class="label">描述</span>
              <span class="value">{{ config.description }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      :title="editingId ? '编辑 LLM 配置' : '添加 LLM 配置'"
      v-model="modalVisible"
      width="650px"
    >
      <div class="modal-form">
        <div class="form-row">
          <div class="form-group name-group">
            <label class="form-label required">名称</label>
            <el-input
              v-model="form.name"
              placeholder="请输入配置名称"
            />
          </div>
          <div class="form-group switch-group">
            <label class="form-label">启用</label>
            <el-switch v-model="form.enabled" />
          </div>
          <div class="form-group switch-group">
            <label class="form-label">默认</label>
            <el-switch v-model="form.is_default" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group full-width">
            <label class="form-label">描述</label>
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="2"
              placeholder="请输入 LLM 配置的描述信息"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label required">提供商类型</label>
            <el-select
              v-model="form.provider"
              placeholder="请选择提供商类型"
              @change="handleProviderChange"
            >
              <el-option label="OpenAI" value="openai" />
              <el-option label="OpenAI 兼容" value="deepseek" />
              <el-option label="阿里通义千问" value="qwen" />
              <el-option label="智谱AI" value="zhipu" />
              <el-option label="Anthropic Claude" value="claude" />
              <el-option label="自定义 API" value="custom" />
            </el-select>
          </div>
          <div class="form-group">
            <label class="form-label required">模型</label>
            <el-input
              v-model="form.model"
              placeholder="请输入模型名称"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group full-width">
            <label class="form-label required">API URL</label>
            <el-input
              v-model="form.api_url"
              placeholder="请输入 API URL"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group full-width api-key-group">
            <label class="form-label required">API Key</label>
            <div class="input-with-icon">
              <el-input
                v-model="form.api_key"
                :type="showApiKey ? 'text' : 'password'"
                placeholder="请输入 API Key"
              />
              <el-button type="text" @click="showApiKey = !showApiKey" class="eye-btn">
                <el-icon><View /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="closeModal">取消</el-button>
        <el-button type="primary" @click="saveConfig" :loading="loading">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { InfoFilled, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api/axios'

interface AIConfig {
  id: number
  name: string
  description: string
  provider: string
  model: string
  api_url: string
  api_key: string
  enabled: boolean
  is_default: boolean
}

const loading = ref(false)
const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const showApiKey = ref(false)
const configs = ref<AIConfig[]>([])

const form = reactive({
  name: '',
  description: '',
  provider: '',
  model: '',
  api_url: '',
  api_key: '',
  enabled: true,
  is_default: false,
})

const providerOptions: Record<string, string> = {
  openai: 'OpenAI',
  deepseek: 'OpenAI 兼容',
  qwen: '阿里通义千问',
  zhipu: '智谱AI',
  claude: 'Anthropic Claude',
  custom: '自定义 API',
}

const apiUrlDefaults: Record<string, string> = {
  openai: 'https://api.openai.com/v1',
  deepseek: 'https://api.deepseek.com',
  qwen: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  zhipu: 'https://open.bigmodel.cn/api/paas/v4',
  claude: 'https://api.anthropic.com',
  custom: '',
}

const modelDefaults: Record<string, string> = {
  openai: 'gpt-4o-mini',
  deepseek: 'deepseek-v4-flash',
  qwen: 'qwen-plus',
  zhipu: 'glm-4-flash',
  claude: 'claude-3-5-sonnet-20241022',
  custom: '',
}

const getProviderLabel = (provider: string) => providerOptions[provider] || provider

const handleProviderChange = () => {
  form.api_url = apiUrlDefaults[form.provider] || ''
  form.model = modelDefaults[form.provider] || ''
}

const fetchConfigs = async () => {
  try {
    const res = await api.get('/ai/config')
    configs.value = res.data || []
  } catch (error: any) {
    console.error('加载AI配置失败:', error)
    configs.value = []
  }
}

const openAddModal = () => {
  editingId.value = null
  showApiKey.value = false
  form.name = ''
  form.description = ''
  form.provider = ''
  form.model = ''
  form.api_url = ''
  form.api_key = ''
  form.enabled = true
  form.is_default = configs.value.length === 0
  modalVisible.value = true
}

const openEditModal = (config: AIConfig) => {
  editingId.value = config.id
  showApiKey.value = false
  form.name = config.name
  form.description = config.description
  form.provider = config.provider
  form.model = config.model
  form.api_url = config.api_url
  form.api_key = ''
  form.enabled = config.enabled
  form.is_default = config.is_default
  modalVisible.value = true
}

const closeModal = () => {
  modalVisible.value = false
  editingId.value = null
}

const saveConfig = async () => {
  if (!form.name || !form.provider || !form.api_url || !form.api_key || !form.model) {
    ElMessage.warning('请填写完整的配置信息')
    return
  }

  loading.value = true
  try {
    if (editingId.value) {
      await api.put(`/ai/config/${editingId.value}`, {
        name: form.name,
        description: form.description,
        provider: form.provider,
        model: form.model,
        api_url: form.api_url,
        api_key: form.api_key,
        enabled: form.enabled,
        is_default: form.is_default,
      })
    } else {
      await api.post('/ai/config', {
        name: form.name,
        description: form.description,
        provider: form.provider,
        model: form.model,
        api_url: form.api_url,
        api_key: form.api_key,
        enabled: form.enabled,
        is_default: form.is_default,
      })
    }
    ElMessage.success('配置已保存')
    closeModal()
    await fetchConfigs()
  } catch (error: any) {
    console.error('保存配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    loading.value = false
  }
}

const toggleEnabled = async (config: AIConfig) => {
  try {
    await api.put(`/ai/config/${config.id}`, {
      name: config.name,
      description: config.description,
      provider: config.provider,
      model: config.model,
      api_url: config.api_url,
      api_key: '',
      enabled: config.enabled,
      is_default: config.is_default,
    })
    ElMessage.success(config.enabled ? '已启用' : '已禁用')
  } catch (error: any) {
    console.error('更新状态失败:', error)
    config.enabled = !config.enabled
    ElMessage.error('更新失败')
  }
}

const deleteConfig = async (config: AIConfig) => {
  try {
    await ElMessageBox.confirm(`确定要删除配置 "${config.name}" 吗？`, '确认删除', {
      type: 'warning',
    })
    await api.delete(`/ai/config/${config.id}`)
    ElMessage.success('已删除')
    await fetchConfigs()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchConfigs()
})
</script>

<style scoped>
.ai-settings-page {
  background: #f5f5f5;
  min-height: 100vh;
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

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
  color: #8c8c8c;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 0 0 16px 0;
}

.config-list {
  display: grid;
  gap: 16px;
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
  gap: 8px;
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
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.config-row {
  display: flex;
  gap: 8px;
}

.config-row .label {
  font-size: 12px;
  color: #8c8c8c;
  min-width: 60px;
}

.config-row .value {
  font-size: 12px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.form-group.name-group {
  flex: 2;
}

.form-group.switch-group {
  flex: 0.4;
  min-width: 80px;
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

.switch-group .form-label {
  margin-bottom: 4px;
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
</style>
