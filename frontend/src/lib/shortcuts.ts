/**
 * 全局快捷键注册
 * Ctrl+K / Cmd+K → 打开 GlobalSearch
 */
import { onMounted, onUnmounted } from 'vue'

export function useGlobalShortcut(handler: () => void) {
  function onKeydown(e: KeyboardEvent) {
    // Ctrl+K 或 Cmd+K
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault()
      // 不在 input/textarea 中触发时不拦截
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
      if (tag === 'input' || tag === 'textarea') return
      handler()
    }
    // Esc 关闭（由组件内部自行处理）
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onUnmounted(() => window.removeEventListener('keydown', onKeydown))
}