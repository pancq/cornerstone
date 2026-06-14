# 基石 Cornerstone · IPAM模块功能增强
## Trae 开发提示词

---

## 背景说明

当前项目已有完整的前后端框架：
- 前端：Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- 后端：FastAPI + SQLAlchemy（异步）+ SQLite/PostgreSQL + JWT认证
- IPAM现有功能：子网列表、IP分配、使用率展示、冲突拦截、CSV导入

本次任务是在现有基础上**增强IPAM模块**，新增以下4个功能：

1. IP方块矩阵可视化
2. IP扫描探活
3. VLAN管理
4. IP到期自动回收提醒å

请严格遵循现有代码风格，复用已有组件、API封装、Store模式，不要重写已有功能。

---

## 功能一：IP方块矩阵可视化

### 效果描述
在子网详情页（`/ipam/prefixes/:id`）顶部，将子网内所有IP以方块矩阵形式展示，类似热力图，替代纯文字列表，让运维人员一眼看出哪些IP在用、哪些空闲。

### 前端组件

新建 `frontend/src/features/ipam/components/IpMatrix.vue`：

```
功能要求：
- 将子网内所有可用IP按顺序排列成方块网格（每行16个）
- 每个方块代表一个IP地址，宽高各20px，间距2px
- 颜色规则：
    已分配 + 在线（扫描确认）→ 绿色 #67C23A
    已分配 + 离线/未扫描     → 蓝色 #409EFF
    未分配（空闲）           → 灰色 #DCDFE6
    预留（Reserved）         → 黄色 #E6A23C
    已分配 + 扫描失败         → 红色 #F56C6C
- 鼠标悬停方块显示 Element Plus Tooltip，内容：
    IP地址 / 状态 / 设备名（若有）/ 最后在线时间（若有）
- 点击方块：
    已分配IP → 弹出IP详情抽屉（复用现有详情组件）
    空闲IP → 弹出「快速分配」对话框，预填该IP地址
- 方块数量超过256时（/16以上大网段），自动折叠为按/24子块展示，点击展开
- 组件接收 props: { prefixId: number, ipList: IpAddress[] }
- 矩阵下方展示图例（色块+文字说明）
```

### 后端无需改动
复用现有 `GET /api/v1/ipam/addresses?prefix_id={id}` 接口即可。

---

## 功能二：IP扫描探活

### 功能描述
对子网内的IP地址进行多维度在线状态探测，综合判断每个IP是否真实在线，结果实时回显到前端，并更新IpMatrix的颜色状态。

### 探活策略（按优先级）
```
ARP探测（局域网最准，不受防火墙影响）
  ↓ 若不可达（跨网段）
TCP端口探测（Windows禁Ping时有效）
  探测端口：22(SSH), 80(HTTP), 443(HTTPS), 445(SMB), 3389(RDP)
  只要任意一个端口响应 → 判定在线
  ↓ 若均无响应
ICMP Ping
  ↓ 若无响应
判定为离线（但不代表设备不存在，可能防火墙屏蔽）
```

**注意**：Windows默认禁止Ping但通常开放3389(RDP)或445(SMB)，必须包含这两个端口。

### 后端新增

**1. 数据库新增字段**（修改现有 `ip_addresses` 表，Alembic migration）：
```python
# 在现有IpAddress模型中新增：
is_online: bool = Column(Boolean, nullable=True)           # 是否在线
last_seen_at: datetime = Column(DateTime, nullable=True)   # 最后在线时间
scan_method: str = Column(String(20), nullable=True)       # 探测方式: icmp/tcp/arp
open_ports: str = Column(String(200), nullable=True)       # 响应的TCP端口
mac_address: str = Column(String(50), nullable=True)       # ARP获取的MAC
last_scanned_at: datetime = Column(DateTime, nullable=True) # 最后扫描时间
```

**2. 新建扫描服务** `backend/src/services/scanner.py`：
```python
# 实现以下函数：

async def probe_single_ip(ip: str, tcp_ports: list[int], timeout: float) -> dict:
    """
    多维度探测单个IP，返回：
    {
        "ip": "192.0.2.1",
        "is_online": True/False,
        "method": "tcp/icmp/arp/none",
        "open_ports": [22, 445],
        "mac_address": "aa:bb:cc:dd:ee:ff" or None,
        "duration_ms": 120
    }
    """

async def scan_prefix(prefix_network: str, ip_records: list, config: ScanConfig) -> AsyncGenerator:
    """
    扫描整个子网，通过asyncio.Semaphore控制并发（默认50）
    每扫描完一个IP立即yield结果，供WebSocket实时推送
    """

# 工具函数：
async def _ping_icmp(ip: str, timeout: float) -> bool   # 使用ping3库
async def _probe_tcp(ip: str, ports: list, timeout: float) -> list[int]  # 使用asyncio socket
async def _probe_arp(ip: str, timeout: float) -> tuple[bool, str]  # 使用scapy，失败时静默降级
```

**3. 新增API接口** `backend/src/api/ipam.py`（在现有文件中追加）：

```
POST /api/v1/ipam/prefixes/{prefix_id}/scan
    触发手动扫描，返回 task_id
    Body: { "tcp_ports": [22,80,443,445,3389], "timeout_ms": 2000, "max_concurrent": 50 }

GET /api/v1/ipam/scan/tasks
    获取扫描任务列表（扫描历史）

GET /api/v1/ipam/addresses/{ip_id}/scan-history
    获取单个IP的历史扫描记录

WebSocket /api/v1/ipam/ws/scan/{task_id}
    实时推送扫描进度，消息格式：
    进度：{ "type": "progress", "total": 254, "scanned": 45, "online": 12, "percent": 17.7, "current_ip": "192.0.2.46" }
    完成：{ "type": "done", "total": 254, "online": 38, "offline": 216, "duration_seconds": 12.4 }
    单IP结果：{ "type": "result", "ip": "192.0.2.5", "is_online": true, "method": "tcp", "open_ports": [445] }
```

### 前端新增

**1. 扫描进度组件** `frontend/src/features/ipam/components/ScanProgress.vue`：
```
- Element Plus Dialog，标题「正在扫描 {子网地址}」
- 顶部：El-Progress 环形进度条，显示百分比
- 中部统计：已扫描 N / 总计 N / 发现在线 N
- 当前正在探测的IP地址（小字，灰色）
- 实时滚动日志：每发现一个在线IP追加一行（绿色✓ + IP + 探测方式）
- 底部：「取消」按钮（关闭WebSocket连接）
- 扫描完成后按钮变为「完成」，点击刷新IP列表和矩阵
```

**2. 在子网详情页添加「立即扫描」按钮**：
```
- 位置：页面右上角操作区
- 点击后打开ScanProgress对话框
- 通过 WebSocket 连接 /api/v1/ipam/ws/scan/{task_id}
- 扫描完成后自动刷新 IpMatrix 颜色状态
```

**3. WebSocket封装** `frontend/src/lib/websocket.ts`（若不存在则新建）：
```typescript
// 封装WebSocket连接，支持：
// - 自动重连（最多3次）
// - 消息回调 onMessage(data)
// - 连接状态管理
// - 主动断开 close()
```

---

## 功能三：VLAN管理

### 功能描述
新增独立的VLAN管理页面，VLAN可与子网关联，设备台账也可引用VLAN，方便查询「某个VLAN下有哪些子网和设备」。

### 后端新增

**数据模型** `backend/src/models/vlan.py`（新建）：
```python
class VlanGroup(Base):
    """VLAN组/域，如「上海办公网」"""
    __tablename__ = "vlan_groups"
    id: int
    name: str           # 组名
    site_id: int        # 关联站点（可为空，表示全局）
    description: str

class Vlan(Base):
    """VLAN记录"""
    __tablename__ = "vlans"
    id: int
    vid: int            # VLAN ID，1-4094
    name: str           # 如「办公网」「管理网」「DMZ」
    group_id: int       # 关联VlanGroup
    status: str         # active / reserved / deprecated
    description: str
    created_at: datetime
    updated_at: datetime

# 修改现有 prefixes 表：
# 新增外键 vlan_id -> vlans.id（可为空）
```

**API接口** 新建 `backend/src/api/vlans.py`：
```
GET    /api/v1/vlans/groups          获取VLAN组列表
POST   /api/v1/vlans/groups          创建VLAN组
PUT    /api/v1/vlans/groups/{id}     编辑VLAN组
DELETE /api/v1/vlans/groups/{id}     删除VLAN组

GET    /api/v1/vlans/                获取VLAN列表，支持按group_id/site_id/status筛选
POST   /api/v1/vlans/                创建VLAN（自动检测同组内VID重复）
PUT    /api/v1/vlans/{id}            编辑VLAN
DELETE /api/v1/vlans/{id}            删除VLAN
GET    /api/v1/vlans/{id}/prefixes   获取该VLAN关联的所有子网
```

### 前端新增

**页面** `frontend/src/features/ipam/VlanList.vue`（新建）：
```
- 路由：/ipam/vlans
- 左侧：VLAN组列表（树形或列表，点击筛选右侧）
- 右侧：VLAN表格
    列：VID / 名称 / 所属组 / 关联站点 / 关联子网数 / 状态 / 操作
    支持搜索（按VID/名称）
    VID范围快速筛选：1-1024 / 1025-2048 / 2049-3072 / 3073-4094
- 新增/编辑VLAN弹窗：
    VID（数字，1-4094，自动校验重复）
    名称 / 所属组 / 状态 / 描述
- 点击VLAN行：右侧展开抽屉，显示该VLAN关联的子网列表
```

**子网表单更新**：
在现有新增/编辑子网弹窗中，增加「关联VLAN」下拉选择框，调用 `GET /api/v1/vlans/` 获取选项。

**IPAM导航更新**：
在IPAM模块左侧导航或顶部Tab中增加「VLAN管理」入口。

---

## 功能四：IP到期自动回收提醒

### 功能描述
部分IP是临时分配的（如给外包、临时设备），需要设置到期时间。到期前系统自动提醒，并支持一键释放回收。

### 后端

现有 `ip_addresses` 表已有 `expire_at` 字段，在此基础上：

**新增定时任务** `backend/src/tasks/ip_expiry.py`：
```python
# 使用APScheduler，每天08:00执行：
async def check_ip_expiry():
    """
    查询所有 expire_at 不为空且状态为 active 的IP：
    - expire_at < 今天：标记状态为 expired，写入操作日志
    - expire_at 在7天内：生成预警记录（写入alerts或直接在查询时计算）
    - expire_at 在30天内：生成轻度预警
    """
```

**新增API**（在现有 `ipam.py` 中追加）：
```
GET /api/v1/ipam/addresses/expiring?days=30
    返回未来N天内到期的IP列表
    返回字段包含：ip地址、设备名、负责人、到期时间、剩余天数

POST /api/v1/ipam/addresses/{id}/release
    一键释放IP：清空设备名/负责人/用途，状态改为available，expire_at置空
    写入操作日志
```

### 前端

**预警中心更新** `frontend/src/features/alerts/`：
在现有预警中心页面新增「IP到期预警」分组，展示：
```
- 表格列：IP地址 / 子网 / 设备名 / 负责人 / 到期时间 / 剩余天数 / 操作
- 剩余天数 ≤7天：红色加粗
- 剩余天数 8-30天：橙色
- 操作列：「续期」（修改expire_at）/ 「立即释放」（调用release接口）
- 「立即释放」需二次确认弹窗
```

**IP分配表单更新**：
在新增/编辑IP弹窗中，增加「到期时间」日期选择器（可选），并在IP列表表格中展示到期时间列（若有）。

**首页仪表盘更新**：
在预警卡片区域增加「IP即将到期」统计，显示7天内到期数量，点击跳转预警中心IP到期分组。

---

## 开发顺序建议

请按以下顺序实现，每步完成后验证再继续：

**Step 1**：后端数据库migration（新增扫描字段 + VLAN表）
**Step 2**：IP扫描后端服务（scanner.py + WebSocket接口）
**Step 3**：VLAN后端CRUD接口
**Step 4**：IP到期定时任务 + release接口
**Step 5**：前端IpMatrix可视化组件
**Step 6**：前端扫描进度组件 + WebSocket接入
**Step 7**：前端VLAN管理页面
**Step 8**：前端IP到期预警 + 表单更新

---

## 注意事项

- 所有新增接口遵循现有格式：`{ code: 0, message: "ok", data: {} }`
- 所有写操作写入 `audit_logs` 表（复用现有日志工具函数）
- ARP探测需要root/NET_RAW权限，若权限不足则静默降级，只用ICMP+TCP探测，不要报错
- scapy不可用时自动跳过ARP，保证程序健壮性
- VLAN VID在同一VLAN组内不允许重复，创建时后端校验并返回明确错误信息
- IP矩阵组件对于大于/20的网段（超过4096个IP），只展示前256个并提示「网段过大，仅展示前256个IP」
- WebSocket断开时前端给出提示，不静默失败
