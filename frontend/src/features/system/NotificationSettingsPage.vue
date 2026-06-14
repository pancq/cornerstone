<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import NotificationSettings from './NotificationSettings.vue'

const { t } = useI18n()
</script>

<template>
  <div class="notification-page">
    <el-card shadow="never">
      <template #header>
        <div class="card-title">
          <el-icon><Bell /></el-icon>
          {{ t('system.notifications') }}
        </div>
      </template>
      <NotificationSettings />
    </el-card>
  </div>
</template>

<script lang="ts">
import { Bell } from '@element-plus/icons-vue'
</script>

<style scoped>
.notification-page {
  padding: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.card-title .el-icon {
  color: #1890ff;
}
</style>
