/**
 * 菜单 ↔ 路由权限一致性静态断言
 *
 * 此测试锁定"菜单配置与路由配置权限字符串必须一致"这一不变量。
 * 文档记录 Tessa 实测发现 /system/users 菜单(system:admin) vs 路由(system:read) 不一致。
 * 此测试确保未来不会再出现类似漂移。
 */
import { describe, it, expect } from 'vitest'
import { menuConfig, extractMenuRoutePermissions } from './config/menuConfig'
import { extractRoutePermissions } from './app/router'

describe('菜单 ↔ 路由 权限一致性', () => {
  const menuPerms = extractMenuRoutePermissions()
  const routePerms = extractRoutePermissions()

  it('所有菜单项的 path 在路由中存在', () => {
    const menuPaths = new Set(menuPerms.keys())
    const routePaths = new Set(routePerms.keys())

    const missingInRoutes: string[] = []
    for (const path of menuPaths) {
      // 通配符路由（含 :）用基础路径匹配
      const basePath = path.split('/:')[0]
      if (!routePaths.has(path) && !routePaths.has(basePath)) {
        missingInRoutes.push(path)
      }
    }

    expect(missingInRoutes, `菜单项在路由中缺失: ${missingInRoutes.join(', ')}`).toEqual([])
  })

  it('菜单项与对应路由的 permission 完全一致', () => {
    const mismatches: string[] = []

    for (const [menuPath, menuPerm] of menuPerms) {
      // 精确匹配优先，否则用基础路径匹配通配符路由
      const routePerm = routePerms.get(menuPath)
        ?? routePerms.get(menuPath.split('/:')[0])

      if (routePerm === undefined) continue

      if (menuPerm !== routePerm) {
        mismatches.push(
          `${menuPath}: 菜单=${JSON.stringify(menuPerm)} vs 路由=${JSON.stringify(routePerm)}`
        )
      }
    }

    expect(mismatches, `菜单↔路由权限不一致: ${mismatches.join('\n')}`).toEqual([])
  })

  it('路由中存在权限的页面在菜单中也有对应入口（覆盖性）', () => {
    const menuPaths = new Set(menuPerms.keys())
    const menuBasePaths = new Set(
      Array.from(menuPerms.keys()).map((p) => p.split('/:')[0])
    )

    // 详情页/子路由/父路由不强求菜单入口
    const SKIP_PATTERNS = [/:id/, /:id\/changes/, /\/links$/, /\/alerts$/, /^\/system$/]

    const routeOnly: string[] = []
    for (const [routePath, routePerm] of routePerms) {
      if (routePerm === null) continue
      // 跳过详情页和子路由
      if (SKIP_PATTERNS.some((re) => re.test(routePath))) continue
      // 父路由（如 /system）仅在菜单中有精确 path 才算覆盖
      if (!menuPaths.has(routePath) && !menuBasePaths.has(routePath)) {
        routeOnly.push(`${routePath} (permission: ${routePerm})`)
      }
    }

    expect(routeOnly, `路由有权限但菜单无入口: ${routeOnly.join(', ')}`).toEqual([])
  })

  it('带子菜单的折叠项可以没有自身 path', () => {
    const noPathWithChildren: string[] = []
    for (const group of menuConfig) {
      for (const item of group.items) {
        if (!item.path && item.children && item.children.length > 0) {
          // 带子菜单的折叠项无自身 path 是合法的（如 ipam/topology/backups）
          // 但必须有子项
          if (item.children.length === 0) {
            noPathWithChildren.push(item.nameKey)
          }
        }
        if (!item.path && !item.children) {
          noPathWithChildren.push(item.nameKey)
        }
      }
    }
    expect(noPathWithChildren, `菜单项既无 path 也无子项: ${noPathWithChildren.join(', ')}`).toEqual([])
  })

  it('权限字符串格式合规（module:action）', () => {
    const invalid: string[] = []
    for (const group of menuConfig) {
      for (const item of group.items) {
        if (item.permission && !/^[\w]+:[\w]+$/.test(item.permission)) {
          invalid.push(`${item.nameKey}: "${item.permission}"`)
        }
        if (item.children) {
          for (const child of item.children) {
            if (child.permission && !/^[\w]+:[\w]+$/.test(child.permission)) {
              invalid.push(`${child.nameKey}: "${child.permission}"`)
            }
          }
        }
      }
    }
    expect(invalid, `权限字符串格式不合规: ${invalid.join('\n')}`).toEqual([])
  })
})
