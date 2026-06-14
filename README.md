# 基石 Cornerstone

IT 基础设施资源管理平台，依据 `基石Cornerstone_IT基础设施资源管理平台_PRD_v1.0.docx` 实现第一期核心体验。

> **安全提醒**：首次部署后请立即修改默认管理员密码，生产环境请使用 PostgreSQL 并更换 `SECRET_KEY`。

## 技术栈

### 前端
- **框架**: Vue 3 + TypeScript
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **构建工具**: Vite

### 后端
- **框架**: FastAPI + Python 3.11+
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy (异步模式)
- **认证**: JWT + RBAC
- **设备连接**: Netmiko

## 快速开始

### 前置要求
- Node.js >= 18
- Python >= 3.11

### 运行前端

```bash
cd frontend
npm install
npm run dev
```

### 运行后端

```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端API | http://localhost:8000 |
| API文档 | http://localhost:8000/docs |

## 功能模块

### 1. 首页仪表盘
- 专线、IP、设备、备份状态统计卡片
- 近期预警展示
- 资源总览视图

### 2. 站点管理
- 站点列表展示（名称、所在地、联系人、电话、专线数量、运行状态）
- 运行状态监控（正常/告警/离线）
- 告警站点高亮显示
- 一键跳转Zabbix监控页面
- 电话一键复制功能
- 搜索、新增、编辑、删除功能

### 3. 专线管理
- 专线列表、搜索、新增、编辑、删除
- 合同到期预警
- 带宽、费用、状态管理
- 专线详情页面

### 4. IPAM（IP地址管理）
- 地址段/子网展示
- IP 分配与管理
- 使用率色块显示
- 重复 IP 冲突拦截
- CSV 导入功能

### 5. 设备台账
- 设备列表、新增/编辑/删除
- 管理 IP 关联
- 保修到期预警
- CSV 导入功能

### 6. 配置备份
- 备份历史记录
- 手动备份记录
- 配置查看/下载
- 最近版本 Diff 对比

### 7. 预警中心
预警中心提供传统规则预警和AI智能检测两种预警机制。

#### 传统规则预警
| 预警类型 | 检测规则 | 触发条件 | 级别判定 |
|---------|---------|---------|---------|
| IP到期预警 | 检查 `expireAt` 字段 | 剩余天数 ≤ 30天 | ≤7天:危险, ≤30天:警告 |
| 专线合同预警 | 检查 `contractEnd` 字段 | 剩余天数 ≤ 30天 | ≤7天:危险, ≤30天:警告 |
| 设备保修预警 | 检查 `warrantyEnd` 字段 | 剩余天数 ≤ 30天 | ≤7天:危险, ≤30天:警告 |
| 备份失败预警 | 检查 `status === '失败'` | 有失败记录即触发 | 危险 |
| 子网容量预警 | 计算使用率 = 已用IP/254 | 使用率 ≥ 80% | 危险 |

#### AI智能检测
基于实时状态数据和趋势分析的智能预警：

1. **设备状态异常检测**
   - 检测离线设备 → 危险级别
   - 检测维修中设备 → 警告级别

2. **专线连接异常检测**
   - 检测断开专线 → 危险级别
   - 检测不稳定专线 → 警告级别

3. **备份成功率趋势检测**
   - 计算最近7天备份成功率
   - <50%: 危险 | 50-80%: 警告

4. **IP池耗尽预测**
   - 检测使用率 ≥70% 的子网
   - 预测耗尽时间并预警

#### AI预警展示
每个AI预警包含：
- 问题描述和当前值 vs 阈值对比
- 智能处理建议
- 检测时间
- 快速跳转到相关详情页面

#### AI大模型预测中心（新增）
基于大语言模型的智能预测功能：

**支持的AI服务**：
- Claude 3 (Anthropic) - 海外模型
- GPT-4 (OpenAI) - 海外模型
- 本地模型 (如 Llama 3) - 私有化部署

**预测功能**：
1. **智能摘要** - 一键生成系统预警摘要，快速了解当前状态
2. **趋势预测** - 预测资源消耗趋势，提前规划扩容
3. **根因分析** - 智能分析故障原因，提供排查建议
4. **智能问答** - 自然语言提问，AI为您解答

**预测结果包含**：
- 置信度评分
- 详细分析报告
- 可操作建议
- 检测时间戳

### 8. 系统管理
- 用户管理（用户名、邮箱、角色、状态）
- 用户新增/编辑/删除

### 9. 操作日志
- 操作记录列表
- 按操作、目标、用户搜索过滤
- 操作类型分类（创建/更新/删除/备份）
- 操作结果状态显示

### 10. 系统设置
- 公司Logo上传与管理
- Logo存储到服务器数据库
- 所有用户共享Logo设置

## 已实现的交互特性

| 特性 | 描述 |
|------|------|
| 状态监控 | 站点运行状态实时显示（绿/红/灰三色状态徽标） |
| Zabbix集成 | 点击状态一键跳转Zabbix监控大盘 |
| 告警过滤 | 点击告警统计卡片自动过滤告警站点 |
| 一键复制 | 电话号码一键复制到剪贴板 |
| 骨架屏 | 数据加载时显示骨架屏 |
| 空状态 | 搜索无结果时显示友好提示 |
| 行高亮 | 告警状态行背景泛红突出显示 |
| Logo上传 | 支持JPG/PNG/GIF格式，最大2MB |
| Logo共享 | 上传的Logo存储到服务器，所有用户可见 |

## 项目结构

```
├── frontend/                    # 前端代码
│   ├── src/
│   │   ├── api/                 # API调用
│   │   ├── app/                 # 应用配置（路由等）
│   │   ├── features/            # 功能模块页面
│   │   │   ├── alerts/          # 预警中心
│   │   │   ├── auth/            # 认证登录
│   │   │   ├── backups/         # 配置备份
│   │   │   ├── circuits/        # 专线管理
│   │   │   ├── dashboard/       # 仪表盘
│   │   │   ├── devices/         # 设备台账
│   │   │   ├── ipam/            # IP地址管理
│   │   │   ├── sites/           # 站点管理
│   │   │   └── system/          # 系统管理
│   │   ├── store/               # Pinia状态管理
│   │   ├── types/               # TypeScript类型定义
│   │   └── lib/                 # 工具函数
│   └── package.json
│
├── backend/                     # 后端代码
│   ├── src/
│   │   ├── api/                 # API路由
│   │   │   ├── auth.py          # 认证接口
│   │   │   ├── sites.py         # 站点接口
│   │   │   ├── circuits.py      # 专线接口
│   │   │   ├── ipam.py          # IP管理接口
│   │   │   ├── devices.py       # 设备接口
│   │   │   ├── backups.py       # 备份接口
│   │   │   ├── users.py         # 用户接口
│   │   │   ├── audit_logs.py    # 操作日志接口
│   │   │   └── settings.py      # 系统设置接口
│   │   ├── models/              # 数据库模型
│   │   ├── schemas/             # Pydantic Schema
│   │   ├── utils/               # 工具函数
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   └── main.py              # 应用入口
│   └── venv/                    # Python虚拟环境
│
└── README.md                    # 项目文档
```

## API接口列表

| 模块 | 接口 | 方法 | 描述 |
|------|------|------|------|
| Auth | `/api/v1/auth/token` | POST | 获取JWT令牌 |
| Auth | `/api/v1/auth/refresh` | POST | 刷新令牌 |
| Sites | `/api/v1/sites/` | GET | 获取站点列表 |
| Sites | `/api/v1/sites/{id}` | GET | 获取站点详情 |
| Sites | `/api/v1/sites/` | POST | 创建站点 |
| Sites | `/api/v1/sites/{id}` | PUT | 更新站点 |
| Sites | `/api/v1/sites/{id}` | DELETE | 删除站点 |
| Circuits | `/api/v1/circuits/` | GET | 获取专线列表 |
| Circuits | `/api/v1/circuits/{id}` | GET | 获取专线详情 |
| IPAM | `/api/v1/ipam/prefixes` | GET | 获取子网列表 |
| IPAM | `/api/v1/ipam/addresses` | GET | 获取IP地址列表 |
| Devices | `/api/v1/devices/` | GET | 获取设备列表 |
| Backups | `/api/v1/backups/` | GET | 获取备份列表 |
| Users | `/api/v1/users/` | GET | 获取用户列表 |
| Logs | `/api/v1/logs/` | GET | 获取操作日志 |
| Settings | `/api/v1/settings/logo` | GET | 获取Logo |
| Settings | `/api/v1/settings/logo` | POST | 上传Logo |
| Settings | `/api/v1/settings/logo` | DELETE | 删除Logo |

## 数据库模型

| 表名 | 描述 |
|------|------|
| users | 用户信息 |
| roles | 角色定义 |
| permissions | 权限定义 |
| sites | 站点信息 |
| circuits | 专线信息 |
| devices | 设备信息 |
| ip_addresses | IP地址 |
| prefixes | 子网前缀 |
| backups | 备份记录 |
| audit_logs | 操作日志 |
| settings | 系统设置 |
| credentials | 设备凭证 |

## 认证与权限

- **认证方式**: JWT Bearer Token
- **权限模型**: RBAC（基于角色的访问控制）
- **默认用户**: admin，密码由 `INITIAL_ADMIN_PASSWORD` 环境变量指定（详见下方环境变量配置）

## 数据存储

### 前端（演示数据）
- 存储位置：浏览器 `localStorage`
- 预置演示数据：
  - 3个脱敏演示站点（Demo Site A、Demo Site B、Demo Lab）
  - 3条专线（互联网专线、MPLS、SD-WAN）
  - 4个IP子网和IP地址
  - 3台设备（交换机、防火墙、路由器）
  - 3次配置备份记录
  - 3个系统用户
  - 2条操作日志

### 后端（生产数据）
- 数据库：SQLite（开发）/ PostgreSQL（生产）
- Logo等配置存储到数据库，所有用户共享

## 设备配置采集

使用 Netmiko 实现网络设备连接：
- 支持设备类型：Cisco IOS、Huawei VRP、H3C、Juniper等
- 配置备份自动化
- 凭证加密存储

## 部署方式

### 开发环境
```bash
# 启动前端
cd frontend && npm run dev

# 启动后端
cd backend && source venv/bin/activate && uvicorn src.main:app --reload
```

### 生产环境
```bash
# 构建前端
cd frontend && npm run build

# 启动后端（带进程管理）
cd backend && source venv/bin/activate && uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 环境变量配置

复制环境变量模板并修改：

```bash
cp backend/.env.example backend/.env
```

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串（异步） | `sqlite+aiosqlite:///./cornerstone.db` |
| `DATABASE_URL_SYNC` | 数据库连接字符串（同步） | `sqlite:///./cornerstone.db` |
| `SECRET_KEY` | JWT 签名密钥（生产环境请更换为随机字符串） | `cornerstone-secret-key-...` |
| `ALGORITHM` | JWT 加密算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `480` |
| `INITIAL_ADMIN_PASSWORD` | 首次启动时 admin 用户的初始密码 | 未设置时使用开发默认值 |
| `CREDENTIAL_SECRET_KEY` | 设备凭证加密密钥（留空自动生成） | 空 |
| `DEBUG` | 调试模式 | `false` |
| `BACKUP_DIR` | 配置备份持久化目录 | `/opt/cornerstone/backups` |
| `CORS_ORIGINS` | 允许的前端来源（逗号分隔） | `http://localhost:5173` |
| `SSO__ENABLED` | 启用 SSO 登录 | `false` |

> **安全提醒**：生产环境部署前，请务必修改 `SECRET_KEY` 和 `INITIAL_ADMIN_PASSWORD`，并使用 PostgreSQL 作为数据库。

## 后续规划

- [ ] 完善设备配置采集功能
- [ ] 邮件通知集成（SMTP）
- [ ] Docker Compose 部署方案
- [ ] 完善与Zabbix/Grafana监控系统集成
- [ ] 增加更多预警规则
- [ ] 报表导出功能
- [ ] 多租户支持

## License

MIT License
