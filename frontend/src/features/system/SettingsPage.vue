<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture, Refresh, OfficeBuilding, Edit } from '@element-plus/icons-vue'
import api from '../../api/axios'
import { getCompanyInfo, updateCompanyInfo, type CompanyInfo } from '../../api/reports'
import { useI18n } from 'vue-i18n'
import { useBrandStore } from '../../store/brand'

const { t } = useI18n()
const brandStore = useBrandStore()
const currentLogo = ref<string>('')
const fileInputRef = ref<HTMLInputElement | null>(null)
const isLoading = ref(false)

const companyForm = reactive<CompanyInfo>({
  company_name: '',
  company_short_name: '',
  it_department_name: '信息技术部',
  it_contact_name: '',
  it_contact_email: '',
})
const companyLoading = ref(false)

// 品牌设置表单
const brandForm = reactive({
  brand_name_zh: '基石',
  brand_name_en: 'Cornerstone',
  brand_slogan: '看得见，管得住',
  brand_subtitle: 'IT基础设施资源管理平台',
})
const brandLoading = ref(false)
const brandFetchLoading = ref(false)

const fetchBrandSettings = async () => {
  brandFetchLoading.value = true
  try {
    const res = await api.get('/api/v1/settings/brand')
    const data = res.data
    brandForm.brand_name_zh = data.brand_name_zh || '基石'
    brandForm.brand_name_en = data.brand_name_en || 'Cornerstone'
    brandForm.brand_slogan = data.brand_slogan || '看得见，管得住'
    brandForm.brand_subtitle = data.brand_subtitle || 'IT基础设施资源管理平台'
  } catch (error: any) {
    console.error('加载品牌设置失败:', error)
  } finally {
    brandFetchLoading.value = false
  }
}

const saveBrandSettings = async () => {
  brandLoading.value = true
  try {
    await api.put('/api/v1/settings/brand', {
      brand_name_zh: brandForm.brand_name_zh,
      brand_name_en: brandForm.brand_name_en,
      brand_slogan: brandForm.brand_slogan,
      brand_subtitle: brandForm.brand_subtitle,
      brand_logo_url: '',
    })
    // 刷新品牌store
    await brandStore.loadBrand()
    ElMessage.success('品牌设置已更新')
  } catch (error: any) {
    console.error('保存品牌设置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    brandLoading.value = false
  }
}

const resetBrandSettings = async () => {
  try {
    await ElMessageBox.confirm(
      '确定恢复为默认品牌设置吗？系统名称和标语将恢复为「基石 Cornerstone」。',
      '确认恢复默认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    brandLoading.value = true
    try {
      await api.post('/api/v1/settings/brand/reset')
      await fetchBrandSettings()
      await brandStore.loadBrand()
      ElMessage.success('品牌设置已恢复默认')
    } catch (error: any) {
      console.error('恢复默认品牌设置失败:', error)
      ElMessage.error(error.response?.data?.detail || '恢复失败')
    } finally {
      brandLoading.value = false
    }
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  fetchLogo()
  fetchCompanyInfo()
  fetchBrandSettings()
})

const fetchCompanyInfo = async () => {
  try {
    const data = await getCompanyInfo()
    Object.assign(companyForm, data)
  } catch (error: any) {
    console.error('Failed to load company info:', error)
  }
}

const saveCompanyInfo = async () => {
  companyLoading.value = true
  try {
    await updateCompanyInfo({ ...companyForm })
    ElMessage.success('公司信息已更新')
  } catch (error: any) {
    console.error('Failed to save company info:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    companyLoading.value = false
  }
}

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

      await api.post('/settings/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      currentLogo.value = URL.createObjectURL(file)
      ElMessage.success(t('settings.logoUploadSuccess'))
    } catch (error: any) {
      console.error(t('settings.uploadFailed'), error)
      ElMessage.error(error.response?.data?.detail || t('settings.uploadFailed'))
    } finally {
      isLoading.value = false
      input.value = ''
    }
}

const handleLogoRemove = async () => {
  try {
    await api.delete('/settings/logo')
    currentLogo.value = ''
    ElMessage.success(t('settings.logoRemoved'))
  } catch (error: any) {
    console.error(t('settings.deleteFailed'), error)
    ElMessage.error(error.response?.data?.detail || t('settings.deleteFailed'))
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
        <el-icon class="section-icon"><OfficeBuilding /></el-icon>
        <h2 class="section-title">公司信息</h2>
        <p class="section-desc">公司信息将用于运营月报封面、邮件通知落款等场景，请确保信息准确</p>
      </div>

      <div class="company-form">
        <el-form :model="companyForm" label-width="120px" size="large">
          <el-form-item label="公司全称" required>
            <el-input v-model="companyForm.company_name" placeholder="如「简一致远科技有限公司」" />
          </el-form-item>
          <el-form-item label="公司简称" required>
            <el-input v-model="companyForm.company_short_name" placeholder="如「简一致远」" />
          </el-form-item>
          <el-form-item label="IT部门名称">
            <el-input v-model="companyForm.it_department_name" placeholder="信息技术部" />
          </el-form-item>
          <el-form-item label="IT负责人姓名">
            <el-input v-model="companyForm.it_contact_name" placeholder="" />
          </el-form-item>
          <el-form-item label="IT负责人邮箱">
            <el-input v-model="companyForm.it_contact_email" placeholder="" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveCompanyInfo" :loading="companyLoading">保存</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <div class="settings-section">
      <div class="section-header">
        <el-icon class="section-icon"><Edit /></el-icon>
        <h2 class="section-title">品牌设置</h2>
        <p class="section-desc">以下设置控制系统本身的名称和标语，适用于二次部署或品牌定制场景</p>
      </div>

      <div class="brand-form" v-loading="brandFetchLoading">
        <el-form :model="brandForm" label-width="140px" size="large">
          <el-form-item label="系统中文名称" required>
            <el-input v-model="brandForm.brand_name_zh" placeholder="如「基石」" />
          </el-form-item>
          <el-form-item label="系统英文名称" required>
            <el-input v-model="brandForm.brand_name_en" placeholder="如「Cornerstone」" />
          </el-form-item>
          <el-form-item label="系统标语" required>
            <el-input v-model="brandForm.brand_slogan" placeholder="如「看得见，管得住」" />
          </el-form-item>
          <el-form-item label="系统副标题" required>
            <el-input v-model="brandForm.brand_subtitle" placeholder="如「IT基础设施资源管理平台」" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveBrandSettings" :loading="brandLoading">保存</el-button>
            <el-button @click="resetBrandSettings" :loading="brandLoading">恢复默认</el-button>
          </el-form-item>
        </el-form>
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

.company-form {
  max-width: 500px;
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
