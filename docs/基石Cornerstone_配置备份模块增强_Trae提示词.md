# 基石 Cornerstone · 设备配置备份模块增强
## Trae 开发提示词

---

## 背景说明

当前项目已有完整前后端框架：
- 前端：Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- 后端：FastAPI + SQLAlchemy（异步）+ SQLite/PostgreSQL + JWT认证
- 配置备份现有功能：备份历史记录展示、手动备份记录、配置查看/下载、相邻版本Diff对比（均为前端模拟数据）

本次任务：将配置备份模块从「前端模拟」升级为「真实可用」，实现SSH真实采集、定时自动备份、变更检测告警、版本管理增强、凭证安全管理。

请严格遵循现有代码风格，复用已有组件、API封装、Store模式，不重写已有功能。

---

## 功能一：SSH真实采集 + 凭证加密管理

### 后端

**1. 安装依赖**（追加到 `requirements.txt`）：
```
netmiko==4.3.0
cryptography==41.0.0
paramiko==3.3.1
```

**2. 凭证加密工具** 新建 `backend/src/utils/crypto.py`：
```python
# 使用 cryptography 库的 Fernet 对称加密
# 加密密钥从环境变量 CREDENTIAL_SECRET_KEY 读取，启动时若不存在自动生成并写入 .env
# 实现以下函数：
def encrypt_password(plain_text: str) -> str  # 加密，返回base64字符串
def decrypt_password(cipher_text: str) -> str  # 解密，返回明文
# 前端永远不返回明文密码，只返回 "********"
```

**3. 凭证数据模型**（修改现有 `credentials` 表，确认字段完整）：
```python
class Credential(Base):
    __tablename__ = "credentials"
    id: int
    name: str              # 凭证名称，如「华为核心设备组」
    device_id: int         # 关联设备（可为空，表示共享凭证）
    protocol: str          # ssh / telnet
    port: int              # 默认22
    username: str
    password: str          # 加密存储，AES-256
    enable_password: str   # enable密码（Cisco等需要），加密存储，可为空
    auth_type: str         # password / key（密钥认证）
    private_key: str       # SSH私钥内容，加密存储，可为空
    jump_host: str         # 跳板机IP，可为空
    jump_port: int         # 跳板机端口，默认22
    jump_username: str     # 跳板机用户名
    jump_password: str     # 跳板机密码，加密存储
    description: str
    created_at: datetime
    updated_at: datetime
```

**4. 核心采集服务** 新建 `backend/src/services/backup_collector.py`：
```python
# 支持厂商及对应Netmiko device_type：
VENDOR_MAP = {
    "cisco_ios":    "cisco_ios",
    "cisco_nxos":   "cisco_nxos",
    "huawei_vrp":   "huawei_vrp",
    "h3c":          "hp_comware",
    "juniper":      "juniper_junos",
    "fortinet":     "fortinet",
    "linux":        "linux",
}

# 每个厂商的采集命令：
BACKUP_COMMANDS = {
    "cisco_ios":   "show running-config",
    "cisco_nxos":  "show running-config",
    "huawei_vrp":  "display current-configuration",
    "h3c":         "display current-configuration",
    "juniper":     "show configuration",
    "fortinet":    "show full-configuration",
    "linux":       "cat /etc/network/interfaces",
}

async def collect_device_config(device: Device, credential: Credential) -> CollectResult:
    """
    使用Netmiko SSH连接设备采集配置
    返回：
    {
        "success": True/False,
        "config_content": "...",   # 配置文本
        "error_message": None,     # 失败原因
        "duration_ms": 1200        # 耗时
    }
    步骤：
    1. 先Ping检测设备可达性（ping3库），不可达直接返回失败
    2. 构造Netmiko连接参数（支持跳板机：ssh_config_file or ProxyCommand）
    3. 连接设备，发送采集命令
    4. 超时时间：连接30秒，命令执行60秒
    5. 断开连接
    6. 若发生任何异常，捕获并返回具体错误信息
    """

async def detect_config_change(old_content: str, new_content: str) -> ChangeResult:
    """
    对比两次配置差异
    返回：
    {
        "has_change": True/False,
        "added_lines": 5,          # 新增行数
        "removed_lines": 3,        # 删除行数
        "diff_text": "...",        # unified diff格式文本
        "change_summary": "新增5行，删除3行"
    }
    使用Python标准库 difflib.unified_diff 实现
    """
```

**5. 备份数据模型**（修改现有 `backups` 表）：
```python
class Backup(Base):
    __tablename__ = "backups"
    id: int
    device_id: int          # 关联设备
    version: int            # 版本号，同设备自增
    content: str            # 配置内容（建议存文件路径，大配置不入DB）
    content_hash: str       # SHA256哈希，用于快速判断是否变更
    trigger: str            # manual（手动）/ scheduled（定时）/ pre_change（变更前）
    operator: str           # 触发人（定时任务填"system"）
    status: str             # success / failed
    error_message: str      # 失败原因
    has_change: bool        # 与上一版本相比是否有变更
    change_summary: str     # 变更摘要，如「新增5行，删除3行」
    tag: str                # 人工标签，如「割接前备份」
    duration_ms: int        # 采集耗时
    created_at: datetime
```

**6. 备份API接口**（修改现有 `backend/src/api/backups.py`，补充以下接口）：

```
POST /api/v1/backups/trigger
    手动触发单台设备备份
    Body: { "device_id": 1, "tag": "割接前备份" }
    异步执行，立即返回 task_id，通过WebSocket推送结果

POST /api/v1/backups/trigger-batch
    批量触发多台设备备份
    Body: { "device_ids": [1,2,3], "tag": "" }

GET /api/v1/backups/
    备份历史列表，支持按device_id/status/trigger/has_change筛选，分页

GET /api/v1/backups/{id}/content
    获取指定备份的完整配置内容

GET /api/v1/backups/diff
    任意两个版本Diff对比
    Query: ?backup_id_a=1&backup_id_b=2
    返回unified diff结果

PATCH /api/v1/backups/{id}/tag
    给备份打标签/修改备注
    Body: { "tag": "核心交换机升级前" }

DELETE /api/v1/backups/{id}
    删除单条备份记录

GET /api/v1/credentials/
    获取凭证列表（密码字段返回"********"，不返回明文）

POST /api/v1/credentials/
    创建凭证（密码加密存储）

PUT /api/v1/credentials/{id}
    编辑凭证

DELETE /api/v1/credentials/{id}
    删除凭证

POST /api/v1/credentials/{id}/test
    测试凭证连通性（SSH连接测试，不采集配置）

WebSocket /api/v1/backups/ws/{task_id}
    推送备份任务进度
    消息格式：
    { "type": "progress", "device_id": 1, "device_name": "SW-DEMO-01", "status": "connecting" }
    { "type": "result", "device_id": 1, "success": true, "has_change": true, "change_summary": "新增3行" }
    { "type": "done", "total": 5, "success": 4, "failed": 1 }
```

---

## 功能二：定时自动备份

### 后端

**备份任务数据模型** 新建 `backend/src/models/backup_task.py`：
```python
class BackupTask(Base):
    __tablename__ = "backup_tasks"
    id: int
    name: str               # 任务名称
    is_enabled: bool        # 是否启用
    cron_expr: str          # Cron表达式，如 "0 2 * * *"（每天凌晨2点）
    device_ids: str         # JSON数组，如 "[1,2,3]"，为空表示全部设备
    site_id: int            # 按站点批量，与device_ids二选一
    credential_id: int      # 使用哪套凭证
    retention_count: int    # 保留最近N个版本，默认30
    retention_days: int     # 保留最近N天，默认90，与retention_count取较小值
    notify_on_change: bool  # 配置变更时是否发送告警
    notify_on_fail: bool    # 备份失败时是否发送告警
    last_run_at: datetime
    last_run_status: str    # success / partial_fail / failed
    created_at: datetime
```

**定时调度** 新建 `backend/src/tasks/backup_scheduler.py`：
```python
# 使用 APScheduler AsyncIOScheduler
# 应用启动时加载所有 is_enabled=True 的任务，注册到调度器
# 实现以下函数：

async def run_backup_task(task_id: int):
    """执行一次备份任务：查设备列表 → 并发采集（最多10台并发）→ 写备份记录 → 触发变更检测 → 发送告警"""

async def reload_tasks():
    """重新从DB加载所有任务（任务增删改后调用）"""

async def execute_retention_policy(device_id: int, retention_count: int, retention_days: int):
    """执行保留策略，删除超出限制的旧备份"""
```

**备份任务API** 新建 `backend/src/api/backup_tasks.py`：
```
GET    /api/v1/backup-tasks/         获取任务列表
POST   /api/v1/backup-tasks/         创建任务（自动注册到调度器）
PUT    /api/v1/backup-tasks/{id}     编辑任务（重新注册调度器）
DELETE /api/v1/backup-tasks/{id}     删除任务
PATCH  /api/v1/backup-tasks/{id}/toggle   启用/停用任务
POST   /api/v1/backup-tasks/{id}/run-now  立即执行一次
GET    /api/v1/backup-tasks/{id}/history  该任务的执行历史（最近20次）
```

---

## 功能三：变更检测告警

### 后端

**变更告警逻辑**（在 `backup_collector.py` 中实现，每次备份完自动触发）：
```python
async def process_backup_change_alert(backup: Backup, task: BackupTask):
    """
    每次备份成功后调用：
    1. 取该设备最近一次成功备份的content_hash
    2. 与本次对比，若hash不同则has_change=True
    3. 调用detect_config_change获取diff详情
    4. 若 task.notify_on_change=True 且 has_change=True：
       - 写入 alerts 表（复用现有告警模型）
       - 可选：发送邮件（若SMTP已配置）
    5. 过滤规则：忽略含特定关键词的变更行
       默认忽略包含以下内容的行变更：
       "Last configuration change", "ntp clock-period", "!Time:"
    """
```

**免打扰规则配置**（在系统设置中追加，`settings` 表新增字段）：
```
backup_ignore_patterns: str  # JSON数组，忽略的正则表达式列表
默认值: ["Last configuration change", "ntp clock-period", "!Time:"]
```

### 前端

**预警中心更新**（在现有预警中心页面新增「配置变更」分组）：
```
表格列：设备名 / 站点 / 变更时间 / 变更摘要 / 操作
操作：「查看Diff」→ 跳转到该备份的Diff页面
支持按设备/站点/时间范围筛选
```

---

## 功能四：版本管理增强

### 前端

**备份历史页面增强** `frontend/src/features/backups/BackupList.vue`：

```
页面布局：
- 左侧：设备树（按站点分组，点击筛选右侧列表）
- 右侧上方：筛选栏（时间范围、状态、触发方式、是否有变更）
- 右侧：备份记录表格
    列：版本号 / 设备名 / 备份时间 / 触发方式 / 变更状态 / 标签 / 状态 / 操作
    变更状态：有变更显示橙色「有变更」badge，无变更显示灰色「无变更」
    操作：查看配置 / 打标签 / 对比 / 下载 / 删除

多版本Diff对比交互：
- 表格支持复选框，选中恰好2条记录时顶部出现「对比选中版本」按钮
- 点击后打开Diff对话框

Diff展示组件 BackupDiff.vue：
- 左右分栏布局（older版本在左，newer版本在右）
- 使用 diff2html 或自实现：
    新增行：绿色背景 #f0fff4，行首显示「+」
    删除行：红色背景 #fff0f0，行首显示「-」
    上下文行：正常展示，默认折叠（仅展示变更行前后3行）
- 顶部摘要：「新增 N 行，删除 N 行」
- 右上角：「下载Diff」按钮，导出.diff文件

打标签功能：
- 备份列表每行有「打标签」按钮
- 点击弹出小popover输入框，输入标签文字确认
- 标签显示在版本号旁边，支持删除标签
```

---

## 功能五：凭证管理页面

新建页面 `frontend/src/features/backups/CredentialList.vue`：

```
路由：/backups/credentials
入口：配置备份模块左侧导航或顶部Tab增加「凭证管理」

表格列：凭证名称 / 协议 / 端口 / 用户名 / 跳板机 / 关联设备数 / 操作
密码列不展示，操作列有「查看/编辑」时密码框显示"********"，
编辑时留空表示不修改密码

新增/编辑弹窗字段：
- 凭证名称（必填）
- 协议：SSH / Telnet（单选）
- 端口（默认22）
- 用户名（必填）
- 密码（新增必填，编辑时留空不修改）
- Enable密码（可选，Cisco设备用）
- 认证方式：密码 / SSH密钥（切换时显示对应输入框）
- 私钥内容（textarea，认证方式为密钥时显示）
- 跳板机配置（折叠面板，展开后填写跳板机IP/端口/用户名/密码）
- 描述

底部「测试连接」按钮：
- 点击弹出小对话框输入一个测试设备IP
- 调用 POST /api/v1/credentials/{id}/test
- 显示连接结果：成功（绿色✓ + 耗时）/ 失败（红色✗ + 错误信息）
```

---

## 功能六：备份任务管理页面

新建页面 `frontend/src/features/backups/BackupTaskList.vue`：

```
路由：/backups/tasks
入口：配置备份模块左侧导航增加「备份任务」

表格列：任务名 / 覆盖设备 / 执行频率 / 上次执行 / 上次状态 / 启用状态 / 操作
启用状态：El-Switch 开关，直接调用 toggle 接口

新增/编辑任务弹窗：
- 任务名称
- 设备范围：全部设备 / 按站点 / 指定设备（三选一，后两项展示对应选择器）
- 使用凭证：下拉选择已有凭证
- 执行频率（下拉预设 + 自定义Cron）：
    每天凌晨2点 / 每天凌晨4点 / 每6小时 / 每周一凌晨2点 / 自定义Cron
    选「自定义Cron」时展示输入框 + Cron表达式说明
- 备份保留：保留最近 N 个版本（默认30）/ 保留最近 N 天（默认90）
- 告警设置：
    □ 配置发生变更时告警
    □ 备份失败时告警
- 操作按钮：保存 / 立即执行一次

任务执行历史抽屉（点击「执行历史」）：
- 最近20次执行记录
- 列：执行时间 / 触发方式 / 成功设备数 / 失败设备数 / 执行耗时
- 点击每条记录展开详情：各设备的备份结果
```

---

## 首页仪表盘更新

在现有仪表盘「配置备份」统计卡片区域更新：
```
今日备份：成功 N 台 / 失败 N 台（点击跳转备份历史，过滤今日）
配置变更：近7天发现变更 N 次（点击跳转预警中心变更分组）
最近失败：若有失败设备，显示橙色警告 + 设备名列表（最多3条）
```

---

## 开发顺序

请按以下顺序实现，每步完成后验证再继续：

**Step 1**：`crypto.py` 加密工具 + 凭证表migration
**Step 2**：`backup_collector.py` 核心采集服务（Netmiko SSH采集 + 变更检测）
**Step 3**：备份表migration（新增字段）+ 手动触发备份API + WebSocket进度推送
**Step 4**：定时备份任务模型 + APScheduler调度 + 任务CRUD接口
**Step 5**：变更告警逻辑 + 预警中心「配置变更」分组
**Step 6**：前端凭证管理页面
**Step 7**：前端备份历史页面增强（任意版本Diff + 打标签）
**Step 8**：前端备份任务管理页面
**Step 9**：首页仪表盘备份统计更新

---

## 注意事项

- Netmiko连接超时设置：conn_timeout=30, read_timeout=60，避免卡死
- 所有密码字段：入库前加密，出库后返回"********"，API层统一处理，不依赖前端自觉
- 配置内容较大时（>100KB），存文件系统而非数据库字段，DB只存文件路径；小于100KB直接存DB
- 文件存储路径：`./data/backups/{device_id}/{backup_id}.txt`
- content_hash用于快速判断变更（SHA256），避免每次都全文diff
- APScheduler任务在应用启动时注册，任务增删改时调用reload_tasks()动态更新，不需要重启服务
- 跳板机支持：使用Netmiko的ssh_config_file参数或paramiko ProxyCommand实现二跳SSH
- scapy/ARP相关不在本模块，本模块只用ping3做可达性预检
- 所有写操作写入audit_logs表（复用现有日志工具函数）
- Diff展示优先使用 `diff2html` 前端库（npm install diff2html），样式更美观
