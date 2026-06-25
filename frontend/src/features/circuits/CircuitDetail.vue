<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const route = useRoute()
const router = useRouter()

const activeTab = ref('basic')

const tabs = [
  { name: 'basic', label: '基础信息' },
  { name: 'incidents', label: '故障记录' },
  { name: 'changes', label: '变更记录' }
]

const circuitId = computed(() => route.params.id as string)

function goBack() {
  router.push('/circuits')
}

function goToChanges() {
  router.push(`/circuits/${circuitId.value}/changes`)
}
</script>

<template>
  <div class="circuit-detail">
    <div class="detail-header">
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon> 返回列表
      </button>
    </div>

    <el-tabs v-model="activeTab" class="detail-tabs">
      <el-tab-pane label="基础信息" name="basic">
        <div class="tab-content">
          <el-card class="detail-card" shadow="never">
            <template #header>
              <div class="card-title">
                <el-icon><Connection /></el-icon> 基础信息
              </div>
            </template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="专线名称">
                <strong>{{ $store.circuits.find(c => c.id === circuitId)?.name || '-' }}</strong>
              </el-descriptions-item>
              <el-descriptions-item label="电路编号">
                {{ $store.circuits.find(c => c.id === circuitId)?.circuitNo || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="运营商">
                {{ $store.circuits.find(c => c.id === circuitId)?.provider || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="线路类型">
                {{ $store.circuits.find(c => c.id === circuitId)?.type || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="接入站点">
                <el-icon><Location /></el-icon> {{ $store.sites.find(s => s.id === $store.circuits.find(c => c.id === circuitId)?.siteId)?.name || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="带宽">
                <strong>{{ $store.circuits.find(c => c.id === circuitId)?.bandwidth || '-' }} Mbps</strong>
              </el-descriptions-item>
              <el-descriptions-item label="公网 IP">
                <code>{{ $store.circuits.find(c => c.id === circuitId)?.publicIp || '-' }}</code>
              </el-descriptions-item>
              <el-descriptions-item label="客服电话">
                {{ $store.circuits.find(c => c.id === circuitId)?.supportPhone || '-' }}
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
                {{ $store.circuits.find(c => c.id === circuitId)?.contractStart || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="合同结束日期">
                {{ $store.circuits.find(c => c.id === circuitId)?.contractEnd || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="月租费用">
                <strong class="cost-value">¥{{ ($store.circuits.find(c => c.id === circuitId)?.monthlyCost || 0).toLocaleString() }}</strong>
              </el-descriptions-item>
              <el-descriptions-item label="备注">
                {{ $store.circuits.find(c => c.id === circuitId)?.note || '-' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="detail-card" shadow="never" style="margin-top: 20px">
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
        </div>
      </el-tab-pane>

      <el-tab-pane label="故障记录" name="incidents">
        <div class="tab-content">
          <CircuitIncidentsTab />
        </div>
      </el-tab-pane>

      <el-tab-pane label="变更记录" name="changes">
        <div class="tab-content">
          <CircuitChanges :circuit-id="circuitId" />
        </div>
      </el-tab-pane>
    </el-tabs>
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

.detail-tabs {
  width: 100%;
}

.tab-content {
  padding-top: 20px;
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