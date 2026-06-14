import type { App, DirectiveBinding } from 'vue'
import { useAuthStore } from '../../store/auth'

function checkPermission(permission: string | string[]): boolean {
  const authStore = useAuthStore()
  
  if (!permission) return true
  
  if (Array.isArray(permission)) {
    return permission.some(p => authStore.hasPermission(p))
  }
  
  return authStore.hasPermission(permission)
}

export function setupPermissionDirective(app: App) {
  // v-permission 指令 - 无权限时禁用元素
  app.directive('permission', {
    mounted(el: HTMLElement, binding: DirectiveBinding) {
      const hasPerm = checkPermission(binding.value)
      if (!hasPerm) {
        el.setAttribute('disabled', 'disabled')
        el.classList.add('permission-disabled')
        
        // 添加提示
        el.setAttribute('title', '您的角色无此操作权限')
      }
    },
    updated(el: HTMLElement, binding: DirectiveBinding) {
      const hasPerm = checkPermission(binding.value)
      if (!hasPerm) {
        el.setAttribute('disabled', 'disabled')
        el.classList.add('permission-disabled')
        el.setAttribute('title', '您的角色无此操作权限')
      } else {
        el.removeAttribute('disabled')
        el.classList.remove('permission-disabled')
        el.removeAttribute('title')
      }
    }
  })
  
  // v-permission-hide 指令 - 无权限时隐藏元素
  app.directive('permission-hide', {
    mounted(el: HTMLElement, binding: DirectiveBinding) {
      const hasPerm = checkPermission(binding.value)
      if (!hasPerm) {
        el.style.display = 'none'
      }
    },
    updated(el: HTMLElement, binding: DirectiveBinding) {
      const hasPerm = checkPermission(binding.value)
      el.style.display = hasPerm ? '' : 'none'
    }
  })
}
