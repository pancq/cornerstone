<template>
  <div class="ai-settings-page">
    <div class="page-header">
      <h1>AI 设置</h1>
      <p class="description">配置 AI 模型以启用智能分析、趋势预测等功能</p>
    </div>

    <div class="config-form-container">
      <div class="config-form">
        <div class="form-row">
          <div class="form-group name-group">
            <label class="form-label required">名称</label>
            <el-input
              v-model="aiForm.name"
              placeholder="请输入配置名称"
            />
          </div>
          <div class="form-group switch-group">
            <label class="form-label">启用</label>
            <el-switch v-model="aiForm.enabled" />
          </div>
          <div class="form-group switch-group">
            <label class="form-label">默认</label>
            <el-switch v-model="aiForm.is_default" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group full-width">
            <label class="form-label">描述</label>
            <el-input
              v-model="aiForm.description"
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
              v-model="aiForm.provider"
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
              v-model="aiForm.model"
              placeholder="请输入模型名称"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group full-width">
            <label class="form-label required">API URL</label>
            <el-input
              v-model="aiForm.api_url"
              placeholder="请输入 API URL"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group full-width api-key-group">
            <label class="form-label required">API Key</label>
            <div class="input-with-icon">
              <el-input
                v-model="aiForm.api_key"
                :type="showApiKey ? 'text' : 'password'"
                placeholder="请输入 API Key"
              />
              <el-button type="text" @click="showApiKey = !showApiKey" class="eye-btn">
                <el-icon><View /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <div class="advanced-settings" @click="toggleAdvanced">
          <div class="advanced-header">
            <el-icon><ArrowDown v-if="!advancedExpanded" /><ArrowUp v-else /></el-icon>
            <span>高级设置</span>
          </div>
        </div>

        <div v-show="advancedExpanded" class="advanced-content">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">最大 Token</label>
              <el-input
                v-model.number="aiForm.max_tokens"
                type="number"
                placeholder="2000"
              />
            </div>
            <div class="form-group">
              <label class="form-label">温度</label>
              <el-input
                v-model.number="aiForm.temperature"
                type="number"
                :step="0.1"
                placeholder="0.7"
              />
            </div>
          </div>
        </div>

        <div class="form-actions">
          <el-button type="primary" @click="saveConfig" :loading="loading">保存配置</el-button>
          <el-button @click="resetConfig">重置</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ArrowDown, ArrowUp, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../../api/axios'

const loading = ref(false)
const showApiKey = ref(false)
const advancedExpanded = ref(false)

const aiForm = reactive({
  name: '',
  description: '',
  provider: '',
  model: '',
  api_url: '',
  api_key: '',
  enabled: false,
  is_default: false,
  max_tokens: 2000,
  temperature: 0.7,
})

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

const handleProviderChange = () => {
  aiForm.api_url = apiUrlDefaults[aiForm.provider] || ''
  aiForm.model = modelDefaults[aiForm.provider] || ''
}

const toggleAdvanced = () => {
  advancedExpanded.value = !advancedExpanded.value
}

const fetchAIConfig = async () => {
  try {
    const res = await api.get('/ai/config')
    const data = res.data
    aiForm.name = data.description || ''
    aiForm.description = ''
    aiForm.provider = data.provider || ''
    aiForm.model = data.model || ''
    aiForm.api_url = data.api_url || ''
    aiForm.api_key = ''
    aiForm.enabled = true
    aiForm.is_default = true
  } catch (error: any) {
    console.error('加载AI配置失败:', error)
  }
}

const saveConfig = async () => {
  if (!aiForm.name || !aiForm.provider || !aiForm.api_url || !aiForm.api_key || !aiForm.model) {
    ElMessage.warning('请填写完整的配置信息')
    return
  }

  loading.value = true
  try {
    await api.put('/ai/config', {
      provider: aiForm.provider,
      model: aiForm.model,
      api_url: aiForm.api_url,
      api_key: aiForm.api_key,
      description: aiForm.name,
    })
    ElMessage.success('AI配置已保存')
  } catch (error: any) {
    console.error('保存AI配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    loading.value = false
  }
}

const resetConfig = () => {
  aiForm.name = ''
  aiForm.description = ''
  aiForm.provider = ''
  aiForm.model = ''
  aiForm.api_url = ''
  aiForm.api_key = ''
  aiForm.enabled = false
  aiForm.is_default = false
  aiForm.max_tokens = 2000
  aiForm.temperature = 0.7
}

onMounted(() => {
  fetchAIConfig()
})
</script>

<style scoped>
.ai-settings-page {
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

.config-form-container {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.config-form {
  max-width: 800px;
}

.form-row {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
}

.form-group {
  flex: 1;
  min-width: 200px;
}

.form-group.full-width {
  flex: 100;
}

.form-group.name-group {
  flex: 2;
}

.form-group.switch-group {
  flex: 0.5;
  min-width: 100px;
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

.advanced-settings {
  margin-bottom: 16px;
  cursor: pointer;
}

.advanced-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #595959;
  padding: 8px 0;
}

.advanced-content {
  padding-left: 24px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
