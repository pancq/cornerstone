<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import SSOSettings from './SSOSettings.vue'
import LDAPSettings from './LDAPSettings.vue'

const { t } = useI18n()
const activeTab = ref('sso')
</script>

<template>
  <div class="sso-page">
    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="t('system.ssoTab')" name="sso">
          <SSOSettings />
        </el-tab-pane>
        <el-tab-pane :label="t('system.ldapTab')" name="ldap">
          <LDAPSettings />
        </el-tab-pane>
        <el-tab-pane :label="t('system.dingtalkTab')" name="dingtalk">
          <div class="coming-soon">
            <el-empty :description="t('system.dingtalkComingSoon')" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.sso-page {
  padding: 20px;
}

.coming-soon {
  padding: 40px 0;
}
</style>
