<template>
  <div class="device-topology">
    <div class="topology-header">
      <el-input
        v-model="searchKeyword"
        :placeholder="t('topology.searchPlaceholder')"
        class="search-input"
        clearable
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div class="toolbar">
        <el-select
          v-model="selectedSiteId"
          :placeholder="t('topology.selectSite')"
          class="site-select"
          size="small"
          clearable
          @change="onSiteChange"
        >
          <el-option :label="t('topology.allSites')" :value="null" />
          <el-option
            v-for="site in sites"
            :key="site.id"
            :label="site.name"
            :value="site.id"
          />
        </el-select>
        <el-switch
          v-model="showIsolatedDevices"
          :active-text="t('topology.showIsolated')"
          :inactive-text="t('topology.hideIsolated')"
          inline-prompt
          size="small"
        />
        <el-button :icon="Refresh" :title="t('topology.forceLayout')" @click="runForceLayout" :loading="isLayoutRunning" class="toolbar-btn" />
        <el-button :icon="Grid" :title="t('topology.gridLayout')" @click="resetLayout" class="toolbar-btn" />
        <el-button :icon="ZoomIn" :title="t('topology.zoomIn')" @click="zoomIn" class="toolbar-btn" />
        <el-button :icon="ZoomOut" :title="t('topology.zoomOut')" @click="zoomOut" class="toolbar-btn" />
        <el-button :icon="FullScreen" :title="t('topology.fullscreen')" @click="toggleFullscreen" class="toolbar-btn" />
      </div>
    </div>

    <div class="topology-canvas" ref="canvasWrapper">
      <svg
        :width="canvasWidth"
        :height="canvasHeight"
        class="topology-svg"
        @mousedown="startPan"
        @mousemove="onMouseMove"
        @mouseup="endMouseUp"
        @mouseleave="endMouseUp"
        @wheel="onWheel"
      >
        <defs>
          <marker
            id="arrow-device"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill="#666" />
          </marker>
          <marker
            id="arrow-red-device"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill="#F56C6C" />
          </marker>
        </defs>

        <g :transform="`translate(${panX}, ${panY}) scale(${scale})`">
          <!-- 渲染设备连接边 -->
          <g v-for="edge in filteredEdges" :key="'edge-' + edge.id">
            <line
              :x1="getNodePosition(edge.source).x"
              :y1="getNodePosition(edge.source).y"
              :x2="getNodePosition(edge.target).x"
              :y2="getNodePosition(edge.target).y"
              class="topology-edge"
              :class="[edge.link_type]"
            />
          </g>

          <!-- 渲染设备节点 -->
          <g
            v-for="node in filteredNodes"
            :key="'node-' + node.id"
            :transform="`translate(${getNodePosition(node.id).x}, ${getNodePosition(node.id).y})`"
            class="topology-node device-node"
            :class="{ 'node-selected': selectedNodeId === node.id }"
            @mousedown.stop="startDrag(node.id, $event)"
            @mouseover="showNodeTooltip(node as DeviceNode, $event)"
            @mouseout="hideTooltip"
          >
            <rect
              :width="nodeWidth"
              :height="nodeHeight"
              :x="-nodeWidth / 2"
              :y="-nodeHeight / 2"
              rx="6"
              class="node-box"
              :class="getNodeClass(node as DeviceNode)"
            />
            <!-- 状态指示灯 -->
            <circle
              :cx="nodeWidth / 2 - 8"
              :cy="-nodeHeight / 2 + 8"
              r="6"
              class="status-dot"
              :fill="getStatusColor(node.status)"
            />
            <text
              :x="0"
              :y="-8"
              text-anchor="middle"
              class="node-name"
            >
              {{ node.name }}
            </text>
            <text
              :x="0"
              :y="8"
              text-anchor="middle"
              class="node-city"
            >
              {{ (node as DeviceNode).ip_address }}
            </text>
            <!-- 在线设备显示延迟和丢包率 -->
            <template v-if="node.status !== 'offline' && node.status !== 'critical'">
              <text
                :x="-55"
                :y="22"
                class="node-monitor"
              >
                <tspan class="monitor-label">{{ t('topology.latency') }}:</tspan>
                <tspan class="monitor-value" :class="getMonitorClass((node as DeviceNode).latency, 'latency')">
                  {{ ((node as DeviceNode).latency ?? 0).toFixed(1) + 'ms' }}
                </tspan>
              </text>
              <text
                :x="5"
                :y="22"
                class="node-monitor"
              >
                <tspan class="monitor-label">{{ t('topology.packetLoss') }}:</tspan>
                <tspan class="monitor-value" :class="getMonitorClass((node as DeviceNode).packet_loss, 'packet_loss')">
                  {{ ((node as DeviceNode).packet_loss ?? 0).toFixed(0) + '%' }}
                </tspan>
              </text>
            </template>
          </g>
        </g>
      </svg>

      <div class="tooltip" v-if="tooltipVisible" :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }">
        <div class="tooltip-title">
          {{ tooltipData.name }}
        </div>
        <div class="tooltip-content">
          <div><span class="tooltip-label">{{ t('topology.deviceType') }}：</span><span>{{ getDeviceTypeText((tooltipData as DeviceNode).type) }}</span></div>
          <div><span class="tooltip-label">{{ t('topology.vendor') }}：</span><span>{{ (tooltipData as DeviceNode).vendor }}</span></div>
          <div><span class="tooltip-label">{{ t('topology.managementIp') }}：</span><span>{{ (tooltipData as DeviceNode).ip_address || t('topology.notConfigured') }}</span></div>
          <div><span class="tooltip-label">{{ t('topology.status') }}：</span><span :class="getStatusClass((tooltipData as DeviceNode).status)">{{ getStatusText((tooltipData as DeviceNode).status) }}</span></div>
          <div v-if="(tooltipData as DeviceNode).latency != null"><span class="tooltip-label">{{ t('topology.latency') }}：</span><span>{{ ((tooltipData as DeviceNode).latency ?? 0).toFixed(2) }}ms</span></div>
          <div v-if="(tooltipData as DeviceNode).packet_loss != null"><span class="tooltip-label">{{ t('topology.packetLoss') }}：</span><span>{{ ((tooltipData as DeviceNode).packet_loss ?? 0).toFixed(1) }}%</span></div>
          <div><span class="tooltip-label">{{ t('topology.site') }}：</span><span>{{ (tooltipData as DeviceNode).site_name || t('topology.notAssigned') }}</span></div>
        </div>
      </div>
    </div>

    <div class="topology-legend">
      <div class="legend-item">
        <span class="status-dot" style="background: #67C23A"></span> {{ t('topology.statusNormal') }}
      </div>
      <div class="legend-item">
        <span class="status-dot" style="background: #E6A23C"></span> {{ t('topology.statusWarning') }}
      </div>
      <div class="legend-item">
        <span class="status-dot" style="background: #909399"></span> {{ t('topology.statusOffline') }}
      </div>
      <div class="legend-item">
        <span class="status-dot" style="background: #F56C6C"></span> {{ t('topology.statusCritical') }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Search, Refresh, Grid, ZoomIn, ZoomOut, FullScreen } from '@element-plus/icons-vue'
import { getDeviceGraph, type DeviceNode, type DeviceEdge } from '../../api/topology'
import { getSites, type SiteResponse } from '../../api/sites'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// 画布状态
const canvasWrapper = ref<HTMLElement | null>(null)
const canvasWidth = ref(800)
const canvasHeight = ref(600)
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)

// 数据状态
const deviceNodes = ref<DeviceNode[]>([])
const deviceEdges = ref<DeviceEdge[]>([])
const sites = ref<SiteResponse[]>([])
const selectedSiteId = ref<number | null>(null)
const showIsolatedDevices = ref(false)
const selectedNodeId = ref<string | null>(null)

// 搜索状态
const searchKeyword = ref('')

// 拖拽状态
const isDragging = ref(false)
const draggingNodeId = ref<string | null>(null)
const dragOffset = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const panOffset = ref({ x: 0, y: 0 })

// 布局状态
const isLayoutRunning = ref(false)
const nodePositions = ref<Record<string, { x: number; y: number }>>({})
const layoutAnimationId = ref<number | null>(null)

// 提示框状态
const tooltipVisible = ref(false)
const tooltipData = ref<DeviceNode>({} as DeviceNode)
const tooltipX = ref(0)
const tooltipY = ref(0)
const tooltipTargetNode = ref<string | null>(null) // 记录当前tooltip所属的节点ID
const hoverState = ref<'idle' | 'entering' | 'hovering' | 'leaving'>('idle') // hover状态机
let tooltipHideTimer: ReturnType<typeof setTimeout> | null = null
let tooltipShowTimer: ReturnType<typeof setTimeout> | null = null

// 刷新定时器
const refreshIntervalId = ref<number | null>(null)

// 节点尺寸
const nodeWidth = 160
const nodeHeight = 60

// 过滤后的节点（考虑搜索关键词）
const searchFilteredNodes = computed(() => {
  if (!searchKeyword.value.trim()) return deviceNodes.value
  const query = searchKeyword.value.toLowerCase()
  return deviceNodes.value.filter(d => 
    d.name.toLowerCase().includes(query) || 
    (d as DeviceNode).ip_address?.toLowerCase().includes(query)
  )
})

// 获取有边连接的节点ID集合
function getConnectedNodeIds(): Set<string> {
  const connectedIds = new Set<string>()
  deviceEdges.value.forEach(edge => {
    connectedIds.add(edge.source)
    connectedIds.add(edge.target)
  })
  return connectedIds
}

// 过滤后的边（只保留源节点和目标节点都存在的边）
const filteredEdges = computed(() => {
  const nodeIds = new Set(deviceNodes.value.map(n => n.id))
  return deviceEdges.value.filter(edge => 
    nodeIds.has(edge.source) && nodeIds.has(edge.target)
  )
})

// 最终显示的节点（考虑孤立设备开关）
const filteredNodes = computed(() => {
  let result = searchFilteredNodes.value
  
  if (!showIsolatedDevices.value) {
    const connectedIds = getConnectedNodeIds()
    result = result.filter(node => connectedIds.has(node.id))
  }
  
  return result
})

function handleSearch() {
  // 搜索逻辑已在 computed 中处理
}

function getNodePosition(nodeId: string): { x: number; y: number } {
  return nodePositions.value[nodeId] || { x: 0, y: 0 }
}

function getNodeClass(node: DeviceNode): string {
  return `node-${node.type} node-${node.status}`
}

function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    normal: '#67C23A',
    warning: '#E6A23C',
    offline: '#909399',
    critical: '#F56C6C',
    error: '#F56C6C',
    unknown: '#909399'
  }
  return map[status] || '#909399'
}

function getStatusText(status: string): string {
  const map: Record<string, string> = {
    normal: t('topology.statusNormal'),
    online: t('topology.statusOnline'),
    warning: t('topology.statusWarning'),
    offline: t('topology.statusOffline'),
    critical: t('topology.statusCritical'),
    error: t('topology.statusError'),
    unknown: t('topology.statusUnknown')
  }
  return map[status] || status
}

function getStatusClass(status: string): string {
  return `status-${status}`
}

function getDeviceTypeText(type: string): string {
  const map: Record<string, string> = {
    switch: t('topology.deviceSwitch'),
    router: t('topology.deviceRouter'),
    firewall: t('topology.deviceFirewall'),
    server: t('topology.deviceServer'),
    ap: t('topology.deviceAp')
  }
  return map[type] || type
}

function getMonitorClass(value: number | null, type: 'latency' | 'packet_loss'): string {
  if (value === null) return 'monitor-normal'
  if (type === 'latency') {
    if (value > 100) return 'monitor-warning'
    if (value > 50) return 'monitor-caution'
    return 'monitor-normal'
  } else {
    if (value > 5) return 'monitor-warning'
    if (value > 1) return 'monitor-caution'
    return 'monitor-normal'
  }
}

function initializePositions() {
  const nodes = deviceNodes.value
  const cols = Math.ceil(Math.sqrt(nodes.length))
  const spacing = 200
  const startX = canvasWidth.value / 2 / scale.value
  const startY = canvasHeight.value / 2 / scale.value
  
  nodes.forEach((node, index) => {
    const row = Math.floor(index / cols)
    const col = index % cols
    nodePositions.value[node.id] = {
      x: startX + (col - cols / 2) * spacing,
      y: startY + (row - Math.ceil(nodes.length / cols) / 2) * spacing
    }
  })
}

function runForceLayout() {
  if (isLayoutRunning.value) return
  isLayoutRunning.value = true
  
  const k = Math.sqrt(canvasWidth.value * canvasHeight.value / deviceNodes.value.length)
  const iterations = 100
  let iteration = 0
  
  function step() {
    const nodes = deviceNodes.value
    const forces: Record<string, { x: number; y: number }> = {}
    
    nodes.forEach(node => {
      forces[node.id] = { x: 0, y: 0 }
    })
    
    // 节点间斥力
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const n1 = nodes[i]
        const n2 = nodes[j]
        const dx = nodePositions.value[n2.id].x - nodePositions.value[n1.id].x
        const dy = nodePositions.value[n2.id].y - nodePositions.value[n1.id].y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        
        const force = k * k / dist
        forces[n1.id].x -= (dx / dist) * force
        forces[n1.id].y -= (dy / dist) * force
        forces[n2.id].x += (dx / dist) * force
        forces[n2.id].y += (dy / dist) * force
      }
    }
    
    // 边的引力
    deviceEdges.value.forEach(edge => {
      const source = nodePositions.value[edge.source]
      const target = nodePositions.value[edge.target]
      if (!source || !target) return
      
      const dx = target.x - source.x
      const dy = target.y - source.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      
      const force = dist / k
      forces[edge.source].x += (dx / dist) * force
      forces[edge.source].y += (dy / dist) * force
      forces[edge.target].x -= (dx / dist) * force
      forces[edge.target].y -= (dy / dist) * force
    })
    
    // 中心引力
    const centerX = canvasWidth.value / 2 / scale.value
    const centerY = canvasHeight.value / 2 / scale.value
    nodes.forEach(node => {
      const dx = centerX - nodePositions.value[node.id].x
      const dy = centerY - nodePositions.value[node.id].y
      forces[node.id].x += dx * 0.01
      forces[node.id].y += dy * 0.01
    })
    
    // 应用力
    nodes.forEach(node => {
      const pos = nodePositions.value[node.id]
      const fx = forces[node.id].x
      const fy = forces[node.id].y
      const maxForce = 10
      
      pos.x += Math.max(-maxForce, Math.min(maxForce, fx))
      pos.y += Math.max(-maxForce, Math.min(maxForce, fy))
    })
    
    iteration++
    if (iteration < iterations) {
      requestAnimationFrame(step)
    } else {
      isLayoutRunning.value = false
    }
  }
  
  requestAnimationFrame(step)
}

function resetLayout() {
  if (layoutAnimationId.value) {
    cancelAnimationFrame(layoutAnimationId.value)
  }
  isLayoutRunning.value = false
  initializePositions()
}

function zoomIn() {
  scale.value = Math.min(scale.value * 1.2, 3)
}

function zoomOut() {
  scale.value = Math.max(scale.value / 1.2, 0.3)
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

function startDrag(nodeId: string, event: MouseEvent) {
  isDragging.value = true
  draggingNodeId.value = nodeId
  dragOffset.value = {
    x: event.clientX - nodePositions.value[nodeId].x * scale.value - panX.value,
    y: event.clientY - nodePositions.value[nodeId].y * scale.value - panY.value
  }
}

function startPan(event: MouseEvent) {
  if (event.button !== 0) return
  isPanning.value = true
  panOffset.value = { x: event.clientX - panX.value, y: event.clientY - panY.value }
}

function onMouseMove(event: MouseEvent) {
  if (isDragging.value && draggingNodeId.value) {
    const pos = nodePositions.value[draggingNodeId.value]
    pos.x = (event.clientX - dragOffset.value.x - panX.value) / scale.value
    pos.y = (event.clientY - dragOffset.value.y - panY.value) / scale.value
  } else if (isPanning.value) {
    panX.value = event.clientX - panOffset.value.x
    panY.value = event.clientY - panOffset.value.y
  }
  
  // tooltip固定位置显示，不跟随鼠标移动避免闪烁
  // 位置在showNodeTooltip中设置一次后不再更新
}

function endMouseUp() {
  isDragging.value = false
  isPanning.value = false
  draggingNodeId.value = null
}

function onWheel(event: WheelEvent) {
  event.preventDefault()
  const delta = event.deltaY > 0 ? 0.9 : 1.1
  scale.value = Math.max(0.3, Math.min(3, scale.value * delta))
}

function showNodeTooltip(node: DeviceNode, event: MouseEvent) {
  // 如果已经在显示同一个节点的tooltip，不需要重复设置
  if (tooltipTargetNode.value === node.id && tooltipVisible.value) {
    // 如果正在离开状态，取消离开定时器
    if (hoverState.value === 'leaving' && tooltipHideTimer) {
      clearTimeout(tooltipHideTimer)
      tooltipHideTimer = null
    }
    return
  }
  
  // 如果正在离开状态，取消离开定时器
  if (hoverState.value === 'leaving' && tooltipHideTimer) {
    clearTimeout(tooltipHideTimer)
    tooltipHideTimer = null
  }
  
  // 取消之前的显示定时器（防抖）
  if (tooltipShowTimer) {
    clearTimeout(tooltipShowTimer)
    tooltipShowTimer = null
  }
  
  // 使用防抖延迟显示tooltip
  tooltipShowTimer = setTimeout(() => {
    hoverState.value = 'hovering'
    tooltipTargetNode.value = node.id
    tooltipData.value = node
    tooltipX.value = event.clientX + 15
    tooltipY.value = event.clientY + 15
    tooltipVisible.value = true
    tooltipShowTimer = null
  }, 50)
}

function hideTooltip() {
  // 使用延迟隐藏，防止快速进出导致闪烁
  hoverState.value = 'leaving'
  
  if (tooltipHideTimer) {
    clearTimeout(tooltipHideTimer)
  }
  
  tooltipHideTimer = setTimeout(() => {
    tooltipVisible.value = false
    tooltipTargetNode.value = null
    hoverState.value = 'idle'
    tooltipHideTimer = null
  }, 100)
}

async function loadSiteData() {
  try {
    sites.value = await getSites()
  } catch (error) {
    console.error('Failed to load sites:', error)
  }
}

async function loadDeviceData(keepPositions = false) {
  try {
    const data = await getDeviceGraph(selectedSiteId.value || undefined)
    deviceNodes.value = data.nodes
    deviceEdges.value = data.edges
    if (!keepPositions) {
      initializePositions()
    }
  } catch (error) {
    console.error('Failed to load device topology data:', error)
  }
}

function onSiteChange() {
  resetLayout()
  loadDeviceData()
}

function startRefreshTimer() {
  if (refreshIntervalId.value) {
    clearInterval(refreshIntervalId.value)
  }
  refreshIntervalId.value = window.setInterval(async () => {
    try {
      await loadDeviceData(true)
    } catch (error) {
      console.error('Auto refresh failed:', error)
    }
  }, 30000)
}

function stopRefreshTimer() {
  if (refreshIntervalId.value) {
    clearInterval(refreshIntervalId.value)
    refreshIntervalId.value = null
  }
}

function handleResize() {
  if (canvasWrapper.value) {
    canvasWidth.value = canvasWrapper.value.clientWidth
    canvasHeight.value = canvasWrapper.value.clientHeight
  }
}

onMounted(async () => {
  handleResize()
  window.addEventListener('resize', handleResize)
  await loadSiteData()
  await loadDeviceData()
  startRefreshTimer()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  stopRefreshTimer()
})
</script>

<style scoped>
.device-topology {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(135deg, #0a0e1a 0%, #1a1a2e 50%, #0f1724 100%);
}

.topology-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(180deg, rgba(22, 33, 62, 0.95) 0%, rgba(22, 33, 62, 0.85) 100%);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(45, 58, 79, 0.5);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.search-input {
  width: 320px;
}

.search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(64, 158, 255, 0.3);
  box-shadow: none;
  transition: all 0.3s ease;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(64, 158, 255, 0.6);
  background: rgba(255, 255, 255, 0.12);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.search-input :deep(.el-input__inner) {
  color: #fff;
}

.search-input :deep(.el-input__prefix) {
  color: rgba(255, 255, 255, 0.6);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.site-select {
  width: 200px;
}

.site-select :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(64, 158, 255, 0.3);
  box-shadow: none;
}

.site-select :deep(.el-input__inner) {
  color: #fff;
}

.toolbar-btn {
  width: 40px;
  height: 40px;
  padding: 0;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(64, 158, 255, 0.2);
  color: #fff;
  transition: all 0.3s ease;
}

.toolbar-btn:hover {
  background: rgba(64, 158, 255, 0.2);
  border-color: rgba(64, 158, 255, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.toolbar-btn:active {
  transform: translateY(0);
}

.topology-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: 
    radial-gradient(ellipse at 20% 30%, rgba(64, 158, 255, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 70%, rgba(100, 89, 234, 0.08) 0%, transparent 50%),
    linear-gradient(180deg, #0a0e1a 0%, #1a1a2e 100%);
}

.topology-canvas::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  opacity: 0.5;
}

.topology-svg {
  cursor: grab;
}

.topology-svg:active {
  cursor: grabbing;
}

.topology-edge {
  stroke: #4a5568;
  stroke-width: 2;
  fill: none;
  transition: all 0.3s ease;
  filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.5));
}

.topology-edge.normal {
  stroke: #67C23A;
  stroke-width: 2.5;
  filter: drop-shadow(0 0 6px rgba(103, 194, 58, 0.4));
}

.topology-edge.warning {
  stroke: #E6A23C;
  stroke-width: 2.5;
  filter: drop-shadow(0 0 6px rgba(230, 162, 60, 0.4));
}

.topology-edge.offline,
.topology-edge.critical {
  stroke: #F56C6C;
  stroke-width: 2;
  stroke-dasharray: 6,4;
  filter: drop-shadow(0 0 6px rgba(245, 108, 108, 0.4));
  animation: edge-pulse 2s ease-in-out infinite;
}

@keyframes edge-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.topology-node {
  cursor: pointer;
}

.topology-node text,
.topology-node circle {
  pointer-events: none;
}

.topology-node:hover {
}

.topology-node:hover .node-box {
  stroke: #409eff;
  stroke-width: 3;
}

.node-selected .node-box {
  stroke: #409eff;
  stroke-width: 3;
  filter: drop-shadow(0 0 15px rgba(64, 158, 255, 0.5));
}

.node-filtered {
  opacity: 0.3;
}

.node-box {
  fill: rgba(45, 58, 79, 0.9);
  stroke: rgba(74, 85, 104, 0.8);
  stroke-width: 2;
  backdrop-filter: blur(4px);
}

.node-switch .node-box {
  fill: rgba(45, 58, 79, 0.9);
}

.node-router .node-box {
  fill: rgba(45, 58, 79, 0.9);
}

.node-firewall .node-box {
  fill: rgba(45, 58, 79, 0.9);
}

.status-dot {
  stroke: #fff;
  stroke-width: 2;
  filter: drop-shadow(0 0 4px currentColor);
}

.node-name {
  fill: #fff;
  font-size: 13px;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
}

.node-city {
  fill: rgba(144, 147, 153, 0.9);
  font-size: 11px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
}

.node-monitor {
  font-size: 11px;
}

.monitor-label {
  fill: rgba(144, 147, 153, 0.8);
}

.monitor-value {
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
}

.monitor-normal {
  fill: #67C23A;
}

.monitor-caution {
  fill: #E6A23C;
}

.monitor-warning {
  fill: #F56C6C;
}

.tooltip {
  position: fixed;
  background: rgba(15, 23, 36, 0.98);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(64, 158, 255, 0.3);
  border-radius: 12px;
  padding: 16px 20px;
  z-index: 10000;
  pointer-events: none;
  min-width: 240px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(64, 158, 255, 0.1);
}

.tooltip-title {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(64, 158, 255, 0.2);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.tooltip-content {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.8;
}

.tooltip-content div {
  margin-bottom: 6px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.tooltip-label {
  flex: 0 0 auto;
  color: rgba(255, 255, 255, 0.75);
}

.tooltip-content div:last-child {
  margin-bottom: 0;
}

.tooltip-content div:first-child {
  font-weight: 600;
  color: #fff;
}

.status-normal,
.status-online {
  color: #67C23A;
  font-weight: 600;
  text-shadow: 0 0 8px rgba(103, 194, 58, 0.4);
}

.status-warning {
  color: #E6A23C;
  font-weight: 600;
  text-shadow: 0 0 8px rgba(230, 162, 60, 0.4);
}

.status-offline,
.status-unknown {
  color: #909399;
  font-weight: 600;
}

.status-critical,
.status-error {
  color: #F56C6C;
  font-weight: 600;
  text-shadow: 0 0 8px rgba(245, 108, 108, 0.4);
}

.topology-legend {
  display: flex;
  gap: 20px;
  padding: 16px 24px;
  background: linear-gradient(180deg, rgba(22, 33, 62, 0.85) 0%, rgba(22, 33, 62, 0.95) 100%);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(45, 58, 79, 0.5);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.legend-item .status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
}
</style>