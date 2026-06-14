<template>
  <div class="device-links-list">
    <div class="table-header">
      <h3>设备连接关系</h3>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          新增连接
        </el-button>
        <el-button type="success" :icon="Search" @click="runLldpDiscovery" :loading="discovering">
          发现邻居
        </el-button>
        <el-button :icon="Refresh" @click="loadDeviceLinks" :loading="loading">
          刷新
        </el-button>
      </div>
    </div>

    <el-table :data="deviceLinks" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="源设备">
        <template #default="{ row }">
          <span>{{ getDeviceName(row.source_device_id) }}</span>
          <span v-if="row.source_interface" class="interface-label">{{ row.source_interface }}</span>
        </template>
      </el-table-column>
      <el-table-column label="目标设备">
        <template #default="{ row }">
          <span>{{ getDeviceName(row.target_device_id) }}</span>
          <span v-if="row.target_interface" class="interface-label">{{ row.target_interface }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="link_type" label="连接类型" width="100">
        <template #default="{ row }">
          <el-tag :type="getLinkTypeTagType(row.link_type)" size="small">
            {{ getLinkTypeText(row.link_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="confidence" label="置信度" width="80">
        <template #default="{ row }">
          <span :class="getConfidenceClass(row.confidence)">{{ row.confidence }}%</span>
        </template>
      </el-table-column>
      <el-table-column prop="discovered_at" label="发现时间" width="180" />
      <el-table-column prop="note" label="备注" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="showEditDialog(row)">
            编辑
          </el-button>
          <el-button type="danger" link size="small" @click="confirmDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑连接对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '创建设备连接' : '编辑设备连接'"
      width="600px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="源设备" prop="source_device_id">
          <el-select v-model="form.source_device_id" placeholder="请选择源设备" filterable style="width: 100%">
            <el-option
              v-for="device in devices"
              :key="device.id"
              :label="device.name"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="源接口" prop="source_interface">
          <el-input v-model="form.source_interface" placeholder="如：GigabitEthernet0/1" />
        </el-form-item>
        <el-form-item label="目标设备" prop="target_device_id">
          <el-select v-model="form.target_device_id" placeholder="请选择目标设备" filterable style="width: 100%">
            <el-option
              v-for="device in devices"
              :key="device.id"
              :label="device.name"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标接口" prop="target_interface">
          <el-input v-model="form.target_interface" placeholder="如：GigabitEthernet0/2" />
        </el-form-item>
        <el-form-item label="连接类型" prop="link_type">
          <el-select v-model="form.link_type" placeholder="请选择连接类型" style="width: 100%">
            <el-option label="手动配置" value="manual" />
            <el-option label="LLDP 发现" value="lldp" />
            <el-option label="CDP 发现" value="cdp" />
            <el-option label="推断连接" value="inferred" />
          </el-select>
        </el-form-item>
        <el-form-item label="置信度" prop="confidence">
          <el-slider v-model="form.confidence" :min="0" :max="100" :step="5" show-input />
        </el-form-item>
        <el-form-item label="备注" prop="note">
          <el-input v-model="form.note" type="textarea" :rows="3" placeholder="请输入备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  getDeviceLinks,
  createDeviceLink,
  updateDeviceLink,
  deleteDeviceLink,
  discoverLldpNeighbors,
  type DeviceLink,
  type DeviceLinkCreate,
  type DeviceLinkUpdate
} from '@/api/topology'
import { getDevices, type DeviceResponse } from '@/api/devices'

const loading = ref(false)
const submitting = ref(false)
const discovering = ref(false)
const deviceLinks = ref<DeviceLink[]>([])
const devices = ref<DeviceResponse[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingLinkId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = ref<DeviceLinkCreate & { note?: string }>({
  source_device_id: 0,
  source_interface: undefined,
  target_device_id: 0,
  target_interface: undefined,
  link_type: 'manual',
  confidence: 100,
  note: undefined
})

const rules: FormRules = {
  source_device_id: [{ required: true, message: '请选择源设备', trigger: 'change' }],
  target_device_id: [
    { required: true, message: '请选择目标设备', trigger: 'change' },
    {
      validator: (_rule, value, callback) => {
        if (value === form.value.source_device_id) {
          callback(new Error('目标设备不能与源设备相同'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

const getLinkTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    manual: '手动配置',
    lldp: 'LLDP 发现',
    cdp: 'CDP 发现',
    inferred: '推断连接'
  }
  return typeMap[type] || type
}

const getLinkTypeTagType = (type: string) => {
  const tagTypeMap: Record<string, 'success' | 'primary' | 'warning' | 'info'> = {
    manual: 'info',
    lldp: 'success',
    cdp: 'success',
    inferred: 'warning'
  }
  return tagTypeMap[type] || 'info'
}

const getConfidenceClass = (confidence: number | null) => {
  if (!confidence) return 'confidence-low'
  if (confidence >= 80) return 'confidence-high'
  if (confidence >= 50) return 'confidence-medium'
  return 'confidence-low'
}

const getDeviceName = (deviceId: number) => {
  const device = devices.value.find(d => d.id === deviceId)
  return device ? device.name : `设备${deviceId}`
}

const loadDeviceLinks = async () => {
  loading.value = true
  try {
    deviceLinks.value = await getDeviceLinks()
  } catch (error) {
    console.error('Failed to load device links:', error)
    ElMessage.error('加载设备连接失败')
  } finally {
    loading.value = false
  }
}

const loadDevices = async () => {
  try {
    const data = await getDevices()
    devices.value = data
  } catch (error) {
    console.error('Failed to load devices:', error)
  }
}

const showCreateDialog = () => {
  dialogMode.value = 'create'
  dialogVisible.value = true
}

const showEditDialog = (link: DeviceLink) => {
  dialogMode.value = 'edit'
  editingLinkId.value = link.id
  form.value = {
    source_device_id: link.source_device_id,
    source_interface: link.source_interface,
    target_device_id: link.target_device_id,
    target_interface: link.target_interface,
    link_type: link.link_type,
    confidence: link.confidence || 100,
    note: link.note || undefined
  }
  dialogVisible.value = true
}

const resetForm = () => {
  formRef.value?.resetFields()
  editingLinkId.value = null
  form.value = {
    source_device_id: 0,
    source_interface: undefined,
    target_device_id: 0,
    target_interface: undefined,
    link_type: 'manual',
    confidence: 100,
    note: undefined
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (dialogMode.value === 'create') {
        await createDeviceLink(form.value as DeviceLinkCreate)
        ElMessage.success('创建成功')
      } else {
        if (!editingLinkId.value) return
        const updateData: DeviceLinkUpdate = { ...form.value }
        await updateDeviceLink(editingLinkId.value, updateData)
        ElMessage.success('更新成功')
      }
      dialogVisible.value = false
      await loadDeviceLinks()
    } catch (error) {
      console.error('Failed to submit device link:', error)
      ElMessage.error(dialogMode.value === 'create' ? '创建失败' : '更新失败')
    } finally {
      submitting.value = false
    }
  })
}

const confirmDelete = async (link: DeviceLink) => {
  try {
    await ElMessageBox.confirm(`确定要删除设备连接吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteDeviceLink(link.id)
    ElMessage.success('删除成功')
    await loadDeviceLinks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete device link:', error)
      ElMessage.error('删除失败')
    }
  }
}

const runLldpDiscovery = async () => {
  discovering.value = true
  try {
    await discoverLldpNeighbors()
    ElMessage.success('LLDP发现完成')
    await loadDeviceLinks()
  } catch (error) {
    console.error('LLDP discovery failed:', error)
    ElMessage.error('发现失败')
  } finally {
    discovering.value = false
  }
}

onMounted(() => {
  loadDeviceLinks()
  loadDevices()
})
</script>

<style scoped>
.device-links-list {
  padding: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.interface-label {
  margin-left: 8px;
  padding: 2px 6px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
}

.confidence-high {
  color: #67c23a;
  font-weight: bold;
}

.confidence-medium {
  color: #e6a23c;
  font-weight: bold;
}

.confidence-low {
  color: #f56c6c;
  font-weight: bold;
}
</style>
