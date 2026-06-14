<template>
  <div class="ai-settings-page">
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        {{ t('aiSettings.backToAlerts') }}
      </button>
      <div class="header-content">
        <h1>{{ t('aiSettings.title') }}</h1>
        <p class="description">{{ t('aiSettings.description') }}</p>
      </div>
    </div>

    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="card-title">
            <el-icon><Setting /></el-icon>
            {{ t('aiSettings.serviceManagement') }}
          </div>
          <el-button type="primary" size="small" @click="showAddModal = true">
            <el-icon><Plus /></el-icon>
            {{ t('aiSettings.addCustomService') }}
          </el-button>
        </div>
      </template>

      <div class="service-list">
        <div
          v-for="(service, index) in services"
          :key="service.name"
          :class="['service-card', { active: currentService.name === service.name }]"
        >
          <div class="service-header" @click="toggleServiceCard(service)">
            <div class="service-icon">
              <el-icon><component :is="getServiceIcon(service.provider)" /></el-icon>
            </div>
            <div class="service-info">
              <h3>{{ getServiceDisplayName(service.provider, service.name) }}</h3>
              <span class="service-model">{{ service.model }}</span>
            </div>
            <div class="service-status">
              <el-switch
                :model-value="services[index].enabled"
                @change="handleToggleService(index)"
                :disabled="services.filter(s => s.enabled).length <= 1 && services[index].enabled"
              />
            </div>
            <div class="service-actions">
              <button 
                v-if="!isDefaultService(service.name)"
                class="delete-btn" 
                @click.stop="handleDeleteService(index)"
              >
                <el-icon><Delete /></el-icon>
              </button>
              <div class="toggle-icon">
                <el-icon :class="{ expanded: currentService.name === service.name }">
                  <Refresh />
                </el-icon>
              </div>
            </div>
          </div>

          <div v-if="currentService.name === service.name" class="service-config">
            <div class="config-section">
              <h4>{{ t('aiSettings.apiConfig') }}</h4>

              <div class="form-item">
                <label>API Base URL</label>
                <el-input
                  v-model="services[index].apiBase"
                  :placeholder="t('aiSettings.apiBasePlaceholder')"
                  class="config-input"
                />
              </div>

              <div v-if="service.provider !== 'local'" class="form-item">
                <label>API Key</label>
                <el-input
                  v-model="services[index].apiKey"
                  type="password"
                  :placeholder="t('aiSettings.apiKeyPlaceholder')"
                  class="config-input"
                  show-password
                />
                <p class="hint">{{ t('aiSettings.apiKeyHint') }}</p>
              </div>

              <div class="form-item">
                <label>{{ t('aiSettings.modelName') }}</label>
                <el-input
                  v-model="services[index].model"
                  :placeholder="t('aiSettings.modelNamePlaceholder')"
                  class="config-input"
                />
                <p class="hint">
                  {{ t('aiSettings.commonModels') }}:
                  <template v-for="model in getAvailableModels(service.provider)" :key="model.value">
                    <el-tag size="small" type="info" style="cursor: pointer; margin-right: 4px; margin-bottom: 4px;" @click="services[index].model = model.value">{{ model.label }}</el-tag>
                  </template>
                  <span style="color: #8c8c8c; font-size: 12px; display: block; margin-top: 4px;">{{ t('aiSettings.clickToFill') }}</span>
                </p>
              </div>
            </div>

            <div class="config-actions">
              <el-button type="primary" @click="testConnection(index)">
                <el-icon><Refresh /></el-icon>
                {{ t('aiSettings.testConnection') }}
              </el-button>
              <el-button @click="saveConfig(index)">
                <el-icon><Check /></el-icon>
                {{ t('aiSettings.saveConfig') }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 测试结果提示 -->
    <div v-if="testResult" :class="['test-result', testResult.type]">
      <el-icon :component="testResult.type === 'success' ? Check : Warning" />
      <span>{{ testResult.message }}</span>
    </div>

    <!-- 添加自定义服务模态框 -->
    <el-dialog :title="t('aiSettings.addCustomService')" v-model="showAddModal">
      <el-form :model="newService" label-width="100px">
        <el-form-item :label="t('aiSettings.serviceName')">
          <el-input v-model="newService.name" :placeholder="t('aiSettings.enterServiceName')" />
        </el-form-item>
        <el-form-item :label="t('aiSettings.provider')">
          <el-select v-model="newService.provider" :placeholder="t('aiSettings.selectProvider')">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option :label="t('aiSettings.qwen')" value="qwen" />
            <el-option :label="t('aiSettings.zhipu')" value="zhipu" />
            <el-option label="Claude" value="claude" />
            <el-option label="OpenAI" value="openai" />
            <el-option :label="t('aiSettings.localModel')" value="local" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('aiSettings.apiAddress')">
          <el-input v-model="newService.apiBase" :placeholder="t('aiSettings.enterApiUrl')" />
        </el-form-item>
        <el-form-item :label="t('aiSettings.modelName')">
          <el-input v-model="newService.model" :placeholder="t('aiSettings.enterModelName')" />
        </el-form-item>
        <el-form-item v-if="newService.provider !== 'local'" :label="t('aiSettings.apiKey')">
          <el-input v-model="newService.apiKey" type="password" :placeholder="t('aiSettings.enterApiKey')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddModal = false">{{ t('aiSettings.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddCustomService">{{ t('aiSettings.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { InfoFilled, Cpu, Refresh, Check, Warning, Setting, Link, Grid, Compass, ArrowLeft, Plus, Delete } from '@element-plus/icons-vue';
import { useAIServiceConfig, type AIServiceConfig } from '../../lib/ai';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAppStore } from '../../store';
import { useAuthStore } from '../../store/auth';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const router = useRouter();
const { services, currentService, setCurrentService, toggleService, addCustomService, removeService } = useAIServiceConfig();
const appStore = useAppStore();
const authStore = useAuthStore();

const showAddModal = ref(false);
const newService = reactive<Omit<AIServiceConfig, 'enabled'>>({
  name: '',
  provider: 'local',
  model: '',
  apiBase: '',
  apiKey: ''
});

const defaultServices = computed(() => ['DeepSeek', t('aiSettings.qwen'), t('aiSettings.zhipu'), 'Claude 3', 'GPT-4', t('aiSettings.localModel')]);

function isDefaultService(name: string): boolean {
  return defaultServices.includes(name);
}

async function handleDeleteService(index: number) {
  const service = services.value[index];
  try {
    await ElMessageBox.confirm(
      t('aiSettings.confirmDeleteService', { name: service.name }),
      t('aiSettings.confirm'),
      {
        confirmButtonText: t('aiSettings.ok'),
        cancelButtonText: t('aiSettings.cancel'),
        type: 'warning'
      }
    );
    removeService(index);
    ElMessage.success(t('aiSettings.deleteSuccess'));
  } catch {
    ElMessage.info(t('aiSettings.deleteCancelled'));
  }
}

function handleAddCustomService() {
  if (!newService.name || !newService.apiBase || !newService.model) {
    ElMessage.warning(t('aiSettings.fillAllFields'));
    return;
  }
  
  addCustomService({ ...newService });
  
  // 重置表单
  newService.name = '';
  newService.provider = 'local';
  newService.model = '';
  newService.apiBase = '';
  newService.apiKey = '';
  
  showAddModal.value = false;
  ElMessage.success(t('aiSettings.addSuccess'));
}

function goBack() {
  router.push('/alerts');
}

function toggleServiceCard(service: typeof services.value[0]) {
  // 如果点击的是当前已选中的服务，则收起配置面板
  if (currentService.value.name === service.name) {
    // 选择一个空的服务对象来模拟收起状态
    setCurrentService({
      name: '',
      provider: 'local',
      model: '',
      enabled: false
    });
  } else {
    setCurrentService(service);
  }
}

interface TestResult {
  type: 'success' | 'error';
  message: string;
}

const testResult = ref<TestResult | null>(null);

function handleToggleService(index: number) {
  const service = services.value[index];
  const oldEnabled = service.enabled;
  toggleService(index);

  // 添加操作日志
  appStore.addAuditLog({
    user: authStore.user?.username || 'system',
    action: oldEnabled ? t('aiSettings.disableService') : t('aiSettings.enableService'),
    resource: t('aiSettings.aiServiceConfig'),
    detail: `${oldEnabled ? t('aiSettings.disable') : t('aiSettings.enable')} ${t('aiSettings.service')}: ${service.name} (${service.model})`,
    ipAddress: null,
    createdAt: new Date().toISOString(),
    success: 'true'
  });
}

function getServiceIcon(provider: string) {
  const iconsMap: Record<string, typeof Setting> = {
    deepseek: Compass,
    qwen: Link,
    zhipu: Grid,
    claude: InfoFilled,
    openai: Setting,
    local: Cpu
  };
  return iconsMap[provider] || Setting;
}

function getServiceDisplayName(provider: string, name: string): string {
  const providerNames: Record<string, string> = {
    deepseek: t('aiSettings.providers.deepseek'),
    qwen: t('aiSettings.providers.qwen'),
    zhipu: t('aiSettings.providers.zhipu'),
    claude: t('aiSettings.providers.claude'),
    openai: t('aiSettings.providers.openai'),
    local: t('aiSettings.providers.local')
  };
  return providerNames[provider] || name;
}

function getAvailableModels(provider: string) {
  const models: Record<string, { label: string; value: string }[]> = {
    deepseek: [
      { label: 'DeepSeek V3', value: 'deepseek-v3' },
      { label: 'DeepSeek R1', value: 'deepseek-reasoner' },
      { label: 'DeepSeek Chat', value: 'deepseek-chat' }
    ],
    qwen: [
      { label: t('aiSettings.models.qwenPlus') + t('aiSettings.recommended'), value: 'qwen-plus' },
      { label: t('aiSettings.models.qwenTurbo'), value: 'qwen-turbo' },
      { label: t('aiSettings.models.qwenMax'), value: 'qwen-max' },
      { label: t('aiSettings.models.qwen25') + ' 72B', value: 'qwen2.5-72b-instruct' },
      { label: t('aiSettings.models.qwen25') + ' 32B', value: 'qwen2.5-32b-instruct' }
    ],
    zhipu: [
      { label: t('aiSettings.models.glm4Plus') + t('aiSettings.recommended'), value: 'glm-4-plus' },
      { label: t('aiSettings.models.glm4Flash'), value: 'glm-4-flash' },
      { label: 'GLM-4', value: 'glm-4' },
      { label: 'GLM-4V', value: 'glm-4v' }
    ],
    claude: [
      { label: t('aiSettings.models.claude35Sonnet') + t('aiSettings.latest'), value: 'claude-3-5-sonnet-20241022' },
      { label: t('aiSettings.models.claude35Haiku'), value: 'claude-3-5-haiku-20241022' },
      { label: t('aiSettings.models.claude3Opus'), value: 'claude-3-opus-20240229' },
      { label: t('aiSettings.models.claude3Sonnet'), value: 'claude-3-sonnet-20240229' }
    ],
    openai: [
      { label: t('aiSettings.models.gpt4o') + t('aiSettings.latest'), value: 'gpt-4o' },
      { label: t('aiSettings.models.gpt4oMini'), value: 'gpt-4o-mini' },
      { label: t('aiSettings.models.gpt4Turbo'), value: 'gpt-4-turbo' },
      { label: t('aiSettings.models.gpt4'), value: 'gpt-4' }
    ],
    local: [
      { label: t('aiSettings.models.qwen25') + ' 7B' + t('aiSettings.recommended'), value: 'qwen2.5-7b-instruct' },
      { label: t('aiSettings.models.qwen25') + ' 14B', value: 'qwen2.5-14b-instruct' },
      { label: t('aiSettings.models.qwen25') + ' 32B', value: 'qwen2.5-32b-instruct' },
      { label: t('aiSettings.models.qwen25') + ' 72B', value: 'qwen2.5-72b-instruct' },
      { label: t('aiSettings.models.llama31') + ' 8B', value: 'llama-3.1-8b-instruct' },
      { label: t('aiSettings.models.llama31') + ' 70B', value: 'llama-3.1-70b-instruct' }
    ]
  };
  return models[provider] || [];
}

async function testConnection(index: number) {
  const service = services.value[index];
  if (!service.enabled) {
    ElMessage.warning(t('aiSettings.enableServiceFirst'));
    return;
  }

  if (service.provider !== 'local' && !service.apiKey) {
    ElMessage.warning(t('aiSettings.fillApiKeyFirst'));
    return;
  }

  testResult.value = { type: 'success', message: t('aiSettings.connectionTestSuccess') };
  setTimeout(() => {
    testResult.value = null;
  }, 3000);
}

function saveConfig(index: number) {
  const service = services.value[index];

  localStorage.setItem('ai_service_config', JSON.stringify(services.value));
  localStorage.setItem('ai_current_service', service.name);

  // 添加操作日志
  appStore.addAuditLog({
    user: authStore.user?.username || 'system',
    action: t('aiSettings.modifyAIConfig'),
    resource: t('aiSettings.aiServiceConfig'),
    detail: `${t('aiSettings.modifyServiceConfig')}: ${service.name} - ${t('aiSettings.model')}: ${service.model}, ${t('aiSettings.apiAddress')}: ${service.apiBase}`,
    ipAddress: null,
    createdAt: new Date().toISOString(),
    success: 'true'
  });

  ElMessage.success(t('aiSettings.configSaved'));
}
</script>

<style scoped>
.ai-settings-page {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  color: #262626;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.back-btn:hover {
  background: #f5f5f5;
  border-color: #1890ff;
  color: #1890ff;
}

.header-content {
  flex: 1;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 8px 0;
}

.page-header .description {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

.settings-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.card-title .el-icon {
  color: #1890ff;
}

.service-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.service-card {
  background: #fff;
  border: 2px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.service-card:hover {
  border-color: #1890ff;
}

.service-card.active {
  border-color: #1890ff;
  background: #f0f5ff;
}

.service-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  cursor: pointer;
}

.service-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1890ff, #69c0ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.service-info {
  flex: 1;
}

.service-info h3 {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 4px 0;
}

.service-model {
  font-size: 13px;
  color: #8c8c8c;
}

.service-status {
  margin-right: 16px;
}

.toggle-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8c8c8c;
  transition: transform 0.3s ease;
}

.toggle-icon .expanded {
  transform: rotate(180deg);
}

.service-config {
  padding: 20px;
  background: #fff;
  border-top: 1px solid #e8e8e8;
}

.config-section {
  margin-bottom: 20px;
}

.config-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 16px 0;
}

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #595959;
  margin-bottom: 8px;
}

.config-input {
  width: 100%;
  max-width: 500px;
}

.form-item .hint {
  font-size: 12px;
  color: #bfbfbf;
  margin: 8px 0 0 0;
}

.config-actions {
  display: flex;
  gap: 12px;
}

.test-result {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

.test-result.success {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #52c41a;
}

.test-result.error {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  color: #ff4d4f;
}

.test-result .el-icon {
  width: 20px;
  height: 20px;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .service-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .service-status {
    margin-left: 0;
    align-self: flex-end;
  }
}
</style>
