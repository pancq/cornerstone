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

interface Props {
  /** 设备类型，如 'router' / 'firewall' */
  type: string
  /** 状态 */
  status?: 'online' | 'offline' | 'warning' | 'unknown'
  /** 尺寸：sm=28px  md=48px（默认）  lg=64px */
  size?: 'sm' | 'md' | 'lg'
  /** 是否显示底部名称标签 */
  showLabel?: boolean
  /** 是否显示右上角状态点 */
  showStatus?: boolean
  /** 自定义标签文字，不传则用 config.label */
  label?: string
}

const props = withDefaults(defineProps<Props>(), {
  status: 'unknown',
  size: 'md',
  showLabel: false,
  showStatus: false,
})

const SIZE_MAP: Record<string, number> = { sm: 28, md: 48, lg: 64 }
const FONT_MAP: Record<string, number> = { sm: 14, md: 22, lg: 30 }

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
    display: 'inline-flex' as const,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
    position: 'relative' as const,
    flexShrink: '0',
    opacity: isOffline ? '0.5' : '1',
    filter: isOffline ? 'grayscale(0.8)' : 'none',
    flexDirection: 'column' as const,
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
const STATUS_DOT_COLOR: Record<string, string> = {
  online: '#67C23A',
  offline: '#F56C6C',
  warning: '#E6A23C',
  unknown: '#909399',
}

const dotStyle = computed(() => ({
  position: 'absolute' as const,
  top: '-3px',
  right: '-3px',
  width: '9px',
  height: '9px',
  borderRadius: '50%',
  background: STATUS_DOT_COLOR[props.status] || '#909399',
  border: '1.5px solid #fff',
}))

// 标签样式
const labelStyle = computed(() => ({
  display: 'block' as const,
  textAlign: 'center' as const,
  fontSize: '11px',
  color: '#909399',
  marginTop: '6px',
  whiteSpace: 'nowrap' as const,
  overflow: 'hidden' as const,
  textOverflow: 'ellipsis' as const,
  maxWidth: '80px',
}))
</script>

<style scoped>
.network-icon-wrap {
  cursor: default;
}
.svg-inline {
  display: flex;
  align-items: center;
  justify-content: center;
}
.svg-inline svg {
  display: block;
}
.status-dot {
  pointer-events: none;
}
</style>