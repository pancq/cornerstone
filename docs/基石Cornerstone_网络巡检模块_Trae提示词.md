# 基石 Cornerstone · 网络巡检模块
## Trae 开发提示词

---

## 背景说明

当前项目已有完整前后端框架：
- 前端：Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- 后端：FastAPI + SQLAlchemy（异步）+ SQLite/PostgreSQL + JWT认证
- 现有相关模块：设备台账（devices）、站点（sites）、IP地址（ip_addresses）、预警中心（alerts）

本次任务：实现网络巡检模块，包含快速扫描（ICMP + TCP探活）和全量扫描（SNMP设备指纹采集 + 变更检测告警）。

安装依赖：
```bash
cd backend
pip install pysnmp==4.4.12 ping3==4.0.4
```

---

## 扫描类型设计

### 快速扫描（Quick Scan）
探测设备是否在线，ICMP + TCP 多维度判定，解决 Windows 禁 Ping 问题：

```
Step 1: ICMP Ping（ping3库）
Step 2: TCP端口探测（22/80/443/445/3389，socket标准库）
判定规则：ICMP响应 OR 任意TCP端口响应 → 在线
```

### 全量扫描（Full Scan）
先探活，对在线设备进一步 SNMP 采集，分两步：

```
Step 1: 同快速扫描，判断设备是否在线
Step 2: 在线设备执行 SNMP 查询
    第一步：采集 MIB-II 通用 OID（所有品牌通用）
    第二步：解析 sysObjectID 识别厂商品牌
    第三步：根据品牌采集对应私有 OID（CPU/内存）
```

---

## 数据模型

新建 `backend/src/models/inspection.py`：

```python
class InspectionTask(Base):
    """巡检任务配置"""
    __tablename__ = "inspection_tasks"
    id: int
    name: str                   # 任务名称
    scan_type: str              # quick（快速扫描）/ full（全量扫描）
    is_enabled: bool            # 是否启用定时执行
    cron_expr: str              # Cron表达式，如 "0 */4 * * *"
    # 扫描目标（三选一）
    target_type: str            # all_devices / site / ip_range
    site_id: int                # target_type=site 时使用
    ip_range: str               # target_type=ip_range 时使用，如 "192.0.2.0/24"
    # SNMP配置（全量扫描用）
    snmp_community: str         # SNMP Community，默认 "public"，加密存储
    snmp_version: str           # v1 / v2c / v3，默认 v2c
    snmp_timeout: int           # SNMP超时秒数，默认3
    snmp_retries: int           # 重试次数，默认1
    # TCP探测配置
    tcp_ports: str              # JSON数组，默认 "[22,80,443,445,3389]"
    tcp_timeout_ms: int         # TCP超时毫秒，默认2000
    # 并发控制
    max_concurrent: int         # 最大并发数，默认50
    # 告警配置
    alert_on_offline: bool      # 已知在线设备变离线时告警
    alert_on_new_device: bool   # 发现未登记设备时告警
    alert_on_fingerprint_change: bool  # 设备指纹变更时告警
    # 执行记录
    last_run_at: datetime
    last_run_status: str        # success / partial_fail / failed
    created_at: datetime
    updated_at: datetime

class InspectionResult(Base):
    """单次巡检执行记录"""
    __tablename__ = "inspection_results"
    id: int
    task_id: int                # 关联巡检任务
    scan_type: str              # quick / full
    trigger: str                # scheduled（定时）/ manual（手动）
    operator: str               # 手动触发时的操作人，定时填 "system"
    status: str                 # running / success / partial_fail / failed
    total_targets: int          # 扫描目标总数
    online_count: int           # 在线数量
    offline_count: int          # 离线数量
    new_device_count: int       # 新发现未登记设备数
    change_count: int           # 设备指纹变更数
    error_message: str          # 整体失败原因
    started_at: datetime
    finished_at: datetime
    duration_seconds: int

class InspectionDeviceResult(Base):
    """单台设备的巡检结果"""
    __tablename__ = "inspection_device_results"
    id: int
    result_id: int              # 关联 inspection_results.id
    ip_address: str             # 扫描的IP
    device_id: int              # 关联设备台账（可为空，未登记设备）
    is_online: bool
    detection_method: str       # icmp / tcp / none
    open_ports: str             # JSON数组，响应的TCP端口
    # SNMP采集结果（全量扫描）
    sys_descr: str              # 设备描述
    sys_name: str               # 设备主机名
    sys_object_id: str          # 厂商OID
    sys_up_time: int            # 运行时长（秒）
    sys_location: str           # 位置描述
    vendor: str                 # 识别出的厂商：cisco/huawei/h3c/juniper/fortinet/unknown
    cpu_usage: float            # CPU利用率（%），私有OID采集，失败时为 null
    memory_usage: float         # 内存利用率（%），失败时为 null
    # 变更检测
    is_new_device: bool         # 是否为未登记的新设备
    has_fingerprint_change: bool # 与上次全量扫描相比指纹是否变更
    change_detail: str          # 变更详情JSON，如 {"sys_name": ["old", "new"]}
    # 执行信息
    scan_duration_ms: int       # 本设备扫描耗时
    error_message: str          # 单设备失败原因
    scanned_at: datetime

class DeviceFingerprint(Base):
    """设备指纹快照（每次全量扫描后更新）"""
    __tablename__ = "device_fingerprints"
    id: int
    ip_address: str             # UNIQUE
    device_id: int              # 关联设备台账（可为空）
    sys_descr: str
    sys_name: str
    sys_object_id: str
    sys_location: str
    vendor: str
    last_seen_online: datetime
    last_full_scan_at: datetime
    updated_at: datetime
```

---

## 核心扫描服务

新建 `backend/src/services/inspector.py`：

### SNMP OID 配置

```python
# MIB-II 通用 OID（所有品牌）
MIB2_OIDS = {
    "sys_descr":     "1.3.6.1.2.1.1.1.0",
    "sys_object_id": "1.3.6.1.2.1.1.2.0",
    "sys_up_time":   "1.3.6.1.2.1.1.3.0",
    "sys_name":      "1.3.6.1.2.1.1.5.0",
    "sys_location":  "1.3.6.1.2.1.1.6.0",
}

# 厂商识别：sysObjectID 前缀 → 厂商名
VENDOR_OID_MAP = {
    "1.3.6.1.4.1.9":     "cisco",
    "1.3.6.1.4.1.2011":  "huawei",
    "1.3.6.1.4.1.25506": "h3c",
    "1.3.6.1.4.1.2636":  "juniper",
    "1.3.6.1.4.1.12356": "fortinet",
}

# 厂商私有 OID（CPU/内存）
VENDOR_PERF_OIDS = {
    "cisco": {
        "cpu_usage":    "1.3.6.1.4.1.9.2.1.56.0",
        "memory_usage": "1.3.6.1.4.1.9.9.48.1.1.1.5.1",
    },
    "huawei": {
        "cpu_usage":    "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5.1",
        "memory_usage": "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.7.1",
    },
    "h3c": {
        "cpu_usage":    "1.3.6.1.4.1.25506.2.6.1.1.1.1.6.1",
        "memory_usage": "1.3.6.1.4.1.25506.2.6.1.1.1.1.8.1",
    },
    "juniper": {
        "cpu_usage":    "1.3.6.1.4.1.2636.3.1.13.1.8.1.1.0",
        "memory_usage": "1.3.6.1.4.1.2636.3.1.13.1.11.1.1.0",
    },
    "fortinet": {
        "cpu_usage":    "1.3.6.1.4.1.12356.101.4.1.3.0",
        "memory_usage": "1.3.6.1.4.1.12356.101.4.1.4.0",
    },
}
```

### 探活逻辑

```python
async def probe_online(ip: str, tcp_ports: list[int], timeout_ms: int) -> ProbeResult:
    """
    多维度探活：ICMP + TCP
    返回：{ is_online, method, open_ports, duration_ms }

    执行顺序：
    1. ICMP Ping（ping3，超时1秒）
    2. 若ICMP失败，并发探测所有TCP端口（asyncio + socket）
    3. 任意方式成功 → is_online=True

    注意：
    - ICMP 和 TCP 并发执行（不串行），取最快响应
    - Windows禁Ping时依靠TCP 445/3389判定在线
    - 所有异常静默捕获，不抛出，保证单IP失败不影响整体
    """

async def snmp_get(ip: str, oids: dict, community: str,
                   version: str, timeout: int, retries: int) -> dict:
    """
    SNMP GET查询，使用pysnmp异步接口
    返回：{ oid_key: value, ... }，查询失败的OID值为None
    不抛出异常，所有错误返回空字典

    注意：
    - pysnmp 使用 asyncio 异步接口（getCmd）
    - v2c 使用 CommunityData，v3 使用 UsmUserData
    - OID解析：sysUpTime 转换为秒数（原始值为 1/100秒）
    """

def identify_vendor(sys_object_id: str) -> str:
    """
    根据 sysObjectID 识别厂商
    遍历 VENDOR_OID_MAP，匹配前缀
    未匹配返回 "unknown"
    """

async def collect_device_snmp(ip: str, config: SNMPConfig) -> SNMPResult:
    """
    全量扫描的SNMP采集主函数：
    1. 采集 MIB2_OIDS（通用，必须）
    2. 解析 sysObjectID 识别厂商
    3. 若厂商已知，尝试采集 VENDOR_PERF_OIDS（失败不报错，cpu/memory置None）
    4. 返回完整结果
    """

async def detect_fingerprint_change(ip: str, new_result: SNMPResult,
                                     db: AsyncSession) -> ChangeDetail:
    """
    与 device_fingerprints 表中上次记录对比：
    对比字段：sys_descr / sys_name / sys_object_id / sys_location / vendor
    返回：{ has_change: bool, changed_fields: { field: [old_val, new_val] } }
    """
```

### 巡检执行主流程

```python
async def run_inspection(task: InspectionTask, trigger: str,
                         operator: str, db: AsyncSession,
                         ws_callback=None) -> InspectionResult:
    """
    巡检执行主函数：
    1. 根据 target_type 生成目标IP列表：
        all_devices → 查 devices 表所有 mgmt_ip
        site        → 查指定站点下所有设备的 mgmt_ip
        ip_range    → 枚举网段内所有IP（ipaddress.ip_network）
    2. 创建 InspectionResult 记录（status=running）
    3. 使用 asyncio.Semaphore(max_concurrent) 并发扫描
    4. 每扫描完一台设备：
        - 写入 InspectionDeviceResult
        - 若 ws_callback 不为空，推送实时进度
        - 处理告警逻辑（见下方）
    5. 全量扫描时更新 device_fingerprints 表
    6. 更新 InspectionResult 为最终状态
    """

async def process_alerts(device_result: InspectionDeviceResult,
                          task: InspectionTask, db: AsyncSession):
    """
    每台设备扫描完后的告警处理：
    1. 设备离线告警（alert_on_offline=True）：
        - 查 device_fingerprints，上次在线但本次离线 → 写告警
        - 告警级别：warning
        - 告警内容：「设备 {device_name}（{ip}）已离线，上次在线：{last_seen}」
    2. 新设备发现告警（alert_on_new_device=True）：
        - 该IP不在 devices 表也不在 device_fingerprints 表 → 写告警
        - 告警级别：info
        - 告警内容：「发现未登记设备，IP：{ip}，系统描述：{sys_descr}」
    3. 指纹变更告警（alert_on_fingerprint_change=True）：
        - has_fingerprint_change=True → 写告警
        - 告警级别：warning
        - 告警内容：「设备 {device_name}（{ip}）指纹变更：{changed_fields}」
    """
```

---

## 后端 API

新建 `backend/src/api/inspection.py`，在 `main.py` 中注册：

```
# 巡检任务管理
GET    /api/v1/inspection/tasks              获取任务列表
POST   /api/v1/inspection/tasks              创建任务
PUT    /api/v1/inspection/tasks/{id}         编辑任务
DELETE /api/v1/inspection/tasks/{id}         删除任务
PATCH  /api/v1/inspection/tasks/{id}/toggle  启用/停用

# 手动触发
POST /api/v1/inspection/tasks/{id}/run
    立即触发执行，返回 result_id
    Body: { "scan_type": "quick" | "full" }

# 执行记录
GET /api/v1/inspection/results
    获取巡检执行历史，支持按 task_id/scan_type/status 筛选，分页

GET /api/v1/inspection/results/{result_id}
    获取单次巡检详情（含统计信息）

GET /api/v1/inspection/results/{result_id}/devices
    获取该次巡检中所有设备的扫描结果，支持按
    is_online/is_new_device/has_fingerprint_change 筛选，分页

# 设备指纹
GET /api/v1/inspection/fingerprints
    获取设备指纹列表（最新快照），支持按 vendor/ip 搜索

GET /api/v1/inspection/fingerprints/{ip}
    获取指定IP的指纹详情 + 历史变更记录

# WebSocket 实时进度
WebSocket /api/v1/inspection/ws/{result_id}
    推送巡检进度，消息格式：

    # 进度更新
    {
        "type": "progress",
        "total": 100,
        "scanned": 45,
        "online": 30,
        "offline": 15,
        "percent": 45.0,
        "current_ip": "192.0.2.46"
    }

    # 单设备结果
    {
        "type": "device_result",
        "ip": "192.0.2.5",
        "device_name": "SW-DEMO-01",
        "is_online": true,
        "method": "tcp",
        "open_ports": [22, 445],
        "vendor": "cisco",
        "sys_name": "SW-DEMO-CORE-01",
        "is_new_device": false,
        "has_fingerprint_change": false
    }

    # 发现告警事件
    {
        "type": "alert",
        "level": "warning",
        "message": "发现未登记设备，IP：192.0.2.88"
    }

    # 完成
    {
        "type": "done",
        "total": 100,
        "online": 68,
        "offline": 32,
        "new_devices": 2,
        "changes": 1,
        "duration_seconds": 45.2
    }
```

---

## 定时调度

在现有 `backend/src/tasks/` 目录下新建 `inspection_scheduler.py`：

```python
# 使用 APScheduler AsyncIOScheduler（复用现有备份调度器的模式）
# 应用启动时加载所有 is_enabled=True 的巡检任务并注册
# 实现：
async def run_scheduled_inspection(task_id: int)
async def reload_inspection_tasks()  # 任务增删改后调用，动态更新
```

---

## 前端实现

### 导航结构

```
网络巡检（侧边栏一级菜单，图标：雷达/扫描）
├── 巡检概览      /inspection/dashboard
├── 巡检任务      /inspection/tasks
├── 巡检记录      /inspection/results
└── 设备指纹      /inspection/fingerprints
```

---

### 页面1：巡检概览 `/inspection/dashboard`

```
布局：顶部4个统计卡片 + 下方图表区

统计卡片：
- 在线设备数 / 总设备数（绿色，点击跳转记录页过滤在线）
- 离线设备数（红色，点击跳转过滤离线）
- 今日发现新设备数（橙色）
- 近7天指纹变更次数（蓝色）

图表区（两列）：
左：在线率趋势折线图（近7天，按天统计在线率%，使用ECharts或Element Plus图表）
右：厂商分布饼图（Cisco/华为/H3C/Juniper/未知 各占比）

下方：最近一次巡检结果摘要卡片
- 执行时间 / 扫描类型 / 用时 / 在线N台/离线N台
- 「查看详情」按钮
```

---

### 页面2：巡检任务 `/inspection/tasks`

```
表格列：
任务名称 / 扫描类型（badge：快速扫描-蓝/全量扫描-绿）/ 扫描目标 /
执行频率 / 上次执行时间 / 上次状态 / 启用开关 / 操作

操作列：立即执行（下拉：快速扫描/全量扫描）/ 编辑 / 删除

新增/编辑任务弹窗（分步表单，共3步）：
Step 1 - 基本配置：
  - 任务名称
  - 扫描目标类型（单选）：
      ● 全部设备（扫描设备台账中所有设备的管理IP）
      ● 按站点（下拉选择站点）
      ● 指定IP段（输入 CIDR，如 192.0.2.0/24）
  - 执行频率（预设选项 + 自定义Cron）：
      每4小时 / 每天凌晨2点 / 每天凌晨4点 / 每周一 / 自定义

Step 2 - 扫描配置：
  - 探测超时（TCP超时，默认2000ms，滑块）
  - 并发数（默认50，滑块，最大200）
  - TCP探测端口（多选Tag输入，默认22/80/443/445/3389）
  - SNMP配置（仅全量扫描显示）：
      Community（默认public，加密存储）
      SNMP版本（v1/v2c，默认v2c）
      超时（默认3秒）/ 重试次数（默认1次）

Step 3 - 告警配置：
  - □ 已知设备变为离线时告警
  - □ 发现未登记的新设备时告警
  - □ 设备指纹发生变更时告警（仅全量扫描）
  底部预览：告警将推送到预警中心，可在系统设置中配置邮件通知

立即执行后弹出「巡检进度」对话框（见下方组件）
```

---

### 页面3：巡检记录 `/inspection/results`

```
顶部筛选：时间范围 / 任务名 / 扫描类型 / 状态

表格列：
执行时间 / 任务名 / 扫描类型 / 触发方式（定时/手动）/
在线N/总N / 新设备 / 指纹变更 / 状态 / 用时 / 操作

点击「查看详情」进入单次巡检详情页：

详情页布局：
顶部：本次巡检摘要（统计卡片 + 基本信息）
筛选Tab：全部 / 在线 / 离线 / 新设备 / 有变更

设备结果表格列：
IP地址 / 设备名（无则显示「未登记」红色） / 在线状态 /
探测方式 / 厂商 / 主机名（SNMP获取） / CPU% / 内存% /
指纹变更 / 扫描耗时

指纹变更展示：
点击「查看变更」弹出对话框，显示变更字段对比：
字段名 | 变更前 | 变更后
sys_name | SW-OLD-01 | SW-NEW-01
```

---

### 页面4：设备指纹 `/inspection/fingerprints`

```
功能：展示每台设备最新的SNMP指纹快照

顶部筛选：按厂商 / 按站点 / IP搜索

表格列：
IP地址 / 设备名 / 厂商（带图标） / 主机名 / 系统描述（截断） /
最后在线时间 / 最后全量扫描时间 / 操作

操作：查看历史变更

历史变更抽屉（右侧滑出）：
时间线展示每次全量扫描中该设备的指纹变更记录：
- 日期
- 变更字段列表（变更前→变更后）
- 若无变更显示「无变化」
```

---

### 巡检进度组件 `InspectionProgress.vue`

```
复用配置备份 WebSocket 进度组件的模式，新建：
frontend/src/features/inspection/components/InspectionProgress.vue

Element Plus Dialog：
- 标题：「正在巡检 - {任务名}」+ 扫描类型badge
- 环形进度条：百分比 + 「已扫描N/总N」
- 统计行：在线 N（绿）/ 离线 N（红）/ 新设备 N（橙）/ 变更 N（蓝）
- 当前正在扫描的IP（小字灰色，实时更新）
- 实时日志滚动区（最新20条）：
    绿色 ✓ {ip} {device_name} 在线（{method}）
    红色 ✗ {ip} 离线
    橙色 ⚡ {ip} 新设备发现
    蓝色 ~ {ip} {device_name} 指纹变更
- 告警提示（若有）：黄色警告条，显示告警内容
- 底部：「取消」（关闭WebSocket）/ 完成后变为「查看详情」
```

---

## 开发顺序

**Step 1**：数据库 migration（4张新表）+ pysnmp/ping3 依赖安装验证

**Step 2**：`inspector.py` 核心服务
  - `probe_online`（ICMP + TCP）
  - `snmp_get`（pysnmp异步接口）
  - `identify_vendor`（sysObjectID识别）
  - `collect_device_snmp`（完整采集流程）

**Step 3**：`detect_fingerprint_change` + `process_alerts` 告警逻辑

**Step 4**：`run_inspection` 主流程 + WebSocket 进度推送

**Step 5**：巡检任务 CRUD API + APScheduler 调度注册

**Step 6**：其余 API 接口（执行记录、设备指纹、WebSocket）

**Step 7**：前端路由 + 巡检进度组件（WebSocket接入）

**Step 8**：巡检任务管理页（分步表单）

**Step 9**：巡检概览页（统计卡片 + 图表）

**Step 10**：巡检记录页 + 单次详情页

**Step 11**：设备指纹页 + 历史变更抽屉

---

## 注意事项

- pysnmp 异步接口使用 `hlapi.asyncio` 模块，注意 v4.4.x 和 v6.x API 差异，统一使用 4.4.12
- SNMP Community 字符串加密存储（复用 `crypto.py` 的 `encrypt_password`）
- 私有 OID（CPU/内存）采集失败时静默忽略，对应字段置 None，不影响整体流程
- sysUpTime OID 返回值单位为 1/100 秒（TimeTicks），需除以 100 转换为秒
- 扫描 IP 段时跳过网络地址和广播地址（`ipaddress.ip_network().hosts()`）
- 设备台账中没有管理IP的设备跳过，记录跳过原因
- 同一时间同一任务不允许重复执行，触发时检查是否有 status=running 的记录
- WebSocket 连接断开时巡检任务继续在后台执行，结果正常写库
- 所有巡检执行操作写入 audit_logs 表
- 厂商私有 OID 的 CPU/内存值各厂商含义略有不同（有的是百分比，有的是绝对值），采集后统一换算为百分比（0-100）存储，换算失败置 None
