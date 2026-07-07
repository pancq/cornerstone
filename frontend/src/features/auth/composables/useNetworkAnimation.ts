import { ref, onMounted, onUnmounted } from 'vue'

type AnimationMode = 'default' | 'username' | 'password' | 'captcha' | 'login-click' | 'login-loading' | 'login-success' | 'login-fail'

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

const NODE_COUNT = 32
const ANIMATION_WIDTH = 600
const ANIMATION_HEIGHT = 800
const COLORS = ['#3b82f6', '#6366f1', '#8b5cf6', '#0ea5e9', '#22d3ee', '#14b8a6']
const PACKET_INTERVAL = 400
const NODE_SPAWN_DELAY = 1000

export function useNetworkAnimation() {
  const mouseX = ref(0)
  const mouseY = ref(0)
  const illustrationRect = ref<DOMRect | null>(null)
  const illustrationRef = ref<HTMLElement | null>(null)
  const animationMode = ref<AnimationMode>('default')
  const hasEntered = ref(false)

  const nodes = ref<NetworkNode[]>([])
  const links = ref<NetworkLink[]>([])
  const dataPackets = ref<DataPacket[]>([])

  let packetId = 0
  let packetInterval: number | null = null

  const initNodes = () => {
    nodes.value = []
    links.value = []

    for (let i = 0; i < NODE_COUNT; i++) {
      nodes.value.push({
        id: i,
        x: Math.random() * 550 + 25,
        y: Math.random() * 780 + 10,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 5 + 3,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        opacity: Math.random() * 0.5 + 0.3,
        pulse: false
      })
    }

    for (let i = 0; i < NODE_COUNT; i++) {
      const connections = Math.floor(Math.random() * 4) + 2
      for (let j = 0; j < connections; j++) {
        const target = Math.floor(Math.random() * NODE_COUNT)
        if (
          target !== i &&
          !links.value.some(
            l =>
              (l.from === i && l.to === target) ||
              (l.from === target && l.to === i)
          )
        ) {
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

    nodes.value.forEach(node => {
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

      if (node.x < node.radius) {
        node.x = node.radius
        node.vx *= -0.6
      }
      if (node.x > ANIMATION_WIDTH - node.radius) {
        node.x = ANIMATION_WIDTH - node.radius
        node.vx *= -0.6
      }
      if (node.y < node.radius) {
        node.y = node.radius
        node.vy *= -0.6
      }
      if (node.y > ANIMATION_HEIGHT - node.radius) {
        node.y = ANIMATION_HEIGHT - node.radius
        node.vy *= -0.6
      }
    })

    links.value.forEach(link => {
      const from = nodes.value[link.from]
      const to = nodes.value[link.to]
      const dx = from.x - to.x
      const dy = from.y - to.y
      const dist = Math.sqrt(dx * dx + dy * dy)

      if (dist < 150) {
        link.opacity = ((150 - dist) / 150) * 0.4
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
      nodes.value.forEach(node => {
        node.pulse = true
        node.opacity = 1
      })
      setTimeout(() => {
        animationMode.value = 'default'
        nodes.value.forEach(node => {
          node.pulse = false
        })
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

  const startAnimation = () => {
    updateIllustrationRect()
    initNodes()
    animate()

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('resize', updateIllustrationRect)

    setTimeout(() => {
      hasEntered.value = true
      packetInterval = window.setInterval(spawnDataPacket, PACKET_INTERVAL)
    }, NODE_SPAWN_DELAY)
  }

  const stopAnimation = () => {
    window.removeEventListener('mousemove', handleMouseMove)
    window.removeEventListener('resize', updateIllustrationRect)
    if (packetInterval) {
      clearInterval(packetInterval)
    }
  }

  onMounted(() => {
    startAnimation()
  })

  onUnmounted(() => {
    stopAnimation()
  })

  return {
    illustrationRef,
    nodes,
    links,
    dataPackets,
    hasEntered,
    animationMode,
    setAnimationMode,
    triggerNodePulse
  }
}