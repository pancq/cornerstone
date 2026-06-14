<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, Refresh } from '@element-plus/icons-vue'
import api from '../../api/axios'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const currentLogo = ref<string>('')
const fileInputRef = ref<HTMLInputElement | null>(null)
const isLoading = ref(false)

onMounted(() => {
  fetchLogo()
})

const fetchLogo = async (retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await api.get('/api/v1/settings/logo')
      const data = response.data
      if (data.value) {
        currentLogo.value = `data:image/png;base64,${data.value}`
      }
      return
    } catch (error: any) {
      const isConnectionError = error.code === 'ECONNREFUSED' ||
        error.message?.includes('ECONNREFUSED') ||
        error.errno === 'ECONNREFUSED'
      if (i < retries - 1 && isConnectionError) {
        await new Promise(resolve => setTimeout(resolve, 1000))
        continue
      }
      console.log(t('settings.fetchLogoFailed'), error)
    }
  }
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) {
    return
  }

  // 验证文件类型
  const isImage = file.type.startsWith('image/')
  const fileName = file.name.toLowerCase()
  const validExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
  const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext))

  if (!isImage && !hasValidExtension) {
    ElMessage.error(t('settings.uploadImageError'))
    input.value = ''
    return
  }

  // 验证文件大小
  const maxSize = 2 * 1024 * 1024 // 2MB
  if (file.size > maxSize) {
    ElMessage.error(t('settings.imageSizeError'))
    input.value = ''
    return
  }

  isLoading.value = true

  try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/v1/settings/logo', {
        method: 'POST',
        body: formData
      })

    if (response.ok) {
      // 显示预览
      currentLogo.value = URL.createObjectURL(file)
      ElMessage.success(t('settings.logoUploadSuccess'))
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || t('settings.uploadFailed'))
    }
  } catch (error) {
    console.error(t('settings.uploadFailed'), error)
    ElMessage.error(t('settings.uploadNetworkError'))
  } finally {
    isLoading.value = false
    input.value = ''
  }
}

const handleLogoRemove = async () => {
  try {
    const response = await fetch('/api/v1/settings/logo', {
      method: 'DELETE'
    })

    if (response.ok) {
      currentLogo.value = ''
      ElMessage.success(t('settings.logoRemoved'))
    } else {
      ElMessage.error(t('settings.deleteFailed'))
    }
  } catch (error) {
    console.error(t('settings.deleteFailed'), error)
    ElMessage.error(t('settings.deleteFailed'))
  }
}
</script>

<template>
  <div class="settings-page">
    <div class="settings-section">
      <div class="section-header">
        <el-icon class="section-icon"><Picture /></el-icon>
        <h2 class="section-title">{{ t('settings.companyLogo') }}</h2>
        <p class="section-desc">{{ t('settings.companyLogoDesc') }}</p>
      </div>

      <div class="logo-upload-area">
        <div class="logo-preview">
          <div v-if="currentLogo" class="logo-image-container">
            <img :src="currentLogo" :alt="t('settings.companyLogo')" class="logo-image" />
          </div>
          <div v-else class="logo-placeholder">
            <div class="logo-placeholder-icon">
              <el-icon><Picture /></el-icon>
            </div>
            <p>{{ t('settings.noLogo') }}</p>
            <p class="hint">{{ t('settings.logoHint') }}</p>
          </div>
        </div>

        <div class="logo-upload">
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            class="upload-input"
            @change="handleFileChange"
          />
          <el-button type="primary" size="large" @click="triggerFileInput" :loading="isLoading">
            <el-icon><Picture /></el-icon>
            {{ t('settings.uploadLogo') }}
          </el-button>

          <div v-if="currentLogo" class="logo-actions">
            <el-button type="default" size="small" @click="handleLogoRemove">
              <el-icon><Refresh /></el-icon>
              {{ t('settings.restoreDefault') }}
            </el-button>
          </div>
          <p class="upload-hint">{{ t('settings.uploadHint') }}</p>
        </div>
      </div>
    </div>

    <div class="settings-section">
      <div class="section-header">
        <h2 class="section-title">{{ t('settings.operationTips') }}</h2>
      </div>
      <ul class="tips-list">
        <li>{{ t('settings.tip1') }}</li>
        <li>{{ t('settings.tip2') }}</li>
        <li>{{ t('settings.tip3') }}</li>
        <li>{{ t('settings.tip4') }}</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-section {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-header {
  margin-bottom: 20px;
}

.section-icon {
  font-size: 20px;
  color: #1890ff;
  margin-right: 8px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 4px;
}

.section-desc {
  font-size: 13px;
  color: #8c8c8c;
}

.logo-upload-area {
  display: flex;
  gap: 40px;
  align-items: flex-start;
}

.logo-preview {
  flex-shrink: 0;
}

.logo-image-container {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px dashed #d9d9d9;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #f5f5f5;
}

.logo-placeholder {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  border: 2px dashed #d9d9d9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #fafafa;
}

.logo-placeholder-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e6f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1890ff;
  font-size: 20px;
}

.logo-placeholder p {
  margin: 0;
  font-size: 13px;
  color: #8c8c8c;
}

.logo-placeholder .hint {
  font-size: 11px;
  color: #bfbfbf;
}

.logo-upload {
  flex: 1;
  padding-top: 20px;
}

.logo-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.upload-input {
  display: none;
}

.upload-hint {
  margin-top: 12px;
  font-size: 12px;
  color: #bfbfbf;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
}

.tips-list li {
  font-size: 13px;
  color: #595959;
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .logo-upload-area {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
