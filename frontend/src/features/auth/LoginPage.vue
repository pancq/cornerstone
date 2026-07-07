<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../../store/auth'
import { useBrandStore } from '../../store/brand'
import { useRouter } from 'vue-router'
import api from '../../api/axios'

const { t } = useI18n()
const authStore = useAuthStore()
const brandStore = useBrandStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const captchaCode = ref('')
const captchaId = ref('')
const captchaImageUrl = ref('')
const loading = ref(false)
const ssoLoading = ref(false)
const error = ref('')
const showPassword = ref(false)
const captchaLoading = ref(false)
const ssoConfigLoaded = ref(false)
const ldapEnabled = ref(false)
const ldapConfigLoaded = ref(false)

const loginMode = ref<'local' | 'ldap'>('local')

const isTypingUsername = ref(false)
const isTypingPassword = ref(false)
const companyLogo = ref<string>('')

// ============================================
// 科技感网络节点动画系统
// ============================================

const mouseX = ref(0)
const mouseY = ref(0)
const illustrationRect = ref<DOMRect | null>(null)
const illustrationRef = ref<HTMLElement | null>(null)

type AnimationMode = 'default' | 'username' | 'password' | 'captcha' | 'login-click' | 'login-loading' | 'login-success' | 'login-fail'
const animationMode = ref<AnimationMode>('default')
const hasEntered = ref(false)

interface NetworkNode {
  id: number
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  color: string
  opacity: number
  pulse: boolean
}

interface NetworkLink {
  from: number
  to: number
  opacity: number
}

interface DataPacket {
  id: number
  linkIndex: number
  progress: number
  color: string
}

const nodes = ref<NetworkNode[]>([])
const links = ref<NetworkLink[]>([])
const dataPackets = ref<DataPacket[]>([])

const nodeCount = 18
let packetId = 0
const colors = ['#3b82f6', '#6366f1', '#8b5cf6', '#0ea5e9', '#22d3ee', '#14b8a6']

const initNodes = () => {
  nodes.value = []
  links.value = []
  
  for (let i = 0; i < nodeCount; i++) {
    nodes.value.push({
      id: i,
      x: Math.random() * 400 + 50,
      y: Math.random() * 300 + 50,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      radius: Math.random() * 6 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      opacity: Math.random() * 0.5 + 0.3,
      pulse: false
    })
  }
  
  for (let i = 0; i < nodeCount; i++) {
    const connections = Math.floor(Math.random() * 3) + 1
    for (let j = 0; j < connections; j++) {
      const target = Math.floor(Math.random() * nodeCount)
      if (target !== i && !links.value.some(l => (l.from === i && l.to === target) || (l.from === target && l.to === i))) {
        links.value.push({
          from: i,
          to: target,
          opacity: Math.random() * 0.3 + 0.1
        })
      }
    }
  }
}

const animate = () => {
  const rect = illustrationRect.value
  if (!rect) return
  
  const width = 500
  const height = 400
  
  nodes.value.forEach((node) => {
    let dx = mouseX.value - (rect.left + node.x)
    let dy = mouseY.value - (rect.top + node.y)
    const dist = Math.sqrt(dx * dx + dy * dy)
    
    if (dist < 200) {
      const force = (200 - dist) / 200
      dx /= dist
      dy /= dist
      node.vx -= dx * force * 0.08
      node.vy -= dy * force * 0.08
    }
    
    if (animationMode.value === 'login-success') {
      node.vx *= 0.95
      node.vy *= 0.95
    }
    
    node.x += node.vx
    node.y += node.vy
    
    node.vx *= 0.98
    node.vy *= 0.98
    
    if (node.x < node.radius) { node.x = node.radius; node.vx *= -0.6 }
    if (node.x > width - node.radius) { node.x = width - node.radius; node.vx *= -0.6 }
    if (node.y < node.radius) { node.y = node.radius; node.vy *= -0.6 }
    if (node.y > height - node.radius) { node.y = height - node.radius; node.vy *= -0.6 }
  })
  
  links.value.forEach((link) => {
    const from = nodes.value[link.from]
    const to = nodes.value[link.to]
    const dx = from.x - to.x
    const dy = from.y - to.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    
    if (dist < 150) {
      link.opacity = (150 - dist) / 150 * 0.4
    } else {
      link.opacity = 0
    }
  })
  
  dataPackets.value.forEach((packet, index) => {
    packet.progress += 0.015
    
    if (packet.progress >= 1) {
      dataPackets.value.splice(index, 1)
    }
  })
  
  requestAnimationFrame(animate)
}

const spawnDataPacket = () => {
  if (links.value.length === 0) return
  
  const activeLinks = links.value.filter(l => l.opacity > 0.1)
  if (activeLinks.length === 0) return
  
  const linkIndex = activeLinks[Math.floor(Math.random() * activeLinks.length)]
  const originalIndex = links.value.indexOf(linkIndex)
  
  if (originalIndex === -1) return
  
  const fromNode = nodes.value[linkIndex.from]
  dataPackets.value.push({
    id: packetId++,
    linkIndex: originalIndex,
    progress: 0,
    color: fromNode.color
  })
}

let packetInterval: number | null = null

const handleMouseMove = (e: MouseEvent) => {
  mouseX.value = e.clientX
  mouseY.value = e.clientY
}

const updateIllustrationRect = () => {
  if (illustrationRef.value) {
    illustrationRect.value = illustrationRef.value.getBoundingClientRect()
  }
}

const setAnimationMode = (mode: AnimationMode) => {
  animationMode.value = mode
  
  if (mode === 'login-success') {
    nodes.value.forEach((node) => {
      node.pulse = true
      node.opacity = 1
    })
    setTimeout(() => {
      animationMode.value = 'default'
      nodes.value.forEach((node) => { node.pulse = false })
    }, 1000)
  } else if (mode === 'login-fail') {
    setTimeout(() => {
      animationMode.value = 'default'
    }, 800)
  }
}

const triggerNodePulse = () => {
  const randomNode = nodes.value[Math.floor(Math.random() * nodes.value.length)]
  randomNode.pulse = true
  setTimeout(() => {
    randomNode.pulse = false
  }, 400)
}

const loadLogo = async () => {
  try {
    const response = await api.get('/settings/logo')
    if (response.data && response.data.value) {
      companyLogo.value = `data:image/png;base64,${response.data.value}`
    }
  } catch (error) {
    console.warn('加载Logo失败，使用默认Logo:', error)
  }
}

const hasSSO = computed(() => {
  return authStore.ssoConfig?.enabled && authStore.ssoConfig?.has_oauth2
})

const showLdapTab = computed(() => {
  return ldapEnabled.value && ldapConfigLoaded.value
})

async function refreshCaptcha() {
    captchaLoading.value = true
    try {
        const response = await fetch('/api/v1/auth/captcha')
        const newCaptchaId = response.headers.get('X-Captcha-ID')
        if (newCaptchaId) {
            captchaId.value = newCaptchaId
            const blob = await response.blob()
            captchaImageUrl.value = URL.createObjectURL(blob)
        }
    } catch (err) {
        console.error('获取验证码失败:', err)
    } finally {
        captchaLoading.value = false
    }
}

async function handleLogin() {
    if (!username.value) {
        error.value = t('login.usernameRequired')
        return
    }
    if (!password.value) {
        error.value = t('login.passwordRequired')
        return
    }
    if (!captchaCode.value) {
        error.value = t('login.captchaRequired')
        return
    }

    loading.value = true
    error.value = ''
    setAnimationMode('login-loading')

    try {
        const success = await authStore.loginWithCaptcha(
            username.value, 
            password.value, 
            captchaId.value, 
            captchaCode.value
        )
        if (success) {
            setAnimationMode('login-success')
            setTimeout(() => {
                router.push('/')
            }, 500)
        } else {
            setAnimationMode('login-fail')
            error.value = t('login.invalidCredentials')
            refreshCaptcha()
        }
    } catch (err: any) {
        setAnimationMode('login-fail')
        if (err.response?.status === 400) {
            error.value = t('login.captchaError')
            refreshCaptcha()
        } else {
            error.value = t('login.loginFailed')
        }
    } finally {
        loading.value = false
    }
}

async function handleSSOLogin() {
    ssoLoading.value = true
    try {
        const result = await authStore.getSSOAuthorizeUrl()
        if (result.authorize_url) {
            window.location.href = result.authorize_url
        }
    } catch (err: any) {
        error.value = t('login.ssoLoginFailed')
    } finally {
        ssoLoading.value = false
    }
}

async function handleLDAPLogin() {
    if (!username.value) {
        error.value = t('login.usernameRequired')
        return
    }
    if (!password.value) {
        error.value = t('login.passwordRequired')
        return
    }

    loading.value = true
    error.value = ''
    setAnimationMode('login-loading')

    try {
        const response = await fetch('/api/v1/auth/ldap/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username.value,
                password: password.value
            })
        })
        
        const data = await response.json()
        
        if (response.ok) {
            localStorage.setItem('access_token', data.access_token)
            localStorage.setItem('refresh_token', data.refresh_token)
            setAnimationMode('login-success')
            setTimeout(() => {
                router.push('/')
            }, 500)
        } else {
            setAnimationMode('login-fail')
            error.value = data.detail || t('login.loginFailed')
        }
    } catch (err: any) {
        setAnimationMode('login-fail')
        error.value = t('login.loginFailed')
    } finally {
        loading.value = false
    }
}

async function fetchLDAPConfig() {
    try {
        const response = await fetch('/api/v1/auth/ldap/enabled')
        const data = await response.json()
        ldapEnabled.value = data.enabled
    } catch (err) {
        console.error('获取LDAP配置失败:', err)
    } finally {
        ldapConfigLoaded.value = true
    }
}

onMounted(async () => {
    await brandStore.loadBrand()
    refreshCaptcha()
    await authStore.fetchSSOConfig()
    ssoConfigLoaded.value = true
    await fetchLDAPConfig()
    await loadLogo()
    
    updateIllustrationRect()
    initNodes()
    animate()
    
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('resize', updateIllustrationRect)
    
    setTimeout(() => {
        hasEntered.value = true
        packetInterval = window.setInterval(spawnDataPacket, 800)
    }, 1000)
    
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    if (code) {
        loading.value = true
        try {
            const result = await authStore.ssoCallback(code)
            if (result.success) {
                router.push('/')
            } else {
                error.value = result.message || t('login.loginFailed')
            }
        } catch (err: any) {
            error.value = t('login.ssoLoginFailed')
        } finally {
            loading.value = false
            urlParams.delete('code')
            window.history.replaceState({}, document.title, window.location.pathname)
        }
    }
})

onUnmounted(() => {
    window.removeEventListener('mousemove', handleMouseMove)
    window.removeEventListener('resize', updateIllustrationRect)
    if (packetInterval) {
        clearInterval(packetInterval)
    }
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

        <div class="login-illustration" ref="illustrationRef">
            <div class="illustration-content">
                <div class="logo-area">
                    <div v-if="companyLogo" class="logo-icon">
                        <img :src="companyLogo" alt="Logo" class="custom-logo-image" />
                    </div>
                    <div v-else class="logo-icon">
                        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M24 4L4 20v24l20 16 20-16V20L24 4z" fill="url(#logoGradient)"/>
                            <path d="M24 10L8 22v16l16 10 16-10V22L24 10z" fill="white" opacity="0.95"/>
                            <defs>
                                <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" style="stop-color:#3b82f6"/>
                                    <stop offset="100%" style="stop-color:#8b5cf6"/>
                                </linearGradient>
                            </defs>
                        </svg>
                    </div>
                    <span class="logo-text">{{ brandStore.brandNameZh }}&nbsp;&nbsp;{{ brandStore.brandNameEn }}</span>
                </div>
                
                <div class="network-container" :class="{ 'entered': hasEntered, 'login-success': animationMode === 'login-success', 'login-fail': animationMode === 'login-fail' }">
                    <svg viewBox="0 0 500 400" class="network-svg">
                        <defs>
                            <filter id="glow">
                                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                                <feMerge>
                                    <feMergeNode in="coloredBlur"/>
                                    <feMergeNode in="SourceGraphic"/>
                                </feMerge>
                            </filter>
                            <radialGradient id="nodeGradient" cx="30%" cy="30%">
                                <stop offset="0%" stop-color="white" stop-opacity="0.8"/>
                                <stop offset="100%" stop-color="white" stop-opacity="0"/>
                            </radialGradient>
                        </defs>
                        <g class="links">
                            <line
                                v-for="(link, index) in links"
                                :key="'link-' + index"
                                :x1="nodes[link.from]?.x || 0"
                                :y1="nodes[link.from]?.y || 0"
                                :x2="nodes[link.to]?.x || 0"
                                :y2="nodes[link.to]?.y || 0"
                                :stroke="nodes[link.from]?.color || '#3b82f6'"
                                :stroke-opacity="link.opacity"
                                stroke-width="1"
                                class="link-line"
                            />
                        </g>
                        <g class="data-packets">
                            <g v-for="packet in dataPackets" :key="'packet-' + packet.id">
                                <circle
                                    :cx="(nodes[links[packet.linkIndex]?.from]?.x || 0) + ((nodes[links[packet.linkIndex]?.to]?.x || 0) - (nodes[links[packet.linkIndex]?.from]?.x || 0)) * packet.progress"
                                    :cy="(nodes[links[packet.linkIndex]?.from]?.y || 0) + ((nodes[links[packet.linkIndex]?.to]?.y || 0) - (nodes[links[packet.linkIndex]?.from]?.y || 0)) * packet.progress"
                                    r="4"
                                    :fill="packet.color"
                                    filter="url(#glow)"
                                    class="data-packet"
                                />
                                <circle
                                    :cx="(nodes[links[packet.linkIndex]?.from]?.x || 0) + ((nodes[links[packet.linkIndex]?.to]?.x || 0) - (nodes[links[packet.linkIndex]?.from]?.x || 0)) * packet.progress"
                                    :cy="(nodes[links[packet.linkIndex]?.from]?.y || 0) + ((nodes[links[packet.linkIndex]?.to]?.y || 0) - (nodes[links[packet.linkIndex]?.from]?.y || 0)) * packet.progress"
                                    r="2"
                                    fill="white"
                                    class="data-packet-core"
                                />
                            </g>
                        </g>
                        <g class="nodes">
                            <g v-for="node in nodes" :key="'node-' + node.id" class="node-group">
                                <circle
                                    :cx="node.x"
                                    :cy="node.y"
                                    :r="node.radius * 2.5"
                                    :fill="node.color"
                                    :opacity="node.pulse ? 0.3 : 0.1"
                                    class="node-glow"
                                />
                                <circle
                                    :cx="node.x"
                                    :cy="node.y"
                                    :r="node.radius"
                                    :fill="node.color"
                                    :opacity="node.opacity"
                                    :filter="node.pulse ? 'url(#glow)' : ''"
                                    class="node-core"
                                    :class="{ 'pulsing': node.pulse }"
                                />
                                <circle
                                    :cx="node.x"
                                    :cy="node.y"
                                    :r="node.radius * 0.4"
                                    fill="white"
                                    :opacity="node.opacity"
                                    class="node-center"
                                />
                            </g>
                        </g>
                    </svg>
                </div>
                
                <div class="slogan">
                    <h2>{{ t('login.leftTitle') }}</h2>
                    <p>{{ t('login.leftSubtitle') }}</p>
                </div>
            </div>
        </div>

        <div class="login-form-container">
            <div class="login-box">

                <div class="login-header">
                    <div class="header-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M12 15v2m-6 4h12a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2zm10-10V7a4 4 0 0 0-8 0v4h8z"/>
                        </svg>
                    </div>
                    <h2>{{ t('login.title') }}</h2>
                    <p>{{ t('login.rightSubtitle') }}</p>
                </div>

                <div v-if="showLdapTab" class="login-tabs">
                    <button 
                        class="tab-btn" 
                        :class="{ active: loginMode === 'local' }"
                        @click="loginMode = 'local'; refreshCaptcha()"
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M12 15v2m-6 4h12a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2zm10-10V7a4 4 0 0 0-8 0v4h8z"/>
                        </svg>
                        {{ t('login.localLogin') }}
                    </button>
                    <button 
                        class="tab-btn" 
                        :class="{ active: loginMode === 'ldap' }"
                        @click="loginMode = 'ldap'"
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                            <circle cx="9" cy="7" r="4"/>
                            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                        </svg>
                        {{ t('login.ldapLogin') }}
                    </button>
                </div>

                <div class="login-form">
                    <Transition name="fade-slide">
                        <div v-if="error" class="error-message">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                            </svg>
                            <span>{{ error }}</span>
                        </div>
                    </Transition>

                    <div class="form-group">
                        <label class="form-label">
                            <span class="label-text">{{ t('login.username') }}</span>
                            <span class="label-required">*</span>
                        </label>
                        <div class="input-wrapper">
                            <span class="input-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                                    <circle cx="12" cy="7" r="4"/>
                                </svg>
                            </span>
                            <input 
                                v-model="username" 
                                type="text" 
                                :placeholder="t('login.username')"
                                class="form-input"
                                @focus="isTypingUsername = true; setAnimationMode('username')"
                                @blur="isTypingUsername = false; setAnimationMode('default')"
                                @input="triggerNodePulse()"
                            />
                            <span class="input-focus-ring"></span>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">
                            <span class="label-text">{{ t('login.password') }}</span>
                            <span class="label-required">*</span>
                        </label>
                        <div class="input-wrapper">
                            <span class="input-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                                </svg>
                            </span>
                            <input 
                                v-model="password" 
                                :type="showPassword ? 'text' : 'password'" 
                                :placeholder="t('login.password')"
                                class="form-input"
                                @focus="isTypingPassword = true; setAnimationMode('password')"
                                @blur="isTypingPassword = false; setAnimationMode('default')"
                                @input="triggerNodePulse()"
                                @keyup.enter="handleLogin"
                            />
                            <span 
                                class="input-suffix password-toggle" 
                                @click="showPassword = !showPassword; isTypingPassword ? setAnimationMode('password') : null"
                            >
                                <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
                                    <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                                </svg>
                                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-5.94 12.06"/>
                                    <line x1="1" y1="1" x2="23" y2="23"/>
                                </svg>
                            </span>
                            <span class="input-focus-ring"></span>
                        </div>
                    </div>

                    <div v-if="loginMode === 'local'" class="form-group">
                        <label class="form-label">
                            <span class="label-text">{{ t('login.captcha') }}</span>
                            <span class="label-required">*</span>
                        </label>
                        <div class="captcha-row">
                            <div class="input-wrapper captcha-input">
                                <input 
                                    v-model="captchaCode" 
                                    type="text" 
                                    :placeholder="t('login.captchaPlaceholder')"
                                    class="form-input"
                                    @focus="setAnimationMode('captcha')"
                                    @blur="setAnimationMode('default')"
                                    @input="triggerNodePulse()"
                                    @keyup.enter="handleLogin"
                                />
                                <span class="input-focus-ring"></span>
                            </div>
                            <div 
                                class="captcha-image-wrapper" 
                                @click="refreshCaptcha"
                                :title="t('login.captchaExpired')"
                            >
                                <img 
                                    v-if="captchaImageUrl" 
                                    :src="captchaImageUrl" 
                                    :alt="t('login.captcha')" 
                                    class="captcha-image"
                                />
                                <div v-else class="captcha-loading">
                                    <svg class="loading-spinner" viewBox="0 0 24 24">
                                        <circle class="path" cx="12" cy="12" r="10" fill="none" stroke-width="2"/>
                                    </svg>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-group remember-me">
                        <label class="checkbox-label">
                            <input type="checkbox" class="checkbox" />
                            <span class="checkbox-custom">
                                <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3">
                                    <path d="M5 13l4 4L19 7"/>
                                </svg>
                            </span>
                            <span class="checkbox-text">{{ t('login.rememberMe') }}</span>
                        </label>
                    </div>

                    <button 
                        type="button" 
                        class="login-btn" 
                        :class="{ 'btn-loading': loading }"
                        :disabled="loading"
                        @click="setAnimationMode('login-click'); loginMode === 'local' ? handleLogin() : handleLDAPLogin()"
                    >
                        <span v-if="loading" class="btn-loader">
                            <svg class="loading-spinner" viewBox="0 0 24 24">
                                <circle class="path" cx="12" cy="12" r="10" fill="none" stroke-width="2"/>
                            </svg>
                        </span>
                        <span v-else>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 16l-4-4m0 0L7 10m4 6l4-4m-4 6l4-4"/>
                            </svg>
                            {{ loginMode === 'local' ? t('login.loginButton') : t('login.ldapLoginButton') }}
                        </span>
                    </button>

                    <template v-if="hasSSO">
                        <div class="login-divider">
                            <span class="divider-line"></span>
                            <span class="divider-text">{{ t('login.or') }}</span>
                            <span class="divider-line"></span>
                        </div>
                        <button 
                            type="button" 
                            class="sso-login-btn" 
                            :class="{ 'btn-loading': ssoLoading }"
                            :disabled="ssoLoading"
                            @click="handleSSOLogin"
                        >
                            <svg class="sso-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                            </svg>
                            <span>{{ ssoLoading ? t('common.loading') : t('login.ssoLogin') }}</span>
                        </button>
                    </template>
                </div>
                
            </div>
        </div>
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
  0%, 100% {
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
  background-image: 
    linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  background-size: 50px 50px;
}

.noise-overlay {
  position: absolute;
  inset: 0;
  opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}

.login-illustration {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  backdrop-filter: none;
  border-right: none;
}

.illustration-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 0;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}

.logo-icon {
  background: transparent;
  border-radius: 12px;
  overflow: hidden;
}

.logo-icon svg {
  width: 58px;
  height: 58px;
  filter: drop-shadow(0 10px 28px rgba(59, 130, 246, 0.35));
  animation: logoFloat 6s ease-in-out infinite;
}

.custom-logo-image {
  max-width: 80px;
  max-height: 58px;
  width: auto;
  height: auto;
  object-fit: contain;
  filter: drop-shadow(0 10px 28px rgba(59, 130, 246, 0.35));
  animation: logoFloat 6s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  25% {
    transform: translateY(-8px) rotate(1.5deg);
  }
  50% {
    transform: translateY(0) rotate(0deg);
  }
  75% {
    transform: translateY(-4px) rotate(-1.5deg);
  }
}

.logo-text {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 1.5px;
  background: linear-gradient(135deg, #f8fafc 0%, #cbd5e1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
}

/* ============================================
   科技感网络节点动画
   ============================================ */

.network-container {
  position: relative;
  width: 500px;
  height: 300px;
  opacity: 0;
  transform: scale(0.95);
  transition: all 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}

.network-container.entered {
  opacity: 1;
  transform: scale(1);
}

.network-container.login-success {
  animation: networkSuccess 0.6s ease-out;
}

.network-container.login-fail {
  animation: networkFail 0.5s ease-out;
}

@keyframes networkSuccess {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes networkFail {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

.network-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
  background: transparent;
}

.link-line {
  transition: opacity 0.3s ease;
}

.node-group {
  transition: transform 0.15s ease;
}

.node-glow {
  transition: r 0.3s ease, opacity 0.3s ease;
}

.node-core {
  transition: r 0.3s ease, opacity 0.3s ease;
}

.node-core.pulsing {
  animation: nodePulse 0.4s ease-out;
}

.node-center {
  transition: opacity 0.3s ease;
}

.data-packet {
  transition: r 0.1s ease;
}

.data-packet-core {
  transition: r 0.1s ease;
}

@keyframes nodePulse {
  0%, 100% { r: var(--original-radius, 5); }
  50% { r: calc(var(--original-radius, 5) * 1.5); }
}

/* ============================================
   标语样式
   ============================================ */

.slogan {
  text-align: center;
  animation: sloganFadeIn 1s ease-out 0.5s both;
}

@keyframes sloganFadeIn {
  from {
    opacity: 0;
    transform: translateY(25px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slogan h2 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 4px 20px rgba(59, 130, 246, 0.25);
}

.slogan p {
  font-size: 14px;
  opacity: 0.85;
  letter-spacing: 1.5px;
  color: #94a3b8;
}

/* ============================================
   右侧登录表单区域
   ============================================ */

.login-form-container {
  width: 520px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 50px 20px;
  padding-left: 20px;
  background: rgba(255, 255, 255, 0.015);
  backdrop-filter: blur(20px);
}

.login-box {
  width: 100%;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 20px;
  padding: 48px;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.04);
  animation: loginBoxSlideIn 0.8s cubic-bezier(0.4, 0, 0.2, 1) 0.3s both;
}

@keyframes loginBoxSlideIn {
  from {
    opacity: 0;
    transform: translateX(40px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 42px;
}

.header-icon {
  width: 58px;
  height: 58px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  border-radius: 18px;
  color: white;
  font-size: 26px;
  box-shadow: 0 10px 28px rgba(59, 130, 246, 0.35);
  animation: headerIconPulse 3.5s ease-in-out infinite;
}

@keyframes headerIconPulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 10px 28px rgba(59, 130, 246, 0.35);
  }
  50% {
    transform: scale(1.04);
    box-shadow: 0 14px 36px rgba(59, 130, 246, 0.45);
  }
}

.header-icon svg {
  width: 28px;
  height: 28px;
}

.login-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 10px;
  letter-spacing: 0.5px;
}

.login-header p {
  font-size: 13px;
  color: #64748b;
}

.login-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 28px;
  padding: 6px;
  background: #f8fafc;
  border-radius: 12px;
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-btn:hover {
  background: #f1f5f9;
  color: #334155;
}

.tab-btn.active {
  background: white;
  color: #3b82f6;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.tab-btn svg {
  width: 18px;
  height: 18px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #dc2626;
  background: #fef2f2;
  border-radius: 12px;
  padding: 14px 18px;
  font-size: 13px;
  border: 1px solid #fecaca;
}

.error-message svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.label-text {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.label-required {
  color: #ef4444;
  font-weight: 700;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  width: 20px;
  height: 20px;
  color: #94a3b8;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-focus-ring {
  position: absolute;
  inset: -2px;
  border-radius: 12px;
  border: 2px solid transparent;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-input:focus + .input-focus-ring {
  border-color: #3b82f6;
  box-shadow: 0 0 0 5px rgba(59, 130, 246, 0.08);
}

.form-input {
  width: 100%;
  height: 48px;
  padding: 0 16px 0 50px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #fafbfc;
  color: #1e293b;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
  box-shadow: 
    0 0 0 3px rgba(59, 130, 246, 0.08),
    0 3px 12px rgba(0, 0, 0, 0.05);
}

.form-input:focus ~ .input-icon {
  color: #3b82f6;
  transform: scale(1.08);
}

.form-input::placeholder {
  color: #94a3b8;
}

.input-suffix {
  position: absolute;
  right: 16px;
  width: 22px;
  height: 22px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-suffix:hover {
  color: #3b82f6;
  transform: scale(1.12);
}

.password-toggle svg {
  width: 20px;
  height: 20px;
}

.captcha-row {
  display: flex;
  gap: 14px;
}

.captcha-input {
  flex: 1;
}

.captcha-image-wrapper {
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
}

.captcha-image-wrapper:hover {
  transform: scale(1.02);
  box-shadow: 0 5px 16px rgba(0, 0, 0, 0.12);
}

.captcha-image {
  width: 130px;
  height: 48px;
  object-fit: cover;
}

.captcha-loading {
  width: 130px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafbfc;
  border-radius: 12px;
}

.loading-spinner {
  width: 22px;
  height: 22px;
}

.loading-spinner .path {
  stroke: #3b82f6;
  stroke-linecap: round;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.remember-me {
  flex-direction: row;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 13px;
  color: #64748b;
  transition: color 0.2s;
}

.checkbox-label:hover {
  color: #334155;
}

.checkbox {
  display: none;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid #cbd5e1;
  border-radius: 7px;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox:checked + .checkbox-custom {
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  border-color: #3b82f6;
  transform: scale(1.05);
  box-shadow: 0 5px 16px rgba(59, 130, 246, 0.35);
}

.checkbox-custom svg {
  width: 12px;
  height: 12px;
  opacity: 0;
  transition: opacity 0.3s;
}

.checkbox:checked + .checkbox-custom svg {
  opacity: 1;
}

.checkbox-text {
  user-select: none;
}

.login-btn {
  height: 52px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 5px 18px rgba(59, 130, 246, 0.35);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(59, 130, 246, 0.45);
}

.login-btn:active:not(:disabled) {
  transform: translateY(-1px);
}

.login-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
}

.login-btn svg {
  width: 18px;
  height: 18px;
}

.btn-loader {
  display: flex;
  align-items: center;
}

.login-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 10px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
}

.divider-text {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

.sso-login-btn {
  height: 52px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  background: white;
  color: #475569;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.sso-login-btn:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.15);
}

.sso-login-btn:active:not(:disabled) {
  transform: translateY(-1px);
}

.sso-login-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
}

.sso-icon {
  width: 20px;
  height: 20px;
}

@media (max-width: 1024px) {
  .login-illustration {
    display: none;
  }
  
  .login-form-container {
    width: 100%;
    justify-content: center;
  }
}
</style>
