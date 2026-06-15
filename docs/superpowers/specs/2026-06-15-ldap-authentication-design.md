# LDAP 认证集成设计规格

## 1. 概述

### 1.1 功能目标
为企业用户提供 LDAP 目录服务认证支持，允许用户使用 LDAP 账号登录系统。

### 1.2 技术选型
- **Python LDAP 库**：`ldap3`（支持 AD 和 OpenLDAP）
- **连接模式**：支持 SSL/TLS 和 StartTLS
- **认证方式**：简单绑定（Simple Bind）

### 1.3 支持的 LDAP 服务器
- Microsoft Active Directory
- OpenLDAP
- 其他标准 LDAPv3 服务器

---

## 2. 架构设计

### 2.1 目录结构
```
backend/src/services/
├── sso_service.py          # 现有 SSO 服务（OAuth2/SAML）
├── ldap_service.py         # 新增：LDAP 认证服务
```

### 2.2 核心组件

#### 2.2.1 LDAP 配置模型
```python
class LDAPConfig:
    enabled: bool              # 是否启用
    server: str                # LDAP 服务器地址 (如 ldap://192.168.1.100)
    port: int                  # 端口（389 或 636 for SSL）
    use_ssl: bool              # 是否使用 SSL
    use_starttls: bool         # 是否使用 StartTLS
    verify_cert: bool          # 是否验证服务器证书
    bind_dn: str               # 绑定 DN（如 cn=admin,dc=example,dc=com）
    bind_password: str         # 绑定密码（加密存储）
    base_dn: str               # 用户搜索基准 DN
    user_filter: str           # 用户搜索过滤器
    username_attr: str         # 用户名属性（AD: sAMAccountName, OpenLDAP: uid）
    display_attr: str          # 显示名称属性（AD/OpenLDAP: displayName/cn）
    email_attr: str            # 邮箱属性（mail）
    phone_attr: str            # 手机属性（mobile）
    department_attr: str        # 部门属性（department）
    group_attr: str            # 用户组属性（memberOf）
    default_role: str          # LDAP 用户默认角色
```

#### 2.2.2 LDAP 连接管理器
```python
class LDAPConnectionManager:
    """管理 LDAP 连接生命周期"""

    def connect() -> Connection:
        """建立 LDAP 连接"""

    def verify_connection() -> bool:
        """验证连接是否可用"""

    def disconnect():
        """关闭连接"""
```

#### 2.2.3 LDAP 认证服务
```python
class LDAPAuthService:
    """LDAP 认证服务"""

    def authenticate(username: str, password: str) -> LDAPUser:
        """验证用户凭据"""

    def get_user_info(user_dn: str) -> dict:
        """获取用户详细信息"""

    def search_user(username: str) -> LDAPUser:
        """搜索用户"""
```

---

## 3. API 设计

### 3.1 后端 API

#### 3.1.1 LDAP 配置管理（管理员）
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/auth/ldap/config` | 获取 LDAP 配置 |
| PUT | `/api/v1/auth/ldap/config` | 更新 LDAP 配置 |
| POST | `/api/v1/auth/ldap/test` | 测试 LDAP 连接 |

#### 3.1.2 LDAP 登录
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/ldap/login` | LDAP 用户登录 |
| GET | `/api/v1/auth/ldap/enabled` | 检查 LDAP 是否启用 |

### 3.2 请求/响应格式

#### POST /api/v1/auth/ldap/login
**请求体：**
```json
{
  "username": "zhangsan",
  "password": "secret123"
}
```

**成功响应：**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 28800,
  "refresh_token": "eyJ...",
  "user": {
    "id": 5,
    "username": "zhangsan",
    "display_name": "张三",
    "email": "zhangsan@example.com",
    "role": "viewer",
    "role_display_name": "只读查看者",
    "permissions": [...],
    "is_active": true,
    "is_sso_user": false
  }
}
```

**失败响应：**
```json
{
  "detail": "LDAP 认证失败：用户名或密码错误"
}
```

#### PUT /api/v1/auth/ldap/config
**请求体：**
```json
{
  "enabled": true,
  "server": "ldap://192.168.1.100",
  "port": 389,
  "use_ssl": false,
  "use_starttls": true,
  "verify_cert": true,
  "bind_dn": "cn=service,dc=example,dc=com",
  "bind_password": "service_password",
  "base_dn": "ou=users,dc=example,dc=com",
  "user_filter": "(objectClass=person)",
  "username_attr": "sAMAccountName",
  "display_attr": "displayName",
  "email_attr": "mail",
  "phone_attr": "mobile",
  "department_attr": "department",
  "default_role": "viewer"
}
```

---

## 4. 数据存储

### 4.1 配置存储
- 使用现有的 `SystemConfig` 表
- 配置键：`ldap_config`
- 配置值：JSON 格式

### 4.2 用户字段扩展
在现有 `User` 模型基础上：
```python
class User(Base):
    # ... 现有字段 ...

    # 新增 LDAP 相关字段
    ldap_dn = Column(String(500), nullable=True)          # LDAP DN
    ldap_username = Column(String(100), nullable=True)  # LDAP 用户名
    department = Column(String(200), nullable=True)      # 部门
    mobile = Column(String(50), nullable=True)           # 手机
    is_ldap_user = Column(Boolean, default=False)        # 是否 LDAP 用户
```

---

## 5. 用户同步逻辑

### 5.1 登录流程
```
1. 用户提交 username + password
2. 系统查询 LDAP 配置（检查是否启用）
3. LDAP 连接 → 绑定 → 搜索用户
4. 用户绑定验证
5. 获取用户属性
6. 本地用户处理：
   - 存在：更新用户信息（邮箱、显示名、部门等）
   - 不存在：创建本地用户
7. 生成 JWT token
8. 返回登录响应
```

### 5.2 用户属性映射
| LDAP 属性 | 本地字段 | 说明 |
|-----------|---------|------|
| sAMAccountName / uid | username | 用户登录名 |
| displayName / cn | display_name | 显示名称 |
| mail | email | 邮箱 |
| mobile | mobile | 手机 |
| department | department | 部门 |
| - | is_ldap_user = True | 标记为 LDAP 用户 |
| - | role_id = default_role | 分配默认角色 |

---

## 6. 前端设计

### 6.1 登录页面
在现有登录页面增加 "LDAP 登录" 选项卡：

```
┌─────────────────────────────────────────┐
│  ┌─────────┬─────────┬─────────┐        │
│  │ 本地登录 │ SSO登录  │ LDAP登录 │        │
│  └─────────┴─────────┴─────────┘        │
│                                         │
│  用户名: [________________]             │
│  密码:   [________________]             │
│                                         │
│        [ 登 录 ]                         │
└─────────────────────────────────────────┘
```

### 6.2 LDAP 设置页面
在系统设置 → 安全设置中增加 LDAP 配置区块：
- 启用/禁用 LDAP
- 服务器配置
- 连接测试按钮
- 属性映射配置

---

## 7. 安全考虑

### 7.1 密码传输
- LDAP 连接使用 StartTLS 加密
- 或使用 LDAPS (636 端口) SSL 连接
- 本地不存储 LDAP 密码

### 7.2 敏感信息加密
- LDAP 绑定密码使用 `CREDENTIAL_SECRET_KEY` 加密存储
- 参考现有的凭证加密实现

### 7.3 错误处理
- 连接失败：提示配置错误
- 认证失败：不暴露具体原因（防止用户名枚举）
- 超时处理：LDAP 操作设置 10 秒超时

---

## 8. 错误处理

| 错误场景 | HTTP 状态码 | 错误消息 |
|---------|------------|---------|
| LDAP 服务未启用 | 400 | LDAP 认证未启用 |
| 连接失败 | 400 | 无法连接到 LDAP 服务器 |
| 用户不存在 | 401 | 用户名或密码错误 |
| 密码错误 | 401 | 用户名或密码错误 |
| 用户被禁用 | 401 | 账号已被禁用 |
| 服务器超时 | 504 | LDAP 服务器响应超时 |

---

## 9. 依赖项

### 9.1 Python 包
```toml
ldap3 = "^2.9.1"
```

### 9.2 前端依赖
无新增依赖，使用现有 UI 组件。

---

## 10. 测试计划

### 10.1 单元测试
- LDAP 连接管理器测试
- 用户搜索测试
- 认证流程测试

### 10.2 集成测试
- 本地开发环境 LDAP 连接测试
- 配置保存/加载测试

### 10.3 手动测试
- AD 环境登录测试
- OpenLDAP 环境登录测试
- SSL/TLS 连接测试

---

## 11. 实施步骤

1. **后端：数据模型**
   - 扩展 User 模型
   - 创建 LDAP 配置 schema

2. **后端：核心服务**
   - 实现 LDAP 连接管理器
   - 实现 LDAP 认证服务

3. **后端：API 路由**
   - 配置管理接口
   - 登录接口

4. **前端：登录页面**
   - 增加 LDAP 登录选项卡
   - 表单验证和错误处理

5. **前端：设置页面**
   - LDAP 配置界面
   - 连接测试功能

6. **文档和测试**
   - 更新 API 文档
   - 编写测试用例

---

## 12. 替代方案说明

### 为什么不使用方案 A（扩展 SSO 服务）？
LDAP 认证与 OAuth2/SAML 有本质区别：
- OAuth2/SAML：使用授权码流程，涉及第三方授权服务器
- LDAP：直接绑定验证，属于简单用户名密码认证

独立服务模块职责更清晰，避免 SSO 服务膨胀。

### 为什么使用 ldap3 而非 python-ldap？
- `ldap3` 是纯 Python 实现，跨平台兼容性好
- 安装简单（不需要编译）
- API 设计现代，支持异步操作
