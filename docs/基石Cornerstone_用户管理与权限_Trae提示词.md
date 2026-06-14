# 基石 Cornerstone · 用户管理与权限模块
## Trae 开发提示词

---

## 背景说明

当前项目已有：
- 前端：Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- 后端：FastAPI + SQLAlchemy（异步）+ SQLite/PostgreSQL + JWT认证
- 现有用户功能：用户列表展示、新增/编辑/删除用户、角色字段（仅展示，无真实权限控制）
- 现有认证：JWT登录（`/api/v1/auth/token`），但权限校验未落地

本次任务：实现完整的用户管理 + RBAC权限控制体系，让不同角色的用户看到不同的菜单和功能。

---

## 权限设计

### 角色定义（三个内置角色，不可删除）

```
超级管理员（super_admin）
└── 所有权限，包括用户管理、系统设置
    唯一可以管理其他用户角色的账号

IT运维工程师（engineer）
└── 所有业务模块读写权限
    可以操作：站点、专线、IPAM、设备、配置备份、拓扑
    不可操作：用户管理、系统设置

只读查看者（viewer）
└── 所有业务模块只读权限
    可以查看：所有列表、详情、报表、拓扑
    不可操作：任何新增/编辑/删除/备份触发
```

### 权限粒度（按模块+操作）

```
模块列表：
sites         站点管理
circuits      专线管理
ipam          IP地址管理
devices       设备台账
backups       配置备份
topology      网络拓扑
alerts        预警中心
system        系统管理（用户/设置）
logs          操作日志

操作类型：
read          查看列表、详情
write         新增、编辑
delete        删除
export        导出CSV/PNG
backup_exec   触发备份（backups模块专用）
scan_exec     触发IP扫描（ipam模块专用）
```

### 权限矩阵

| 模块 | 操作 | super_admin | engineer | viewer |
|------|------|-------------|----------|--------|
| sites | read/write/delete | ✅ | ✅ | read only |
| circuits | read/write/delete | ✅ | ✅ | read only |
| ipam | read/write/delete/scan_exec | ✅ | ✅ | read only |
| devices | read/write/delete | ✅ | ✅ | read only |
| backups | read/write/delete/backup_exec | ✅ | ✅ | read only |
| topology | read/write/delete | ✅ | ✅ | read only |
| alerts | read | ✅ | ✅ | ✅ |
| system | read/write/delete | ✅ | ❌ | ❌ |
| logs | read | ✅ | ✅ | ✅ |

---

## 数据模型

修改/新建 `backend/src/models/auth.py`：

```python
class Role(Base):
    """角色"""
    __tablename__ = "roles"
    id: int
    name: str           # super_admin / engineer / viewer
    display_name: str   # 超级管理员 / IT运维工程师 / 只读查看者
    description: str
    is_builtin: bool    # True=内置角色不可删除
    created_at: datetime

class Permission(Base):
    """权限定义"""
    __tablename__ = "permissions"
    id: int
    module: str         # sites / circuits / ipam / devices / backups / topology / alerts / system / logs
    action: str         # read / write / delete / export / backup_exec / scan_exec
    display_name: str   # 如「站点管理-新增编辑」
    description: str

class RolePermission(Base):
    """角色-权限关联"""
    __tablename__ = "role_permissions"
    id: int
    role_id: int        # 关联 roles.id
    permission_id: int  # 关联 permissions.id

class User(Base):
    """用户（修改现有模型，确认包含以下字段）"""
    __tablename__ = "users"
    id: int
    username: str           # 唯一，登录用
    display_name: str       # 显示名，如「张三」
    email: str              # 唯一
    password_hash: str      # bcrypt哈希
    role_id: int            # 关联 roles.id
    is_active: bool         # 是否启用
    last_login_at: datetime # 最后登录时间
    last_login_ip: str      # 最后登录IP
    avatar: str             # 头像URL（可选）
    created_at: datetime
    updated_at: datetime

class UserSession(Base):
    """登录会话记录（用于强制下线）"""
    __tablename__ = "user_sessions"
    id: int
    user_id: int
    jti: str            # JWT ID，用于失效单个token
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    is_revoked: bool    # True=已强制下线
```

**初始化数据**（应用首次启动时自动插入）：
```python
# 初始化三个内置角色和对应权限
# 初始化默认超级管理员账号：admin / Cornerstone@2024
# 若 users 表已有数据则跳过初始化
```

---

## 后端实现

### 认证增强 `backend/src/api/auth.py`

在现有基础上补充：

```
POST /api/v1/auth/token
    登录接口，增加：
    - 记录登录时间和IP到 users 表
    - 创建 UserSession 记录
    - JWT payload 中增加：{ user_id, username, role, permissions: [...], jti }
    - 连续登录失败5次锁定账号15分钟（存Redis或内存）
    返回：
    {
        "access_token": "...",
        "token_type": "bearer",
        "expires_in": 7200,
        "user": {
            "id": 1,
            "username": "admin",
            "display_name": "管理员",
            "role": "super_admin",
            "permissions": ["sites:read", "sites:write", ...]
        }
    }

POST /api/v1/auth/logout
    退出登录，将当前 jti 标记为 revoked

GET  /api/v1/auth/me
    获取当前登录用户信息（含权限列表）

POST /api/v1/auth/change-password
    修改自己的密码
    Body: { "old_password": "...", "new_password": "..." }
    新密码规则：至少8位，包含字母和数字

POST /api/v1/auth/refresh
    刷新token（现有接口，确保正常工作）
```

### 权限中间件 `backend/src/utils/permissions.py`

```python
# 实现权限校验装饰器，在各路由中使用：

def require_permission(module: str, action: str):
    """
    FastAPI依赖注入，校验当前用户是否有指定权限
    无权限返回 403 { "code": 403, "message": "无权限执行此操作" }
    用法示例：
    @router.post("/sites/", dependencies=[Depends(require_permission("sites", "write"))])
    """

def get_current_user():
    """
    从JWT中解析当前用户
    校验 jti 是否被 revoke（查询 user_sessions 表）
    用户被禁用时返回 401
    """

# 在所有现有路由上补充权限校验：
# GET接口     → require_permission(module, "read")
# POST/PUT接口 → require_permission(module, "write")
# DELETE接口  → require_permission(module, "delete")
# 触发备份    → require_permission("backups", "backup_exec")
# 触发扫描    → require_permission("ipam", "scan_exec")
```

### 用户管理API `backend/src/api/users.py`

在现有基础上补充：

```
GET    /api/v1/users/                   获取用户列表（仅super_admin可访问）
       支持按角色/状态/关键字筛选，分页
POST   /api/v1/users/                   创建用户（仅super_admin）
PUT    /api/v1/users/{id}               编辑用户（仅super_admin，不可修改自己角色）
DELETE /api/v1/users/{id}               删除用户（仅super_admin，不可删除自己）
PATCH  /api/v1/users/{id}/toggle        启用/停用用户（停用后该用户已有token立即失效）
POST   /api/v1/users/{id}/reset-password 重置密码（仅super_admin，生成随机密码返回）
GET    /api/v1/users/{id}/sessions      查看用户登录会话列表
POST   /api/v1/users/{id}/revoke-sessions 强制该用户所有会话下线

GET    /api/v1/roles/                   获取角色列表（含每个角色的权限详情）
GET    /api/v1/permissions/             获取所有权限定义列表
```

---

## 前端实现

### 登录页面增强 `frontend/src/features/auth/Login.vue`

```
在现有登录页基础上：
- 登录成功后将用户信息（含permissions数组）存入 Pinia useAuthStore
- 登录失败显示具体错误：「用户名或密码错误」/「账号已被禁用」/「账号已锁定，请N分钟后重试」
- 记住用户名（checkbox，存localStorage）
- 登录成功跳转到登录前访问的页面（vue-router beforeEach守卫记录）
```

### 权限状态管理 `frontend/src/store/auth.ts`

```typescript
// useAuthStore 存储：
interface AuthState {
    user: {
        id: number
        username: string
        display_name: string
        role: 'super_admin' | 'engineer' | 'viewer'
        permissions: string[]   // 如 ["sites:read", "sites:write", "ipam:scan_exec"]
        avatar?: string
    } | null
    token: string | null
    isAuthenticated: boolean
}

// 实现以下方法：
// login(username, password) → 调用登录接口，存token和用户信息
// logout() → 调用登出接口，清空store，跳转登录页
// hasPermission(module: string, action: string): boolean
//     示例：hasPermission('sites', 'write') → true/false
// refreshUserInfo() → 调用 /auth/me 刷新用户信息
```

### 权限指令 `frontend/src/lib/directives/permission.ts`

```typescript
// 注册全局自定义指令 v-permission
// 用法：
// <el-button v-permission="'sites:write'">新增站点</el-button>
// <el-button v-permission="['sites:write', 'sites:delete']">操作</el-button>
// 无权限时：按钮变为 disabled 状态（不是隐藏，避免布局跳动）
// 对于危险操作按钮（删除类）：无权限时直接 v-if 隐藏，用 v-permission-hide 指令
```

### 路由权限守卫 `frontend/src/app/router.ts`

```typescript
// 在现有路由配置中，为每个路由添加 meta.permission 字段：
// { path: '/sites', meta: { permission: 'sites:read' } }
// { path: '/system/users', meta: { permission: 'system:read' } }

// beforeEach 路由守卫：
// 1. 未登录 → 跳转 /login
// 2. 已登录但无权限 → 跳转 /403 页面
// 3. 记录登录前访问的路由，登录成功后跳回

// 新增 403 页面：
// 友好提示「您没有访问此页面的权限」
// 按钮：「返回首页」
```

### 菜单动态权限

```typescript
// 侧边栏菜单根据用户权限动态显示/隐藏：
// viewer角色：隐藏「系统管理」菜单
// engineer角色：隐藏「系统管理」下的「用户管理」「权限管理」子菜单

// 在现有侧边栏组件中，菜单项增加 permission 配置：
const menuItems = [
    { title: '首页', path: '/dashboard', permission: null },  // 所有人可见
    { title: '站点管理', path: '/sites', permission: 'sites:read' },
    { title: '系统管理', path: '/system', permission: 'system:read' },
    // ...
]
// 渲染时过滤掉无权限的菜单项
```

### 用户管理页面增强 `frontend/src/features/system/UserManagement.vue`

```
页面布局：
- 顶部：搜索框（按用户名/邮箱）+ 角色筛选 + 状态筛选 + 「新增用户」按钮
- 表格列：
    头像（小圆形头像，无头像显示用户名首字）
    用户名 / 显示名
    邮箱
    角色（带颜色badge：超级管理员-红、运维工程师-蓝、只读查看者-灰）
    状态（启用/禁用开关，仅super_admin可操作）
    最后登录时间 + IP
    操作：编辑 / 重置密码 / 查看会话 / 删除
- 当前登录用户的行高亮，操作列显示「当前账号」badge，不显示删除按钮

新增/编辑用户弹窗：
- 显示名（必填）
- 用户名（必填，仅新增时可填，编辑时灰显）
- 邮箱（必填）
- 角色（下拉，仅super_admin可修改）
- 密码（新增必填，编辑时留空表示不修改）
- 确认密码
- 状态：启用/禁用

重置密码对话框：
- 确认提示「将为 {用户名} 生成新的随机密码，请妥善保存」
- 确认后显示新密码，带「复制」按钮
- 密码格式：8位随机，含大小写字母和数字

用户会话管理抽屉：
- 标题：「{用户名} 的登录会话」
- 列：登录时间 / IP地址 / 设备（User-Agent解析）/ 状态（活跃/已过期/已撤销）
- 「一键强制下线」按钮（撤销所有活跃会话）
```

### 个人中心页面 `frontend/src/features/system/Profile.vue`

```
路由：/profile
入口：顶部导航栏右侧用户头像下拉菜单中的「个人设置」

页面内容：
左侧：
- 头像展示（圆形，点击可上传更换，支持JPG/PNG，最大1MB）
- 用户名（不可修改）
- 角色badge

右侧两个卡片：
卡片1：基本信息
- 显示名（可编辑）
- 邮箱（可编辑）
- 保存按钮

卡片2：修改密码
- 当前密码
- 新密码（至少8位，含字母和数字，实时强度检测）
- 确认新密码
- 密码强度条（弱/中/强，颜色红/橙/绿）
- 保存按钮

底部：
登录历史（最近5次）：时间 / IP / 设备
```

### 顶部导航栏更新

```
右上角用户区域：
- 头像（小圆形）+ 显示名 + 角色badge
- 下拉菜单：
    个人设置（跳转 /profile）
    ────────
    退出登录（调用logout，清空token跳转登录页）
```

---

## 安全要求

- 密码使用 `bcrypt` 哈希存储，cost factor=12
- JWT secret 从环境变量 `JWT_SECRET_KEY` 读取，启动时若不存在自动生成并写入 `.env`
- access_token 有效期 2小时，refresh_token 有效期 7天
- 所有需要登录的接口统一使用 `get_current_user` 依赖，未登录返回 401
- 接口返回的用户信息不包含 `password_hash` 字段
- 前端 token 存 localStorage，请求时自动添加 `Authorization: Bearer {token}` header
- token 过期时前端自动用 refresh_token 刷新，刷新失败则跳转登录页
- Axios 请求拦截器统一处理 401（跳转登录）和 403（提示无权限）

---

## 开发顺序

**Step 1**：数据库 migration（完善 users 表 + 新增 roles/permissions/role_permissions/user_sessions 表）+ 初始化内置角色和权限数据 + 默认admin账号

**Step 2**：后端认证增强（登录记录IP/时间、JWT携带权限列表、登录失败锁定、logout撤销jti）

**Step 3**：权限校验中间件（`require_permission` 装饰器）+ 在所有现有路由补充权限校验

**Step 4**：用户管理API补充（启用停用、重置密码、会话管理）+ 角色权限查询接口

**Step 5**：前端 `useAuthStore` 完善（存permissions、hasPermission方法）+ Axios拦截器（401/403处理、token自动刷新）

**Step 6**：路由守卫（未登录跳转、无权限跳转403页面）+ 菜单动态权限过滤

**Step 7**：全局 `v-permission` 指令 + 在所有现有页面的操作按钮上补充权限控制

**Step 8**：用户管理页面增强（头像、会话管理抽屉、重置密码弹窗）

**Step 9**：个人中心页面（头像上传、修改密码、登录历史）

**Step 10**：顶部导航栏用户区域更新 + 登录页体验优化

---

## 注意事项

- 三个内置角色（super_admin/engineer/viewer）不允许删除，`is_builtin=True` 的角色删除时后端返回 400 错误
- 不允许删除或禁用自己的账号，后端校验 `current_user.id != target_user_id`
- super_admin 角色只能由其他 super_admin 分配，engineer 无法把自己提升为 super_admin
- 系统中必须保留至少一个启用状态的 super_admin 账号，删除最后一个时后端拒绝
- viewer 角色用户登录后，所有写操作按钮显示为 disabled，鼠标悬停提示「您的角色无此操作权限」
- 权限列表在登录时一次性写入JWT，2小时内不重新查DB；修改用户角色后需调用 revoke-sessions 强制重新登录才能生效
- 前端 `v-permission` 指令只做UI控制，后端接口必须同时做权限校验，不依赖前端
- 所有用户管理操作写入 audit_logs 表，包含操作人、目标用户、变更内容
