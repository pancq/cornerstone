# 基石 Cornerstone · IT负责人权限完整调整
## Trae 开发提示词

---

## 背景说明

viewer 角色已重新定位为「IT负责人」，显示名称已更新。
本次在已有调整基础上，完善以下权限细节：
1. 站点列表：只显示管理相关字段，隐藏技术字段
2. 设备台账：新增摘要视图，只显示管理层关心的字段
3. 预警中心：默认只显示合同到期、保修到期、专线故障三类
4. 审计日志：只显示登录记录和高危操作两类

---

## 一、站点列表 viewer 视图优化

**文件**：`frontend/src/features/sites/SiteList.vue`

### 字段控制

根据当前用户角色，动态控制表格列的显示：

```typescript
import { useAuthStore } from '@/store/auth'
const authStore = useAuthStore()
const isViewer = computed(() => authStore.user?.role === 'viewer')

// viewer 可见列
const VIEWER_SITE_COLUMNS = ['name', 'city', 'contact', 'phone', 'status']

// engineer/super_admin 可见列（全部）
const ALL_SITE_COLUMNS = ['name', 'city', 'contact', 'phone', 'circuit_count', 'device_count', 'status', 'zabbix_url', 'actions']
```

### 表格列配置

```html
<!-- 站点名称：所有角色可见 -->
<el-table-column prop="name" label="站点名称" />

<!-- 城市：所有角色可见 -->
<el-table-column prop="city" label="所在城市" />

<!-- 联系人：所有角色可见 -->
<el-table-column prop="contact" label="联系人" />

<!-- 电话：所有角色可见，保留一键复制功能 -->
<el-table-column prop="phone" label="联系电话" />

<!-- 专线数量：仅 engineer/super_admin 可见 -->
<el-table-column v-if="!isViewer" prop="circuit_count" label="专线数量" />

<!-- 设备数量：仅 engineer/super_admin 可见 -->
<el-table-column v-if="!isViewer" prop="device_count" label="设备数量" />

<!-- 状态：所有角色可见 -->
<el-table-column prop="status" label="运行状态" />

<!-- Zabbix跳转：仅 engineer/super_admin 可见 -->
<el-table-column v-if="!isViewer" prop="zabbix_url" label="监控" />

<!-- 操作列：仅 engineer/super_admin 可见 -->
<el-table-column v-if="!isViewer" label="操作">
  <!-- 编辑/删除按钮 -->
</el-table-column>
```

### 页面顶部操作栏

```html
<!-- 新增站点按钮：仅 engineer/super_admin 可见 -->
<el-button v-if="!isViewer" type="primary" @click="handleAdd">
  新增站点
</el-button>
```

---

## 二、设备台账 viewer 摘要视图

**文件**：`frontend/src/features/devices/DeviceList.vue`

### 字段控制

viewer 只看管理层关心的字段，隐藏所有技术字段：

```typescript
const isViewer = computed(() => authStore.user?.role === 'viewer')
```

```html
<!-- 设备名称：所有角色可见 -->
<el-table-column prop="name" label="设备名称" />

<!-- 设备类型（图标+文字）：所有角色可见 -->
<el-table-column prop="device_type" label="设备类型" />

<!-- 品牌/型号：所有角色可见 -->
<el-table-column prop="model" label="品牌/型号" />

<!-- 所在站点：所有角色可见 -->
<el-table-column prop="site_name" label="所在站点" />

<!-- 采购日期：所有角色可见 -->
<el-table-column prop="purchase_date" label="采购日期" />

<!-- 保修到期：所有角色可见，临近时显示橙/红色 -->
<el-table-column prop="warranty_end" label="保修到期" />

<!-- 运行状态：所有角色可见 -->
<el-table-column prop="status" label="运行状态" />

<!-- 以下字段仅 engineer/super_admin 可见 -->
<!-- 管理IP：隐藏 -->
<el-table-column v-if="!isViewer" prop="mgmt_ip" label="管理IP" />

<!-- 机柜位置：隐藏 -->
<el-table-column v-if="!isViewer" prop="location" label="机柜位置" />

<!-- 序列号：隐藏 -->
<el-table-column v-if="!isViewer" prop="sn" label="序列号" />

<!-- 操作列（新增/编辑/删除）：仅 engineer/super_admin 可见 -->
<el-table-column v-if="!isViewer" label="操作">
  <!-- 操作按钮 -->
</el-table-column>
```

### 顶部操作栏

```html
<!-- 新增设备/CSV导入：仅 engineer/super_admin 可见 -->
<el-button v-if="!isViewer" type="primary">新增设备</el-button>
<el-button v-if="!isViewer">CSV导入</el-button>
```

### 设备详情页

viewer 点击设备名称时：
- 显示基本信息（名称、类型、型号、站点、采购日期、保修日期、状态）
- **隐藏**：管理IP、序列号、SSH凭证、接口列表、配置备份记录
- **隐藏**：编辑按钮、删除按钮

```typescript
// 设备详情页 frontend/src/features/devices/DeviceDetail.vue
// 在各 Tab 显示逻辑中加判断：
const showTechnicalTabs = computed(() => !isViewer.value)

// 隐藏的 Tab：接口管理、配置备份、SSH凭证
```

---

## 三、预警中心 viewer 过滤

**文件**：`frontend/src/features/alerts/AlertCenter.vue`

### 默认显示规则

viewer 进入预警中心时，默认只显示以下三类告警，其他类型折叠或隐藏：

```typescript
// 预警类型定义
const ALERT_TYPES = {
  contract_expiry:  { label: '合同到期',  icon: 'ti-file-description', color: '#E6A23C' },
  warranty_expiry:  { label: '保修到期',  icon: 'ti-shield-off',       color: '#E6A23C' },
  circuit_fault:    { label: '专线故障',  icon: 'ti-alert-triangle',   color: '#F56C6C' },
  backup_fail:      { label: '备份失败',  icon: 'ti-database-off',     color: '#F56C6C' },  // 仅engineer可见
  subnet_full:      { label: '子网容量',  icon: 'ti-network',          color: '#E6A23C' },  // 仅engineer可见
  inspection_alert: { label: '巡检告警',  icon: 'ti-radar',            color: '#E6A23C' },  // 仅engineer可见
}

// viewer 可见的告警类型
const VIEWER_ALERT_TYPES = ['contract_expiry', 'warranty_expiry', 'circuit_fault']

// 根据角色过滤
const visibleAlertTypes = computed(() => {
  if (isViewer.value) return VIEWER_ALERT_TYPES
  return Object.keys(ALERT_TYPES)
})
```

### Tab 显示控制

预警中心顶部的 Tab 分类：

```html
<!-- viewer 只显示这三个 Tab -->
<el-tab-pane label="合同到期" name="contract_expiry" />
<el-tab-pane label="保修到期" name="warranty_expiry" />
<el-tab-pane label="专线故障" name="circuit_fault" />

<!-- 以下 Tab 仅 engineer/super_admin 可见 -->
<el-tab-pane v-if="!isViewer" label="备份失败" name="backup_fail" />
<el-tab-pane v-if="!isViewer" label="子网容量" name="subnet_full" />
<el-tab-pane v-if="!isViewer" label="巡检告警" name="inspection_alert" />
```

### 页面标题说明

viewer 进入预警中心时，在页面顶部显示一行灰色说明：

```html
<div v-if="isViewer" class="viewer-hint">
  <i class="ti ti-info-circle" />
  当前显示合同到期、保修到期、专线故障三类预警，其他运维类告警由IT工程师处理
</div>
```

---

## 四、审计日志 viewer 过滤

**文件**：`frontend/src/features/system/AuditLog.vue`（或对应的日志页面文件）

### 显示规则

viewer 看到的审计日志只包含两类：

```typescript
// 日志类型定义
const LOG_CATEGORIES = {
  login:     '登录记录',   // 所有角色可见
  dangerous: '高危操作',   // 所有角色可见（删除、回滚等）
  normal:    '普通操作',   // 仅 engineer/super_admin 可见
}

// viewer 可见的日志类型
const VIEWER_LOG_ACTIONS = [
  'user_login',         // 用户登录
  'user_logout',        // 用户退出
  'login_failed',       // 登录失败
  'device_delete',      // 删除设备
  'circuit_delete',     // 删除专线
  'backup_rollback',    // 配置回滚
  'user_create',        // 新增用户
  'user_role_change',   // 修改用户角色
  'user_delete',        // 删除用户
]

// 后端查询时根据角色过滤
// viewer 调用 GET /api/v1/logs/?category=login,dangerous
// engineer/super_admin 调用 GET /api/v1/logs/（全部）
```

### 后端接口更新

在 `backend/src/api/audit_logs.py` 中，根据当前用户角色过滤返回数据：

```python
@router.get("/")
async def get_audit_logs(
    category: Optional[str] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # viewer 角色强制只返回登录和高危操作
    VIEWER_ACTIONS = [
        'user_login', 'user_logout', 'login_failed',
        'device_delete', 'circuit_delete', 'backup_rollback',
        'user_create', 'user_role_change', 'user_delete'
    ]

    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if current_user['role'] == 'viewer':
        query = query.where(AuditLog.action.in_(VIEWER_ACTIONS))
    elif category:
        # engineer/super_admin 支持按分类筛选
        if category == 'login':
            query = query.where(AuditLog.action.in_(['user_login', 'user_logout', 'login_failed']))
        elif category == 'dangerous':
            query = query.where(AuditLog.action.in_(VIEWER_ACTIONS[3:]))  # 去掉登录类

    # 分页...
```

### 前端 Tab 控制

```html
<!-- 登录日志：所有角色可见 -->
<el-tab-pane label="登录日志" name="login" />

<!-- 高危操作：所有角色可见 -->
<el-tab-pane label="高危操作" name="dangerous" />

<!-- 操作日志（全部）：仅 engineer/super_admin 可见 -->
<el-tab-pane v-if="!isViewer" label="全部操作" name="all" />
```

---

## 五、菜单可见性确认

确认侧边栏菜单对 viewer 的显示状态（在现有菜单过滤逻辑基础上补充）：

```typescript
// viewer 可见菜单项（完整列表）
const VIEWER_MENU = [
  '/dashboard',           // 首页（管理视图）
  '/circuits',            // 专线（只读）
  '/sites',               // 站点（只读）
  '/devices',             // 设备（摘要视图）
  '/alerts',              // 预警中心（过滤后）
  '/audit-logs',          // 审计日志（过滤后）
]

// viewer 不可见菜单项（确认隐藏）
// /ipam              IP管理
// /topology          网络拓扑
// /backups           配置备份
// /inspection        智能巡检
// /system/users      用户管理
// /system/roles      角色管理
// /system/sso        认证集成
// /system/settings   系统设置（含日志设置、AI设置、通知设置）
```

---

## 六、403 页面优化

viewer 访问无权限页面时，403 页面显示更友好的提示：

```html
<!-- frontend/src/views/403.vue -->
<div class="forbidden-page">
  <i class="ti ti-lock" style="font-size:48px; color:#909399" />
  <h2>无访问权限</h2>
  <p v-if="isViewer">
    此页面需要运维工程师权限。<br>
    如需查看运营概况，请访问
    <router-link to="/dashboard">管理看板</router-link>
  </p>
  <p v-else>您没有访问此页面的权限，请联系管理员。</p>
  <el-button @click="router.push('/dashboard')">返回首页</el-button>
</div>
```

---

## 开发顺序

**Step 1**：站点列表字段控制（v-if="!isViewer" 控制列显示）
**Step 2**：设备台账字段控制（表格列 + 顶部操作栏 + 详情页Tab）
**Step 3**：预警中心 Tab 过滤（viewer 只显示3个Tab + 页面顶部说明）
**Step 4**：审计日志后端过滤（viewer 强制只返回登录和高危操作）
**Step 5**：审计日志前端 Tab 控制
**Step 6**：菜单可见性确认（对照列表检查每个菜单项）
**Step 7**：403 页面优化

---

## 注意事项

- 所有 `v-if="!isViewer"` 的判断只控制前端显示，后端接口同样需要权限校验
- viewer 访问设备详情页时，后端 `GET /api/v1/devices/{id}` 接口正常返回数据，但返回的字段中不包含 `mgmt_ip` 的具体IP地址（返回 `null` 或省略），防止通过接口直接获取管理IP
- 站点和设备的只读限制：viewer 的 PUT/POST/DELETE 请求后端返回 403，不依赖前端隐藏按钮
- 预警中心的过滤逻辑在前端实现即可（后端已返回全部告警，前端根据角色过滤展示），不需要改后端查询
- 审计日志的过滤必须在后端实现，不能只在前端过滤（防止前端绕过）
- 改动完成后用 viewer 账号登录验证：菜单只显示允许的页面，设备列表无技术字段，预警中心只有3个Tab
