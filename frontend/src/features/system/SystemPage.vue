<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// System 页面现在只做重定向，跳转到用户管理
onMounted(() => {
  router.replace('/system/users')
})
</script>

<template>
  <div></div>
</template>
