<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Refresh } from '@element-plus/icons-vue'
import type { Rack } from '../../types/domain'

const props = defineProps<{
  racks: Rack[]
  selectedId: number | null
  search: string
}>()

const emit = defineEmits<{
  (e: 'update:search', v: string): void
  (e: 'select', id: number): void
  (e: 'refresh'): void
}>()

const { t } = useI18n()

// 按 room → 分组
const grouped = computed(() => {
  const map = new Map<string, Rack[]>()
  for (const r of props.racks) {
    const k = r.room || t('rack.unassigned')
    if (!map.has(k)) map.set(k, [])
    map.get(k)!.push(r)
  }
  return Array.from(map.entries()).map(([room, items]) => ({
    room,
    items: items.slice().sort((a, b) => (a.rowPosition || 0) - (b.rowPosition || 0) || a.name.localeCompare(b.name)),
  }))
})
</script>

<template>
  <div class="rack-sidebar">
    <div class="sidebar-header">
      <el-input
        :model-value="search"
        @update:model-value="(v: string) => emit('update:search', v)"
        :placeholder="t('rack.navSearchPlaceholder')"
        size="small"
        clearable
        class="sidebar-search"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button :icon="Refresh" size="small" circle @click="emit('refresh')" />
    </div>

    <div v-if="!racks.length" class="sidebar-empty">
      <el-empty :description-size="12" :image-size="50" />
    </div>

    <div v-else class="rack-tree">
      <div v-for="g in grouped" :key="g.room" class="rack-group">
        <div class="rack-group-title">
          <el-icon><Folder /></el-icon>
          <span>{{ g.room }}</span>
          <el-tag size="small" type="info">{{ g.items.length }}</el-tag>
        </div>
        <ul class="rack-group-list">
          <li
            v-for="r in g.items"
            :key="r.id"
            class="rack-item"
            :class="{ active: r.id === selectedId }"
            @click="emit('select', r.id)"
          >
            <span class="rack-item-name" :title="r.name">{{ r.name }}</span>
            <el-tag
              size="small"
              class="rack-item-status"
              :type="r.status === 'active' ? 'success' : r.status === 'alert' ? 'warning' : 'info'"
            >
              {{ r.totalU || 42 }}U
            </el-tag>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { Search, Folder } from '@element-plus/icons-vue'
export default { components: { Search, Folder } }
</script>

<style scoped>
.rack-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 520px;
}
.sidebar-header {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color, #eef0f3);
}
.sidebar-search { flex: 1; }
.sidebar-empty { padding: 20px 0; }

.rack-tree { flex: 1; overflow-y: auto; padding-right: 4px; }
.rack-group + .rack-group { margin-top: 14px; }
.rack-group-title {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary, #6b7280);
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 6px;
}
.rack-group-title .el-tag { margin-left: auto; }

.rack-group-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.rack-item {
  padding: 6px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary, #1f2937);
  transition: background .12s;
}
.rack-item:hover { background: var(--bg-hover, #eef3ff); }
.rack-item.active {
  background: var(--primary-light, #e8f1ff);
  color: var(--primary, #1e40af);
  font-weight: 500;
}
.rack-item-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rack-item-status { flex-shrink: 0; }
</style>
