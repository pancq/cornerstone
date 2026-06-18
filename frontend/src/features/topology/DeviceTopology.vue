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
        <el-dropdown :trigger="'click'" class="toolbar-btn">
          <el-button :icon="Download" :title="t('topology.export')" class="toolbar-btn" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="exportAsPNG">
                <el-icon><Image /></el-icon>
                {{ t('topology.exportPNG') }}
              </el-dropdown-item>
              <el-dropdown-item @click="exportAsJPG">
                <el-icon><Picture /></el-icon>
                {{ t('topology.exportJPG') }}
              </el-dropdown-item>
              <el-dropdown-item @click="exportAsPDF">
                <el-icon><Document /></el-icon>
                {{ t('topology.exportPDF') }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 右侧详情面板 -->
    <div v-if="selectedNode" class="detail-panel">
      <div class="panel-header">
        <div class="panel-title">{{ selectedNode.name }}</div>
        <el-button :icon="Close" class="close-btn" @click="closeDetailPanel" />
      </div>
      <div class="panel-content">
        <div class="info-row">
          <span class="info-label">设备类型</span>
          <span class="info-value">{{ getDeviceTypeText((selectedNode as DeviceNode).type) }}</span>
        </div>
        
        <template v-if="isInternetNode">
          <div class="info-row" v-if="(selectedNode as DeviceNode).provider">
            <span class="info-label">运营商</span>
            <span class="info-value">{{ (selectedNode as DeviceNode).provider }}</span>
          </div>
          <div class="info-row" v-if="(selectedNode as DeviceNode).bandwidth">
            <span class="info-label">带宽</span>
            <span class="info-value">{{ (selectedNode as DeviceNode).bandwidth }} Mbps</span>
          </div>
        </template>
        
        <div class="info-row" v-if="!isInternetNode">
          <span class="info-label">厂商</span>
          <span class="info-value">{{ (selectedNode as DeviceNode).vendor }}</span>
        </div>
        <div class="info-row" v-if="!isInternetNode">
          <span class="info-label">管理IP</span>
          <span class="info-value">{{ (selectedNode as DeviceNode).ip_address }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">状态</span>
          <span class="info-value" :class="getStatusClass(selectedNode.status)">{{ getStatusText(selectedNode.status) }}</span>
        </div>
        <div class="info-row" v-if="!isInternetNode">
          <span class="info-label">站点</span>
          <span class="info-value">{{ (selectedNode as DeviceNode).site_name || '-' }}</span>
        </div>
        <div class="info-row" v-if="!isInternetNode">
          <span class="info-label">丢包率</span>
          <span class="info-value">{{ (selectedNode as DeviceNode).packet_loss != null ? (selectedNode as DeviceNode).packet_loss + '%' : '-' }}</span>
        </div>
        
        <!-- 对端连接设备和端口信息 -->
        <template v-if="connectedDevices.length > 0">
          <div class="connection-section">
            <div class="connection-label">连接设备</div>
            <div class="connection-list">
              <div v-for="conn in connectedDevices" :key="conn.id" class="connection-item">
                <div class="connection-device">{{ conn.name }}</div>
                <div class="connection-ports">
                  <span v-if="conn.sourceInterface" class="port-info">本端: {{ conn.sourceInterface }}</span>
                  <span v-if="conn.targetInterface" class="port-info">对端: {{ conn.targetInterface }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="topology-main">
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
            <filter id="glow-blue">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          <g :transform="`translate(${panX}, ${panY}) scale(${scale})`">
            <!-- 连接线 -->
            <g v-for="edge in filteredEdges" :key="'edge-' + edge.id">
              <line
                :x1="getNodePosition(edge.source).x"
                :y1="getNodePosition(edge.source).y"
                :x2="getNodePosition(edge.target).x"
                :y2="getNodePosition(edge.target).y"
                class="topology-edge"
                :class="getEdgeClass(edge)"
              />
              <text
                :x="(getNodePosition(edge.source).x + getNodePosition(edge.target).x) / 2"
                :y="(getNodePosition(edge.source).y + getNodePosition(edge.target).y) / 2 - 8"
                text-anchor="middle"
                class="edge-bandwidth"
              >
                {{ getBandwidthLabel(edge) }}
              </text>
            </g>

            <!-- 节点 -->
            <g
              v-for="node in filteredNodes"
              :key="'node-' + node.id"
              :transform="`translate(${getNodePosition(node.id).x}, ${getNodePosition(node.id).y})`"
              class="topology-node"
              :class="{ 'node-selected': selectedNodeId === node.id }"
              @mousedown.stop="startDrag(node.id, $event)"
              @click.stop="onNodeClick(node.id)"
              @mouseenter="onNodeHover(node, $event)"
              @mouseleave="onNodeLeave"
            >
              <rect
                :width="nodeWidth"
                :height="nodeHeight"
                :x="-nodeWidth / 2"
                :y="-nodeHeight / 2"
                rx="10"
                class="node-box"
                :style="getNodeStyle(node as DeviceNode)"
              />
              <!-- 状态点：右上角内嵌 -->
              <circle
                :cx="nodeWidth / 2 - 10"
                :cy="-nodeHeight / 2 + 10"
                r="5"
                class="status-dot"
                :fill="getStatusColor(node.status)"
                stroke="#1a2035"
                stroke-width="1.5"
              />
              <!-- 图标区域：左侧居中 -->
              <g :transform="`translate(${-nodeWidth / 2 + 4}, ${-24})`">
                <foreignObject width="48" height="48">
                  <NetworkIcon
                    :type="getIconType((node as DeviceNode).type, (node as DeviceNode).vendor, node.name)"
                    :status="mapStatus(node.status)"
                    size="md"
                    :show-status="false"
                    class="node-icon"
                  />
                </foreignObject>
              </g>
              <!-- 文本区域 -->
              <g :transform="`translate(${-nodeWidth / 2 + 56}, ${-nodeHeight / 2 + 12})`">
                <text x="0" y="16" text-anchor="start" class="node-name">{{ node.name }}</text>
                <text v-if="!isCircuitNode(node)" x="0" y="34" text-anchor="start" class="node-ip">{{ (node as DeviceNode).ip_address }}</text>
                <text v-if="isCircuitNode(node) && (node as DeviceNode).bandwidth" x="0" y="34" text-anchor="start" class="node-ip">{{ (node as DeviceNode).bandwidth }} Mbps</text>
                <text v-if="!isCircuitNode(node)" x="0" y="52" text-anchor="start" class="node-status" :class="getStatusClass(node.status)">
                  {{ getStatusSummary(node as DeviceNode) }}
                </text>
              </g>
            </g>
          </g>
        </svg>

        <!-- Hover 提示框 -->
        <div v-if="hoveredNode" class="tooltip-panel" :style="tooltipStyle">
          <div class="tooltip-header">
            <span class="tooltip-name">{{ hoveredNode.name }}</span>
          </div>
          <div class="tooltip-divider"></div>
          <div class="tooltip-row">
            <span class="tooltip-label">类型</span>
            <span class="tooltip-value">{{ getDeviceTypeText((hoveredNode as DeviceNode).type) }}</span>
          </div>
          <div class="tooltip-row">
            <span class="tooltip-label">IP</span>
            <span class="tooltip-value">{{ (hoveredNode as DeviceNode).ip_address }}</span>
          </div>
          <div class="tooltip-row">
            <span class="tooltip-label">状态</span>
            <span class="tooltip-value" :class="getStatusClass(hoveredNode.status)">
              <span class="tooltip-status-dot" :style="{ background: getStatusColor(hoveredNode.status) }"></span>
              {{ getStatusText(hoveredNode.status) }}
            </span>
          </div>
          <div class="tooltip-row" v-if="(hoveredNode as DeviceNode).site_name">
            <span class="tooltip-label">位置</span>
            <span class="tooltip-value">{{ (hoveredNode as DeviceNode).site_name }}</span>
          </div>
          <div class="tooltip-divider"></div>
          <div class="tooltip-hint">点击查看详情 →</div>
        </div>
      </div>

      <!-- 图例 -->
      <div class="legend-panel">
        <div class="legend-title">图例</div>
        <div class="legend-section">
          <div class="legend-item">
            <span class="legend-dot online"></span>
            <span>在线</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot warning"></span>
            <span>告警</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot offline"></span>
            <span>离线</span>
          </div>
        </div>
        <div class="legend-section">
          <div class="legend-item">
            <svg width="30" height="4" viewBox="0 0 30 4">
              <line x1="0" y1="2" x2="30" y2="2" stroke="#5B8DB8" stroke-width="2" />
            </svg>
            <span>正常链路</span>
          </div>
          <div class="legend-item">
            <svg width="30" height="4" viewBox="0 0 30 4">
              <line x1="0" y1="2" x2="30" y2="2" stroke="#F56C6C" stroke-width="2" stroke-dasharray="6,3" />
            </svg>
            <span>故障链路</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Search, Refresh, Grid, ZoomIn, ZoomOut, FullScreen, Close, Download, Image, Picture, Document } from '@element-plus/icons-vue'
import { getDeviceGraph, getSiteDevices, updateCircuitConnection, type DeviceNode, type DeviceEdge, type SiteDeviceOption } from '../../api/topology'
import { getSites as getSitesApi, type SiteResponse } from '../../api/sites'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import NetworkIcon from '../../components/icons/NetworkIcon.vue'
import { inferIconType, mapStatus } from '../../components/icons/networkIconTypes'
import { DEVICE_TYPE_CONFIG, STATUS_DOT_COLOR, DEVICE_RANK } from './topologyConfig'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

// 获取图标类型
function getIconType(deviceType: string | null | undefined, vendor: string | null | undefined, name: string | null | undefined): string {
  return inferIconType(deviceType, vendor, name)
}

const { t } = useI18n()

const canvasWrapper = ref<HTMLElement | null>(null)
const canvasWidth = ref(800)
const canvasHeight = ref(600)
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)

const deviceNodes = ref<DeviceNode[]>([])
const deviceEdges = ref<DeviceEdge[]>([])
const sites = ref<SiteResponse[]>([])
const selectedSiteId = ref<number | null>(null)
const showIsolatedDevices = ref(false)
const selectedNodeId = ref<string | null>(null)
const searchKeyword = ref('')

// 站点设备列表（用于专线连接设置）
const siteDevices = ref<SiteDeviceOption[]>([])
// 专线连接选择的设备ID
const selectedConnectionDeviceId = ref<number | null>(null)
const connectionLoading = ref(false)

const isDragging = ref(false)
const draggingNodeId = ref<string | null>(null)
const dragOffset = ref({ x: 0, y: 0 })
const isPanning = ref(false)
const panOffset = ref({ x: 0, y: 0 })

const isLayoutRunning = ref(false)
const nodePositions = ref<Record<string, { x: number; y: number }>>({})

const refreshIntervalId = ref<number | null>(null)

const hoveredNode = ref<DeviceNode | null>(null)
const tooltipStyle = ref({ top: '0px', left: '0px' })

const nodeWidth = 200
const nodeHeight = 72

const searchFilteredNodes = computed(() => {
  if (!searchKeyword.value.trim()) return deviceNodes.value
  const query = searchKeyword.value.toLowerCase()
  return deviceNodes.value.filter(d => 
    d.name.toLowerCase().includes(query) || 
    (d as DeviceNode).ip_address?.toLowerCase().includes(query)
  )
})

function getConnectedNodeIds(): Set<string> {
  const connectedIds = new Set<string>()
  deviceEdges.value.forEach(edge => {
    connectedIds.add(edge.source)
    connectedIds.add(edge.target)
  })
  return connectedIds
}

const filteredEdges = computed(() => {
  const nodeIds = new Set(deviceNodes.value.map(n => n.id))
  return deviceEdges.value.filter(edge => 
    nodeIds.has(edge.source) && nodeIds.has(edge.target)
  )
})

const filteredNodes = computed(() => {
  let result = searchFilteredNodes.value
  if (!showIsolatedDevices.value) {
    const connectedIds = getConnectedNodeIds()
    result = result.filter(node => connectedIds.has(node.id))
  }
  return result
})

const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return deviceNodes.value.find(n => n.id === selectedNodeId.value)
})

// 判断节点是否为专线节点（互联网/MPLS/SD-WAN）
function isCircuitNode(node: any): boolean {
  return node.type === 'internet' || node.type === 'isp' || node.type === 'sdwan' || node.id?.startsWith('internet_')
}

// 判断选中的节点是否为互联网出口
const isInternetNode = computed(() => {
  if (!selectedNode.value) return false
  // 判断是否为专线类型节点（internet/isp/sdwan）
  const nodeType = selectedNode.value.type
  const nodeId = selectedNode.value.id
  return nodeType === 'internet' || nodeType === 'isp' || nodeType === 'sdwan' ||
         nodeId.startsWith('internet_') || nodeId.startsWith('isp_') || nodeId.startsWith('sdwan_')
})

// 获取当前选中互联网出口对应的电路ID
const currentCircuitId = computed(() => {
  if (!selectedNode.value?.circuit_id) return null
  return selectedNode.value.circuit_id
})

// 获取当前连接的设备名称
const connectedDeviceName = computed(() => {
  if (!selectedNode.value) return null
  const edge = deviceEdges.value.find(e => e.source === selectedNode.value?.id || e.target === selectedNode.value?.id)
  if (!edge) return null
  const connectedNodeId = edge.source === selectedNode.value?.id ? edge.target : edge.source
  const connectedNode = deviceNodes.value.find(n => n.id === connectedNodeId)
  return connectedNode?.name || null
})

// 获取所有对端连接设备和端口信息
const connectedDevices = computed(() => {
  if (!selectedNode.value) return []
  
  const result: Array<{
    id: string
    name: string
    sourceInterface: string | null
    targetInterface: string | null
  }> = []
  
  const nodeId = selectedNode.value.id
  
  // 查找所有与当前节点相连的边
  const relatedEdges = deviceEdges.value.filter(e => e.source === nodeId || e.target === nodeId)
  
  for (const edge of relatedEdges) {
    const connectedNodeId = edge.source === nodeId ? edge.target : edge.source
    const connectedNode = deviceNodes.value.find(n => n.id === connectedNodeId)
    
    if (!connectedNode) continue
    
    // 根据当前节点在边中的位置确定端口方向
    let sourceInterface: string | null = null
    let targetInterface: string | null = null
    
    if (edge.source === nodeId) {
      // 当前节点是source端
      sourceInterface = edge.source_interface || null
      targetInterface = edge.target_interface || null
    } else {
      // 当前节点是target端，端口方向互换
      sourceInterface = edge.target_interface || null
      targetInterface = edge.source_interface || null
    }
    
    result.push({
      id: connectedNode.id,
      name: connectedNode.name,
      sourceInterface,
      targetInterface
    })
  }
  
  return result
})

function handleSearch() {}

function getNodePosition(nodeId: string): { x: number; y: number } {
  return nodePositions.value[nodeId] || { x: 0, y: 0 }
}

function getDeviceColor(node: DeviceNode): string {
  const iconType = inferIconType(node.type, node.vendor, node.name)
  const config = DEVICE_TYPE_CONFIG[iconType] || DEVICE_TYPE_CONFIG.unknown
  return config.color
}

function getNodeStyle(node: DeviceNode) {
  const iconType = inferIconType(node.type, node.vendor, node.name)
  const config = DEVICE_TYPE_CONFIG[iconType] || DEVICE_TYPE_CONFIG.unknown
  const mappedStatus = mapStatus(node.status)
  const isOnline = mappedStatus === 'online'
  return {
    fill: '#162035',
    fillOpacity: isOnline ? 0.95 : 0.8,
    stroke: config.color,
    strokeWidth: isOnline ? 2 : 1.5,
    strokeOpacity: isOnline ? 0.8 : 0.5
  }
}

function getEdgeClass(edge: DeviceEdge): string {
  const sourceNode = deviceNodes.value.find(n => n.id === edge.source)
  const targetNode = deviceNodes.value.find(n => n.id === edge.target)
  const sourceStatus = sourceNode?.status || 'unknown'
  const targetStatus = targetNode?.status || 'unknown'
  
  if (sourceStatus === 'critical' || targetStatus === 'critical') return 'edge-critical'
  if (sourceStatus === 'offline' || targetStatus === 'offline') return 'edge-offline'
  if (sourceStatus === 'warning' || targetStatus === 'warning') return 'edge-warning'
  return 'edge-normal'
}

function getStatusColor(status: string): string {
  const mappedStatus = mapStatus(status)
  return STATUS_DOT_COLOR[mappedStatus] || '#909399'
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

function getBandwidthLabel(edge: DeviceEdge): string {
  const bandwidths = ['100M', '1G', '10G', '100M', '1G', '10G', '1G']
  const index = parseInt(edge.id.replace('link_', '')) % bandwidths.length
  return index >= 0 ? bandwidths[index] : '100M'
}

function getDeviceTypeText(type: string): string {
  const map: Record<string, string> = {
    switch: t('topology.deviceSwitch'),
    router: t('topology.deviceRouter'),
    firewall: t('topology.deviceFirewall'),
    server: t('topology.deviceServer'),
    ap: t('topology.deviceAp'),
    'core-switch': t('topology.deviceCoreSwitch'),
    'access-switch': t('topology.deviceAccessSwitch'),
    'load-balancer': '负载均衡',
    ac: '无线控制器',
    internet: '互联网',
    unknown: '未知设备'
  }
  return map[type] || type
}

function getStatusSummary(node: DeviceNode): string {
  const mappedStatus = mapStatus(node.status)
  if (mappedStatus === 'offline') {
    return `${t('topology.statusOffline')} · 2小时前`
  }
  if (mappedStatus === 'warning') {
    return `${t('topology.statusWarning')} · 1条未处理`
  }
  if (mappedStatus === 'online') {
    return `${t('topology.statusOnline')} · 备份3h前`
  }
  return t('topology.statusUnknown')
}

function initializePositions() {
  const nodes = deviceNodes.value
  const layers: Record<string, typeof nodes> = {}
  
  nodes.forEach(node => {
    const iconType = inferIconType((node as DeviceNode).type, (node as DeviceNode).vendor, node.name)
    const rank = DEVICE_RANK[iconType] ?? 3
    const rankKey = `rank_${rank}`
    if (!layers[rankKey]) layers[rankKey] = []
    layers[rankKey].push(node)
  })
  
  const rankOrder = ['rank_0', 'rank_1', 'rank_2', 'rank_3', 'rank_4']
  const activeRanks = rankOrder.filter(r => layers[r] && layers[r].length > 0)
  const totalLayers = activeRanks.length
  
  const usableHeight = canvasHeight.value / scale.value
  const layerSpacing = Math.min(140, (usableHeight - 120) / Math.max(totalLayers - 1, 1))
  const totalHeight = (totalLayers - 1) * layerSpacing
  const startY = (usableHeight - totalHeight) / 2
  
  activeRanks.forEach((rankKey, layerIndex) => {
    const group = layers[rankKey]
    const groupY = startY + layerIndex * layerSpacing
    const groupWidth = group.length * 220
    const centerX = canvasWidth.value / 2 / scale.value
    
    group.forEach((node, index) => {
      const xOffset = (index - (group.length - 1) / 2) * 220
      nodePositions.value[node.id] = {
        x: centerX + xOffset,
        y: groupY
      }
    })
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
    
    const centerX = canvasWidth.value / 2 / scale.value
    const centerY = canvasHeight.value / 2 / scale.value
    nodes.forEach(node => {
      const dx = centerX - nodePositions.value[node.id].x
      const dy = centerY - nodePositions.value[node.id].y
      forces[node.id].x += dx * 0.01
      forces[node.id].y += dy * 0.01
    })
    
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

function onNodeClick(nodeId: string) {
  selectedNodeId.value = selectedNodeId.value === nodeId ? null : nodeId
  
  // 如果点击的是互联网出口节点，加载站点设备列表
  const clickedNode = deviceNodes.value.find(n => n.id === nodeId)
  if (clickedNode && (clickedNode.type === 'internet' || nodeId.startsWith('internet_'))) {
    loadSiteDevicesForConnection(clickedNode.site_id)
  }
}

// 加载站点设备列表
async function loadSiteDevicesForConnection(siteId: number | null) {
  if (!siteId) return
  try {
    siteDevices.value = await getSiteDevices(siteId)
    // 从当前连接关系中获取已连接的设备
    const node = selectedNode.value
    if (node) {
      const edge = deviceEdges.value.find(e => e.source === node.id || e.target === node.id)
      if (edge) {
        const connectedNodeId = edge.source === node.id ? edge.target : edge.source
        const connectedDevice = deviceNodes.value.find(n => n.id === connectedNodeId)
        if (connectedDevice) {
          selectedConnectionDeviceId.value = connectedDevice.device_id > 0 ? connectedDevice.device_id : null
        }
      }
    }
  } catch (error) {
    console.error('Failed to load site devices:', error)
  }
}

// 更新专线连接
async function handleConnectionChange() {
  if (!currentCircuitId.value) return
  
  connectionLoading.value = true
  try {
    await updateCircuitConnection(currentCircuitId.value, selectedConnectionDeviceId.value)
    ElMessage.success('连接已更新')
    // 重新加载拓扑数据
    await loadDeviceData()
  } catch (error) {
    console.error('Failed to update connection:', error)
    ElMessage.error('更新连接失败')
  } finally {
    connectionLoading.value = false
  }
}

function onNodeHover(node: DeviceNode, event: MouseEvent) {
  hoveredNode.value = node
  const canvasRect = canvasWrapper.value?.getBoundingClientRect()
  if (canvasRect) {
    const x = event.clientX - canvasRect.left + 16
    const y = event.clientY - canvasRect.top - 10
    tooltipStyle.value = {
      top: `${y}px`,
      left: `${x}px`
    }
  }
}

function onNodeLeave() {
  hoveredNode.value = null
}

function closeDetailPanel() {
  selectedNodeId.value = null
}

function viewDeviceDetail() {
  console.log('View device detail:', selectedNode.value)
}

async function loadSiteData() {
  try {
    sites.value = await getSitesApi()
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

// 导出为PNG
async function exportAsPNG() {
  const canvasEl = canvasWrapper.value
  if (!canvasEl) {
    ElMessage.error(t('topology.exportError'))
    return
  }
  
  try {
    ElMessage.info(t('topology.exporting'))
    const canvas = await html2canvas(canvasEl, {
      backgroundColor: '#0f1724',
      scale: 2,
      useCORS: true,
      logging: false
    })
    
    const link = document.createElement('a')
    link.download = `topology-${Date.now()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    ElMessage.success(t('topology.exportSuccess'))
  } catch (error) {
    console.error('Export PNG failed:', error)
    ElMessage.error(t('topology.exportError'))
  }
}

// 导出为JPG
async function exportAsJPG() {
  const canvasEl = canvasWrapper.value
  if (!canvasEl) {
    ElMessage.error(t('topology.exportError'))
    return
  }
  
  try {
    ElMessage.info(t('topology.exporting'))
    const canvas = await html2canvas(canvasEl, {
      backgroundColor: '#0f1724',
      scale: 2,
      useCORS: true,
      logging: false
    })
    
    const link = document.createElement('a')
    link.download = `topology-${Date.now()}.jpg`
    link.href = canvas.toDataURL('image/jpeg', 0.95)
    link.click()
    ElMessage.success(t('topology.exportSuccess'))
  } catch (error) {
    console.error('Export JPG failed:', error)
    ElMessage.error(t('topology.exportError'))
  }
}

// 导出为PDF
async function exportAsPDF() {
  const canvasEl = canvasWrapper.value
  if (!canvasEl) {
    ElMessage.error(t('topology.exportError'))
    return
  }
  
  try {
    ElMessage.info(t('topology.exporting'))
    const canvas = await html2canvas(canvasEl, {
      backgroundColor: '#0f1724',
      scale: 2,
      useCORS: true,
      logging: false
    })
    
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({
      orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
      unit: 'px',
      format: [canvas.width, canvas.height]
    })
    
    pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height)
    pdf.save(`topology-${Date.now()}.pdf`)
    ElMessage.success(t('topology.exportSuccess'))
  } catch (error) {
    console.error('Export PDF failed:', error)
    ElMessage.error(t('topology.exportError'))
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
  background: #0a0e1a;
  position: relative;
}

.topology-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: rgba(22, 33, 62, 0.95);
  border-bottom: 1px solid rgba(45, 58, 79, 0.5);
  flex-wrap: wrap;
  gap: 8px;
}

.search-input {
  width: 240px;
}

.search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(64, 158, 255, 0.3);
}

.search-input :deep(.el-input__inner) {
  color: #fff;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.site-select {
  width: 160px;
}

.site-select :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(64, 158, 255, 0.3);
}

.site-select :deep(.el-input__inner) {
  color: #fff;
}

.internet-control {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(64, 158, 255, 0.2);
  border-radius: 6px;
  padding: 4px 10px;
}

.control-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.control-value {
  font-size: 14px;
  font-weight: 600;
  color: #40A9FF;
  min-width: 20px;
  text-align: center;
}

.internet-control .el-button {
  width: 24px;
  height: 24px;
  padding: 0;
  font-size: 14px;
  background: rgba(64, 158, 255, 0.15);
  border-color: rgba(64, 158, 255, 0.3);
  color: #40A9FF;
}

.internet-control .el-button:hover {
  background: rgba(64, 158, 255, 0.3);
}

.toolbar-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(64, 158, 255, 0.2);
  color: #fff;
}

.toolbar-btn:hover {
  background: rgba(64, 158, 255, 0.2);
}

.topology-main {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.topology-canvas {
  flex: 1;
  position: relative;
  background: 
    radial-gradient(ellipse at 20% 30%, rgba(64, 158, 255, 0.04) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 70%, rgba(100, 89, 234, 0.04) 0%, transparent 50%),
    #0a0e1a;
}

.topology-canvas::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
  background-size: 30px 30px;
  pointer-events: none;
}

.topology-svg {
  cursor: grab;
}

.topology-svg:active {
  cursor: grabbing;
}

.topology-edge {
  fill: none;
  transition: all 0.3s ease;
}

.topology-edge.edge-normal {
  stroke: #5B8DB8;
  stroke-width: 2;
}

.topology-edge.edge-warning {
  stroke: #E6A23C;
  stroke-width: 2;
  stroke-dasharray: 8,3;
}

.topology-edge.edge-offline {
  stroke: #606266;
  stroke-width: 1.5;
  stroke-dasharray: 4,4;
}

.topology-edge.edge-critical {
  stroke: #F56C6C;
  stroke-width: 2;
  stroke-dasharray: 6,3;
}

.edge-bandwidth {
  fill: rgba(255, 255, 255, 0.6);
  font-size: 10px;
  font-weight: 500;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9);
  pointer-events: none;
}

.topology-node {
  cursor: pointer;
}

.topology-node:hover .node-box {
  stroke-width: 2.5;
  filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.15));
}

.topology-node text,
.topology-node circle {
  pointer-events: none;
}

.node-selected .node-box {
  stroke: #409eff;
  stroke-width: 2.5;
  filter: drop-shadow(0 0 8px rgba(64, 158, 255, 0.4));
}

.node-box {
  stroke-width: 1.5;
}

.node-icon {
  display: flex !important;
  align-items: center;
  justify-content: center;
  width: 100% !important;
  height: 100% !important;
  pointer-events: none;
  padding: 2px;
}

.status-dot {
  filter: drop-shadow(0 0 3px currentColor);
}

.node-name {
  fill: #fff;
  font-size: 14px;
  font-weight: 700;
}

.node-ip {
  fill: rgba(144, 147, 153, 0.7);
  font-size: 12px;
}

.node-status {
  font-size: 11px;
  font-weight: 600;
}

.node-status.status-online,
.node-status.status-normal {
  fill: #67C23A;
}

.node-status.status-warning {
  fill: #E6A23C;
}

.node-status.status-offline,
.node-status.status-critical,
.node-status.status-error {
  fill: #F56C6C;
}

.node-status.status-unknown {
  fill: #909399;
}

/* Tooltip */
.tooltip-panel {
  position: absolute;
  background: rgba(20, 30, 50, 0.96);
  border: 1px solid rgba(64, 158, 255, 0.25);
  border-radius: 8px;
  padding: 12px 16px;
  min-width: 220px;
  z-index: 200;
  pointer-events: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.tooltip-header {
  margin-bottom: 4px;
}

.tooltip-name {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.tooltip-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 8px 0;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.tooltip-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
}

.tooltip-value {
  font-size: 12px;
  color: #fff;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tooltip-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.tooltip-hint {
  font-size: 11px;
  color: rgba(64, 158, 255, 0.7);
  margin-top: 4px;
}

/* Detail Panel */
.detail-panel {
  position: absolute;
  right: 0;
  top: 60px;
  bottom: 0;
  width: 260px;
  background: rgba(15, 23, 36, 0.98);
  border-left: 1px solid rgba(64, 158, 255, 0.2);
  display: flex;
  flex-direction: column;
  z-index: 100;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(64, 158, 255, 0.2);
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.close-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.panel-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.info-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.info-value {
  font-size: 12px;
  color: #fff;
  font-weight: 500;
}

.panel-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(64, 158, 255, 0.2);
}

.panel-footer .el-button {
  width: 100%;
}

/* Connection Setting */
.connection-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(64, 158, 255, 0.2);
}

.connection-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8px;
}

.connection-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.connection-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  padding: 8px 12px;
}

.connection-device {
  font-size: 13px;
  color: #fff;
  font-weight: 500;
}

.connection-ports {
  display: flex;
  gap: 16px;
  margin-top: 4px;
}

.port-info {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

/* Legend */
.legend-panel {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(15, 23, 36, 0.95);
  border: 1px solid rgba(64, 158, 255, 0.15);
  border-radius: 8px;
  padding: 12px 16px;
  z-index: 50;
}

.legend-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 8px;
}

.legend-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 8px;
}

.legend-section:last-child {
  margin-bottom: 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.online {
  background: #67C23A;
}

.legend-dot.warning {
  background: #E6A23C;
}

.legend-dot.offline {
  background: #F56C6C;
}

.status-normal,
.status-online {
  color: #67C23A;
}

.status-warning {
  color: #E6A23C;
}

.status-offline,
.status-critical,
.status-error {
  color: #F56C6C;
}

.status-unknown {
  color: #909399;
}
</style>