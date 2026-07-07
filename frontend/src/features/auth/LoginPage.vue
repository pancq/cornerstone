<script setup lang="ts">
import { onMounted } from 'vue'
import { useBrandStore } from '../../store/brand'
import NetworkIllustration from './components/NetworkIllustration.vue'
import LoginForm from './components/LoginForm.vue'

const brandStore = useBrandStore()

onMounted(async () => {
  await brandStore.loadBrand()
})
</script>

<template>
  <div class="login-page">
    <div class="background-effects">
      <div class="floating-orb orb-1"></div>
      <div class="floating-orb orb-2"></div>
      <div class="floating-orb orb-3"></div>
      <div class="grid-pattern"></div>
      <div class="noise-overlay"></div>
    </div>

    <NetworkIllustration />
    <LoginForm />
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: flex;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
}

.background-effects {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.floating-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.35;
  animation: floatOrb 28s ease-in-out infinite;
}

.orb-1 {
  width: 550px;
  height: 550px;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  top: -200px;
  left: -180px;
  animation-delay: 0s;
}

.orb-2 {
  width: 450px;
  height: 450px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  bottom: -120px;
  right: 10%;
  animation-delay: -10s;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
  top: 45%;
  right: -150px;
  animation-delay: -18s;
}

@keyframes floatOrb {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(60px, -50px) scale(1.1);
  }
  50% {
    transform: translate(-40px, 50px) scale(0.9);
  }
  75% {
    transform: translate(-20px, -40px) scale(1.05);
  }
}

.grid-pattern {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
  background-size: 50px 50px;
}

.noise-overlay {
  position: absolute;
  inset: 0;
  opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}
</style>