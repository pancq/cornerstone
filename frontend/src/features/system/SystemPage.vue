<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth'
import { useI18n } from 'vue-i18n'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
const { Setting, User, Connection, Bell, Shield } = ElementPlusIconsVue

const { t } = useI18n()
import UserManagement from './UserManagement.vue'
import SSOSettings from './SSOSettings.vue'
import NotificationSettings from './NotificationSettings.vue'
import SecuritySettings from './SecuritySettings.vue'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const activeTab = ref('users')
const previousHash = ref('')

// 暴露给子组件的方法，用于从外部控制UserManagement的内部Tab
const userManagementRef = ref<InstanceType<typeof UserManagement> | null>(null)

// 处理hash变化的通用方法
function handleHashChange(hash: string) {
  if (['users', 'sso', 'notification', 'security', 'roles'].includes(hash)) {
    if (hash === 'roles') {
      // roles在UserManagement内部
      activeTab.value = 'users'
      nextTick(() => {
        if (userManagementRef.value && 'setActiveInnerTab' in userManagementRef.value) {
          (userManagementRef.value as any).setActiveInnerTab('roles')
        }
      })
    } else {
      // sso, notification, security, users 直接设置对应的Tab
      activeTab.value = hash
    }
  }
}

onMounted(() => {
  // 检查URL的hash部分来设置默认Tab
  if (route.hash) {
    const hash = route.hash.slice(1)
    handleHashChange(hash)
  }
  
  // 监听浏览器的hashchange事件
  window.addEventListener('hashchange', () => {
    const hash = window.location.hash.slice(1)
    handleHashChange(hash)
  })
})

// 监听路由hash变化
watch(() => route.hash, (newHash) => {
  if (newHash && newHash !== previousHash.value) {
    const hash = newHash.slice(1)
    previousHash.value = newHash
    handleHashChange(hash)
  }
}, { immediate: true })

watch(activeTab, (newTab) => {
  // 同步URL hash
  const currentHash = route.hash
  const expectedHash = `#${newTab}`
  if (currentHash !== expectedHash) {
    previousHash.value = expectedHash
    router.replace({ hash: newTab })
  }
})

// 提供给UserManagement调用的方法
function handleRolesClick() {
  activeTab.value = 'users'
  nextTick(() => {
    if (userManagementRef.value && 'setActiveInnerTab' in userManagementRef.value) {
      (userManagementRef.value as any).setActiveInnerTab('roles')
    }
  })
}

// 暴露给父组件
defineExpose({
  handleRolesClick
})
</script>

<template>
  <div class="system-page">
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="card-title">
          <Setting class="el-icon" />
          {{ t('system.settings') }}
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane :label="t('system.userManagement')" name="users">
          <template #label>
            <span class="tab-label">
              <User class="tab-icon" />
              {{ t('system.userManagement') }}
            </span>
          </template>
          <UserManagement 
            ref="userManagementRef"
            v-if="authStore.hasPermission('users', 'read')" 
          />
          <div v-else class="no-permission">
            {{ t('system.noUserPermission') }}
          </div>
        </el-tab-pane>

        <el-tab-pane :label="t('system.ssoSettings')" name="sso">
          <template #label>
            <span class="tab-label">
              <Connection class="tab-icon" />
              {{ t('system.ssoSettings') }}
            </span>
          </template>
          <SSOSettings v-if="authStore.hasPermission('system', 'write')" />
          <div v-else class="no-permission">
            {{ t('system.noSystemPermission') }}
          </div>
        </el-tab-pane>

        <el-tab-pane :label="t('system.notifications')" name="notification">
          <template #label>
            <span class="tab-label">
              <Bell class="tab-icon" />
              {{ t('system.notifications') }}
            </span>
          </template>
          <NotificationSettings v-if="authStore.hasPermission('system', 'write')" />
          <div v-else class="no-permission">
            {{ t('system.noNotificationPermission') }}
          </div>
        </el-tab-pane>

        <el-tab-pane :label="t('system.security')" name="security">
          <template #label>
            <span class="tab-label">
              <Shield class="tab-icon" />
              {{ t('system.security') }}
            </span>
          </template>
          <SecuritySettings v-if="authStore.hasPermission('system', 'write')" />
          <div v-else class="no-permission">
            {{ t('system.noSystemPermission') }}
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.system-page {
  padding: 20px;
}

.table-card {
  border-radius: 8px;
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

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-icon {
  font-size: 16px;
}

.no-permission {
  padding: 40px;
  text-align: center;
}
</style>
