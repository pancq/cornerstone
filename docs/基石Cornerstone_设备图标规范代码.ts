/* ============================================================
   基石 Cornerstone · 网络设备图标库规范
   Trae 开发说明：严格按照此文件实现，不得自行修改颜色和图标
   ============================================================ */

/* ------------------------------------------------------------
   第一步：安装 Tabler Icons 字体（若未安装）
   在 index.html 或 main.ts 中引入：
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
   ------------------------------------------------------------ */

/* ------------------------------------------------------------
   第二步：设备类型颜色配置
   文件位置：frontend/src/constants/deviceIcons.ts
   ------------------------------------------------------------ */

// deviceIcons.ts
export const DEVICE_TYPE_CONFIG: Record<string, {
  color: string
  bgColor: string
  borderColor: string
  label: string
  group: string
  iconClass: string
  svgInline?: string
}> = {
  // ── 核心网络设备 ──────────────────────────────────────────
  'router': {
    color: '#E6A23C',
    bgColor: 'rgba(230,162,60,0.15)',
    borderColor: 'rgba(230,162,60,0.4)',
    label: '路由器',
    group: '核心网络设备',
    iconClass: 'ti ti-router',
  },
  'core-switch': {
    color: '#409EFF',
    bgColor: 'rgba(64,158,255,0.15)',
    borderColor: 'rgba(64,158,255,0.4)',
    label: '核心交换机',
    group: '核心网络设备',
    iconClass: 'ti ti-switch',
  },
  'access-switch': {
    color: '#79BBFF',
    bgColor: 'rgba(121,187,255,0.12)',
    borderColor: 'rgba(121,187,255,0.35)',
    label: '接入交换机',
    group: '核心网络设备',
    iconClass: 'ti ti-switch-2',
  },
  'firewall': {
    color: '#F56C6C',
    bgColor: 'rgba(245,108,108,0.15)',
    borderColor: 'rgba(245,108,108,0.4)',
    label: '防火墙',
    group: '核心网络设备',
    iconClass: 'ti ti-shield',
  },
  'load-balancer': {
    color: '#9B59B6',
    bgColor: 'rgba(155,89,182,0.15)',
    borderColor: 'rgba(155,89,182,0.4)',
    label: '负载均衡',
    group: '核心网络设备',
    iconClass: 'ti ti-arrow-fork',
  },
  'ap': {
    color: '#67C23A',
    bgColor: 'rgba(103,194,58,0.15)',
    borderColor: 'rgba(103,194,58,0.4)',
    label: '无线AP',
    group: '核心网络设备',
    iconClass: 'ti ti-wifi',
  },
  'ac': {
    color: '#4CAF50',
    bgColor: 'rgba(76,175,80,0.15)',
    borderColor: 'rgba(76,175,80,0.4)',
    label: '无线控制器',
    group: '核心网络设备',
    iconClass: 'ti ti-broadcast',
  },
  'sdwan': {
    color: '#00BCD4',
    bgColor: 'rgba(0,188,212,0.15)',
    borderColor: 'rgba(0,188,212,0.4)',
    label: 'SD-WAN',
    group: '核心网络设备',
    iconClass: '',
    // SD-WAN 使用内联 SVG，不用 Tabler Icons
    svgInline: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="5" cy="5" r="2" fill="#00BCD4"/>
  <circle cx="19" cy="5" r="2" fill="#00BCD4"/>
  <circle cx="5" cy="19" r="2" fill="#00BCD4"/>
  <circle cx="19" cy="19" r="2" fill="#00BCD4"/>
  <circle cx="12" cy="12" r="2.5" fill="#00BCD4"/>
  <line x1="7" y1="5" x2="10.5" y2="10.5" stroke="#00BCD4" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="17" y1="5" x2="13.5" y2="10.5" stroke="#00BCD4" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="7" y1="19" x2="10.5" y2="13.5" stroke="#00BCD4" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="17" y1="19" x2="13.5" y2="13.5" stroke="#00BCD4" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="7" y1="6" x2="17" y2="6" stroke="#00BCD4" stroke-width="1" stroke-dasharray="2 2" stroke-linecap="round"/>
  <line x1="5" y1="7" x2="5" y2="17" stroke="#00BCD4" stroke-width="1" stroke-dasharray="2 2" stroke-linecap="round"/>
</svg>`,
  },

  // ── 服务器与终端 ───────────────────────────────────────────
  'server': {
    color: '#36CFC9',
    bgColor: 'rgba(54,207,201,0.15)',
    borderColor: 'rgba(54,207,201,0.4)',
    label: '服务器',
    group: '服务器与终端',
    iconClass: 'ti ti-server',
  },
  'pc': {
    color: '#8899AA',
    bgColor: 'rgba(136,153,170,0.15)',
    borderColor: 'rgba(136,153,170,0.35)',
    label: 'PC / 工作站',
    group: '服务器与终端',
    iconClass: 'ti ti-device-desktop',
  },
  'laptop': {
    color: '#8899AA',
    bgColor: 'rgba(136,153,170,0.15)',
    borderColor: 'rgba(136,153,170,0.35)',
    label: '笔记本',
    group: '服务器与终端',
    iconClass: 'ti ti-device-laptop',
  },
  'printer': {
    color: '#909399',
    bgColor: 'rgba(144,147,153,0.12)',
    borderColor: 'rgba(144,147,153,0.3)',
    label: '打印机',
    group: '服务器与终端',
    iconClass: 'ti ti-printer',
  },
  'nas': {
    color: '#2D5BE3',
    bgColor: 'rgba(45,91,227,0.15)',
    borderColor: 'rgba(45,91,227,0.4)',
    label: 'NAS / 存储',
    group: '服务器与终端',
    iconClass: 'ti ti-database',
  },
  'camera': {
    color: '#7B61FF',
    bgColor: 'rgba(123,97,255,0.15)',
    borderColor: 'rgba(123,97,255,0.4)',
    label: '网络摄像头',
    group: '服务器与终端',
    iconClass: 'ti ti-camera',
  },

  // ── 安全设备 ───────────────────────────────────────────────
  'ids-ips': {
    color: '#E85F5C',
    bgColor: 'rgba(232,95,92,0.15)',
    borderColor: 'rgba(232,95,92,0.4)',
    label: 'IDS / IPS',
    group: '安全设备',
    iconClass: 'ti ti-eye',
  },
  'vpn': {
    color: '#7B61FF',
    bgColor: 'rgba(123,97,255,0.15)',
    borderColor: 'rgba(123,97,255,0.4)',
    label: 'VPN 网关',
    group: '安全设备',
    iconClass: 'ti ti-lock',
  },
  'waf': {
    color: '#FF7A45',
    bgColor: 'rgba(255,122,69,0.15)',
    borderColor: 'rgba(255,122,69,0.4)',
    label: 'WAF',
    group: '安全设备',
    iconClass: 'ti ti-shield-check',
  },
  'sandbox': {
    color: '#C41D7F',
    bgColor: 'rgba(196,29,127,0.12)',
    borderColor: 'rgba(196,29,127,0.35)',
    label: '沙箱',
    group: '安全设备',
    iconClass: 'ti ti-box',
  },

  // ── 逻辑节点 ───────────────────────────────────────────────
  'internet': {
    color: '#40A9FF',
    bgColor: 'rgba(64,169,255,0.12)',
    borderColor: 'rgba(64,169,255,0.35)',
    label: '互联网 / 云',
    group: '逻辑节点',
    iconClass: 'ti ti-cloud',
  },
  'isp': {
    color: '#909399',
    bgColor: 'rgba(96,98,102,0.12)',
    borderColor: 'rgba(96,98,102,0.3)',
    label: '运营商',
    group: '逻辑节点',
    iconClass: 'ti ti-antenna',
  },
  'datacenter': {
    color: '#4A90D9',
    bgColor: 'rgba(31,78,121,0.18)',
    borderColor: 'rgba(31,78,121,0.4)',
    label: '数据中心',
    group: '逻辑节点',
    iconClass: 'ti ti-building',
  },
  'site': {
    color: '#1D9E75',
    bgColor: 'rgba(29,158,117,0.15)',
    borderColor: 'rgba(29,158,117,0.4)',
    label: '站点 / 办公室',
    group: '逻辑节点',
    iconClass: 'ti ti-home',
  },
  'unknown': {
    color: '#909399',
    bgColor: 'rgba(144,147,153,0.10)',
    borderColor: 'rgba(144,147,153,0.25)',
    label: '未知设备',
    group: '逻辑节点',
    iconClass: 'ti ti-question-mark',
  },
}

// 按分组获取图标列表（用于 IconPicker 组件）
export const DEVICE_ICON_GROUPS = [
  '核心网络设备',
  '服务器与终端',
  '安全设备',
  '逻辑节点',
]

export function getIconConfig(type: string) {
  return DEVICE_TYPE_CONFIG[type] ?? DEVICE_TYPE_CONFIG['unknown']
}


/* ------------------------------------------------------------
   第三步：NetworkIcon.vue 组件完整代码
   文件位置：frontend/src/components/icons/NetworkIcon.vue
   说明：严格按照此代码实现，不得修改颜色和样式
   ------------------------------------------------------------ */

/*
<template>
  <div class="network-icon-wrap" :style="wrapStyle">

    <!-- Tabler 字体图标 -->
    <i v-if="config.iconClass" :class="config.iconClass" :style="iconStyle" aria-hidden="true" />

    <!-- SD-WAN 内联 SVG -->
    <span v-else-if="config.svgInline" v-html="config.svgInline" class="svg-inline" />

    <!-- 右上角状态点 -->
    <span v-if="showStatus" class="status-dot" :style="dotStyle" />

    <!-- 底部标签 -->
    <span v-if="showLabel" class="icon-label" :style="labelStyle">
      {{ label || config.label }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getIconConfig } from '@/constants/deviceIcons'

const props = withDefaults(defineProps<{
  type: string                          // 设备类型，如 'router' / 'firewall'
  status?: 'online' | 'offline' | 'warning' | 'unknown'
  size?: 'sm' | 'md' | 'lg'            // sm=28px  md=48px（默认）  lg=64px
  showLabel?: boolean                   // 是否显示底部名称标签
  showStatus?: boolean                  // 是否显示右上角状态点
  label?: string                        // 自定义标签文字，不传则用 config.label
}>(), {
  status: 'unknown',
  size: 'md',
  showLabel: false,
  showStatus: false,
})

const SIZE_MAP = { sm: 28, md: 48, lg: 64 }
const FONT_MAP = { sm: 14, md: 22, lg: 30 }

const config = computed(() => getIconConfig(props.type))

// 图标盒子样式
const wrapStyle = computed(() => {
  const s = SIZE_MAP[props.size]
  const isOffline = props.status === 'offline'
  return {
    width: `${s}px`,
    height: `${s}px`,
    borderRadius: '10px',
    background: isOffline ? 'rgba(144,147,153,0.10)' : config.value.bgColor,
    border: `1px solid ${isOffline ? 'rgba(144,147,153,0.25)' : config.value.borderColor}`,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    flexShrink: '0',
    opacity: isOffline ? '0.5' : '1',
    filter: isOffline ? 'grayscale(0.8)' : 'none',
    flexDirection: 'column',
    gap: '0',
  }
})

// 字体图标样式
const iconStyle = computed(() => ({
  fontSize: `${FONT_MAP[props.size]}px`,
  color: props.status === 'offline' ? '#909399' : config.value.color,
  lineHeight: '1',
}))

// 状态点颜色
const STATUS_DOT_COLOR = {
  online:  '#67C23A',
  offline: '#F56C6C',
  warning: '#E6A23C',
  unknown: '#909399',
}

const dotStyle = computed(() => ({
  position: 'absolute',
  top: '-3px',
  right: '-3px',
  width: '9px',
  height: '9px',
  borderRadius: '50%',
  background: STATUS_DOT_COLOR[props.status] || '#909399',
  border: '1.5px solid var(--color-background-primary)',
}))

// 标签样式
const labelStyle = computed(() => ({
  display: 'block',
  textAlign: 'center',
  fontSize: '11px',
  color: 'var(--color-text-secondary)',
  marginTop: '6px',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  maxWidth: '80px',
}))
</script>

<style scoped>
.network-icon-wrap { cursor: default; }
.svg-inline { display: flex; align-items: center; justify-content: center; }
.svg-inline svg { display: block; }
.status-dot { pointer-events: none; }
</style>
*/


/* ------------------------------------------------------------
   第四步：IconPicker.vue 组件完整代码
   文件位置：frontend/src/components/icons/IconPicker.vue
   说明：设备台账新增/编辑时选择图标类型
   ------------------------------------------------------------ */

/*
<template>
  <el-popover placement="bottom-start" :width="480" trigger="click">
    <template #reference>
      <div class="picker-trigger">
        <NetworkIcon :type="modelValue || 'unknown'" size="sm" />
        <span class="picker-label">{{ currentConfig.label }}</span>
        <i class="ti ti-chevron-down picker-arrow" aria-hidden="true" />
      </div>
    </template>

    <div class="picker-wrap">
      <!-- 搜索框 -->
      <el-input
        v-model="keyword"
        placeholder="搜索设备类型（路由器、firewall...）"
        prefix-icon="Search"
        clearable
        size="small"
        style="margin-bottom: 12px;"
      />

      <!-- 分组展示 -->
      <div v-for="group in filteredGroups" :key="group.name">
        <div class="picker-group-title">{{ group.name }}</div>
        <div class="picker-grid">
          <div
            v-for="item in group.items"
            :key="item.type"
            class="picker-item"
            :class="{ 'picker-item--active': modelValue === item.type }"
            @click="select(item.type)"
          >
            <NetworkIcon :type="item.type" size="sm" />
            <span class="picker-item-label">{{ item.label }}</span>
          </div>
        </div>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { DEVICE_TYPE_CONFIG, DEVICE_ICON_GROUPS, getIconConfig } from '@/constants/deviceIcons'
import NetworkIcon from './NetworkIcon.vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const keyword = ref('')
const currentConfig = computed(() => getIconConfig(props.modelValue))

// 所有图标按分组整理
const allGroups = DEVICE_ICON_GROUPS.map(groupName => ({
  name: groupName,
  items: Object.entries(DEVICE_TYPE_CONFIG)
    .filter(([, cfg]) => cfg.group === groupName)
    .map(([type, cfg]) => ({ type, label: cfg.label })),
}))

// 关键字过滤
const filteredGroups = computed(() => {
  const kw = keyword.value.toLowerCase()
  if (!kw) return allGroups
  return allGroups.map(group => ({
    ...group,
    items: group.items.filter(item =>
      item.label.toLowerCase().includes(kw) ||
      item.type.toLowerCase().includes(kw)
    ),
  })).filter(group => group.items.length > 0)
})

function select(type: string) {
  emit('update:modelValue', type)
}
</script>

<style scoped>
.picker-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 0.5px solid var(--color-border-tertiary);
  border-radius: var(--border-radius-md);
  cursor: pointer;
  background: var(--color-background-primary);
}
.picker-trigger:hover { border-color: var(--color-border-secondary); }
.picker-label { font-size: 13px; color: var(--color-text-primary); }
.picker-arrow { font-size: 14px; color: var(--color-text-secondary); }

.picker-wrap { max-height: 360px; overflow-y: auto; }
.picker-group-title {
  font-size: 11px;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 10px 0 6px;
  padding-bottom: 4px;
  border-bottom: 0.5px solid var(--color-border-tertiary);
}
.picker-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
  margin-bottom: 4px;
}
.picker-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  border-radius: var(--border-radius-md);
  cursor: pointer;
  border: 0.5px solid transparent;
}
.picker-item:hover { background: var(--color-background-secondary); }
.picker-item--active {
  border-color: var(--color-border-info);
  background: var(--color-background-info);
}
.picker-item-label {
  font-size: 10px;
  color: var(--color-text-secondary);
  text-align: center;
  line-height: 1.2;
  max-width: 56px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
*/


/* ------------------------------------------------------------
   第五步：使用示例
   ------------------------------------------------------------ */

/*
// 1. 在设备列表表格中显示图标（sm尺寸，带状态点）
<NetworkIcon type="firewall" status="warning" size="sm" :show-status="true" />

// 2. 在网络拓扑节点中显示图标（md尺寸，带标签）
<NetworkIcon type="router" status="online" size="md" :show-label="true" label="RT-SHA-01" />

// 3. 在设备编辑表单中使用图标选择器
<IconPicker v-model="form.iconType" />

// 4. 在 G6 拓扑画布中使用（通过 HTML Overlay 或 G6 自定义节点）
// 将 NetworkIcon 渲染为 HTML，通过 G6 的 htmlContent 节点类型嵌入
*/
