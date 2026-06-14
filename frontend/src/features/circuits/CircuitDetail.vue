<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '../../store'
import { storeToRefs } from 'pinia'

const route = useRoute()
const router = useRouter()
const store = useAppStore()
const { circuits, sites } = storeToRefs(store)

const circuitId = computed(() => route.params.id as string)
const circuit = computed(() => circuits.value.find(c => c.id === circuitId.value))
const site = computed(() => sites.value.find(s => s.id === circuit.value?.siteId))

if (!circuit.value) {
  router.push('/circuits')
}

function getStatusType(status: string) {
  if (status === '正常') return 'success'
  if (status === '故障') return 'danger'
  if (status === '已停用') return 'info'
  return 'warning'
}

function goBack() {
  router.push('/circuits')
}

function goToChanges() {
  router.push(`/circuits/${circuitId.value}/changes?name=${encodeURIComponent(circuit.value?.name || '')}`)
}
</script>

<template>
  <div class="circuit-detail">
    <div class="detail-header">
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon> 返回列表
      </button>
      <div class="detail-title">
        <h1>{{ circuit?.name }}</h1>
        <el-tag v-if="circuit" :type="getStatusType(circuit.status)" effect="dark">{{ circuit.status }}</el-tag>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="detail-card" shadow="never">
          <template #header>
            <div class="card-title">
              <el-icon><Connection /></el-icon> 基础信息
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="专线名称">
              <strong>{{ circuit?.name }}</strong>
            </el-descriptions-item>
            <el-descriptions-item label="电路编号">
              {{ circuit?.circuitNo }}
            </el-descriptions-item>
            <el-descriptions-item label="运营商">
              {{ circuit?.provider }}
            </el-descriptions-item>
            <el-descriptions-item label="线路类型">
              {{ circuit?.type }}
            </el-descriptions-item>
            <el-descriptions-item label="接入站点">
              <el-icon><Location /></el-icon> {{ site?.name }}
            </el-descriptions-item>
            <el-descriptions-item label="带宽">
              <strong>{{ circuit?.bandwidth }} Mbps</strong>
            </el-descriptions-item>
            <el-descriptions-item label="公网 IP">
              <code>{{ circuit?.publicIp }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="客服电话">
              {{ circuit?.supportPhone }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="detail-card" shadow="never" style="margin-top: 20px">
          <template #header>
            <div class="card-title">
              <el-icon><Document /></el-icon> 合同信息
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="合同开始日期">
              {{ circuit?.contractStart }}
            </el-descriptions-item>
            <el-descriptions-item label="合同结束日期">
              {{ circuit?.contractEnd }}
            </el-descriptions-item>
            <el-descriptions-item label="月租费用">
              <strong class="cost-value">¥{{ circuit?.monthlyCost?.toLocaleString() }}</strong>
            </el-descriptions-item>
            <el-descriptions-item label="备注">
              {{ circuit?.note }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="detail-card" shadow="never">
          <template #header>
            <div class="card-title">
              <el-icon><Operation /></el-icon> 操作
            </div>
          </template>
          <div class="actions-list">
            <el-button type="primary" style="width: 100%; margin-bottom: 8px">
              <el-icon><Edit /></el-icon> 编辑专线
            </el-button>
            <el-button style="width: 100%; margin-bottom: 8px" @click="goToChanges">
              <el-icon><Document /></el-icon> 变更记录
            </el-button>
            <el-button style="width: 100%">
              <el-icon><Upload /></el-icon> 上传合同
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.circuit-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: #1890ff;
  cursor: pointer;
  padding: 8px 0;
}

.back-btn:hover {
  text-decoration: underline;
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-title h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #262626;
}

.detail-card {
  border-radius: 8px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #262626;
}

.actions-list {
  display: flex;
  flex-direction: column;
}

.cost-value {
  font-size: 18px;
  color: #262626;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}
</style>