# 基石 Cornerstone · 网络拓扑模块
## Trae 开发提示词

---

## 背景说明

当前项目已有完整前后端框架：
- 前端：Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- 后端：FastAPI + SQLAlchemy（异步）+ SQLite/PostgreSQL + JWT认证
- 现有相关数据：站点（sites）、专线（circuits）、设备（devices）、IP地址（ip_addresses）

本次任务分两个阶段实现网络拓扑模块：
- **第一阶段（本次）**：站点间拓扑（利用现有站点+专线数据，快速出效果）
- **第二阶段（本次）**：站点内物理拓扑（新增设备接口和连接关系数据模型）

拓扑渲染库使用 **AntV G6 v5**，请先安装：
```bash
cd frontend && npm install @antv/g6
```

---

## 阶段一：站点间拓扑

### 效果描述
将各办公室站点作为节点，互联网专线/MPLS/SD-WAN等线路作为边，在一张画布上展示公司整体网络连接关系。数据直接复用现有 sites 和 circuits 表，无需新增数据模型。

### 前端

**新建拓扑页面** `frontend/src/features/topology/SiteTopology.vue`：

```
路由：/topology/sites
导航菜单增加「网络拓扑」入口，图标使用 el-icon 的 Share 或 Connection

画布区域：
- 占满剩余页面高度，最小高度 600px
- 背景：深色网格（#1a1a2e 或跟随系统主题）
- 使用 AntV G6 渲染

节点（站点）样式：
- 圆角矩形，宽120px，高60px
- 节点内容：
    上方：站点图标（建筑物图标，SVG）
    中间：站点名称（加粗，白色）
    下方：站点所在城市（小字，灰色）
- 节点颜色按状态：
    正常 → 蓝色边框 #409EFF，深蓝背景
    告警 → 橙色边框 #E6A23C，加橙色光晕
    离线 → 灰色边框 #909399，灰色背景
- 节点右上角小圆点状态指示灯（绿/橙/灰）

边（专线）样式：
- 线条粗细按带宽：
    < 100Mbps  → 细线 1px
    100M~1G    → 中线 2px
    > 1G       → 粗线 4px
- 线条颜色按专线类型：
    互联网专线  → 蓝色 #409EFF
    MPLS       → 绿色 #67C23A
    SD-WAN     → 紫色 #9B59B6
    裸光纤      → 橙色 #E6A23C
- 线条状态：
    正常 → 实线
    故障 → 红色虚线，带流动动画
    停用 → 灰色虚线
- 边中间标签：显示带宽（如「100M」「1G」）

悬停交互：
- 悬停节点：
    高亮该节点所有关联边
    显示 Tooltip：站点名 / 城市 / 联系人 / 专线数量 / 设备数量
- 悬停边：
    显示 Tooltip：专线名称 / 运营商 / 带宽 / 月租费用 / 合同到期日 / 当前状态

点击交互：
- 单击节点：右侧滑出详情面板（不跳转页面）
    展示：站点基本信息 + 该站点所有专线列表 + 设备数量
    底部按钮：「查看站点详情」跳转 /sites/{id}
- 单击边：右侧滑出专线详情面板
    展示：专线完整信息
    底部按钮：「查看专线详情」跳转 /circuits/{id}
- 双击节点：进入站点内部拓扑（阶段二实现，暂时 toast 提示「站点内拓扑即将上线」）

工具栏（画布左上角垂直排列的图标按钮组）：
- 适应画布（居中显示所有节点）
- 放大 / 缩小
- 全屏模式
- 切换布局：
    力导向布局（默认，节点自动分散）
    层次布局（按站点层级排列）
    环形布局
- 导出PNG

图例（画布右下角）：
- 专线类型颜色说明
- 节点状态说明

搜索框（画布右上角）：
- 输入站点名或城市名，匹配节点高亮并居中定位
```

**布局保存**：
```
用户手动拖拽节点后，布局位置保存到 localStorage（key: topology_site_layout）
下次打开自动恢复位置
提供「重置布局」按钮恢复自动布局
```

### 后端

复用现有接口，新增一个聚合接口减少前端请求次数：

```
GET /api/v1/topology/site-graph
返回站点间拓扑所需的全部数据：
{
  "nodes": [
    {
      "id": "site_1",
      "site_id": 1,
      "name": "Demo Site A",
      "city": "上海",
      "status": "normal",       // normal/warning/offline
      "device_count": 5,
      "circuit_count": 2,
      "contact": "张三",
      "phone": "138xxxx"
    }
  ],
  "edges": [
    {
      "id": "circuit_1",
      "circuit_id": 1,
      "source": "site_1",       // source site node id
      "target": "site_2",       // target site node id
      "name": "上海-北京互联网专线",
      "provider": "电信",
      "type": "internet",       // internet/mpls/sdwan/fiber
      "bandwidth": 100,         // Mbps
      "bandwidth_label": "100M",
      "status": "active",       // active/fault/inactive
      "monthly_cost": 5000,
      "contract_end": "2025-12-31",
      "days_to_expire": 180
    }
  ]
}
```

新建 `backend/src/api/topology.py`，在 `main.py` 中注册路由。

---

## 阶段二：站点内物理拓扑

### 新增数据模型

**新建** `backend/src/models/topology.py`：

```python
class DeviceInterface(Base):
    """设备接口"""
    __tablename__ = "device_interfaces"
    id: int
    device_id: int              # 关联设备
    name: str                   # 接口名，如 GigabitEthernet0/0/1
    short_name: str             # 简称，如 Gi0/0/1
    type: str                   # physical / lag / vlan / loopback
    speed: int                  # 接口速率，Mbps
    status: str                 # up / down / disabled
    ip_address_id: int          # 关联IP地址（可为空）
    mac_address: str
    description: str
    created_at: datetime
    updated_at: datetime

class DeviceConnection(Base):
    """设备连接关系（一条记录代表一根线缆两端）"""
    __tablename__ = "device_connections"
    id: int
    # A端
    device_a_id: int            # 设备A
    interface_a_id: int         # 设备A的接口
    # B端
    device_b_id: int            # 设备B
    interface_b_id: int         # 设备B的接口
    # 链路信息
    cable_type: str             # fiber（光纤）/ copper（铜缆）/ dac（DAC线缆）
    link_speed: int             # 链路速率，Mbps（两端协商速率）
    status: str                 # up / down / unknown
    description: str
    created_at: datetime
    updated_at: datetime
```

**Alembic migration**：创建以上两张表，并在现有 `devices` 表确认有 `site_id` 字段。

### 接口管理后端

新建 `backend/src/api/interfaces.py`：
```
GET    /api/v1/devices/{device_id}/interfaces        获取设备接口列表
POST   /api/v1/devices/{device_id}/interfaces        新增接口
PUT    /api/v1/interfaces/{id}                       编辑接口
DELETE /api/v1/interfaces/{id}                       删除接口

GET    /api/v1/connections/                          获取连接列表，支持按site_id筛选
POST   /api/v1/connections/                          新增连接（两端同时录入）
PUT    /api/v1/connections/{id}                      编辑连接
DELETE /api/v1/connections/{id}                      删除连接

GET /api/v1/topology/site/{site_id}/graph
返回站点内拓扑数据：
{
  "site": { "id": 1, "name": "Demo Site A" },
  "nodes": [
    {
      "id": "device_1",
      "device_id": 1,
      "name": "SW-DEMO-CORE-01",
      "type": "switch",          // switch/router/firewall/server/ap
      "model": "Cisco C9300",
      "mgmt_ip": "192.0.2.1",
      "status": "online",
      "location": "A栋机房-机柜01",
      "last_backup_at": "2025-01-15 02:00:00",
      "has_alert": false
    }
  ],
  "edges": [
    {
      "id": "conn_1",
      "connection_id": 1,
      "source": "device_1",
      "target": "device_2",
      "source_interface": "Gi0/0/1",
      "target_interface": "Gi0/0/2",
      "cable_type": "fiber",
      "link_speed": 1000,
      "status": "up"
    }
  ]
}
```

### 站点内拓扑前端

**新建页面** `frontend/src/features/topology/SiteInternalTopology.vue`：

```
路由：/topology/sites/:siteId
从站点间拓扑双击节点进入，面包屑显示：网络拓扑 > Demo Site A

节点（设备）样式：
- 按设备类型使用不同图标（SVG图标）：
    路由器  → 圆形图标
    交换机  → 矩形图标
    防火墙  → 盾牌图标
    服务器  → 服务器图标
    AP      → 无线图标
- 节点下方显示设备名称
- 节点右上角：
    绿点 → 在线（最近备份成功）
    橙点 → 告警
    红点 → 离线或备份失败
    灰点 → 状态未知

边（连接）样式：
- 颜色按线缆类型：
    光纤  → 黄色 #F0C040
    铜缆  → 蓝色 #409EFF
    DAC   → 绿色 #67C23A
- 线条粗细按速率：
    < 1G  → 1px
    1G    → 2px
    10G+  → 4px
- 状态：
    up      → 实线
    down    → 红色虚线
    unknown → 灰色虚线
- 边两端标注接口名（小字）

悬停节点 Tooltip：
    设备名 / 型号 / 管理IP / 机柜位置 / 最后备份时间

悬停边 Tooltip：
    A端接口名 → B端接口名 / 线缆类型 / 链路速率 / 状态

点击节点：
- 右侧滑出设备详情面板
- 展示：设备基本信息 + 接口列表 + 最近备份记录
- 底部按钮：「立即备份」「查看设备详情」

布局：
- 默认层次布局（核心-汇聚-接入从上到下）
- 支持切换力导向布局
- 布局位置保存到 localStorage（key: topology_internal_{siteId}）
```

### 接口录入入口

**设备详情页更新**（在现有 `frontend/src/features/devices/` 下）：
```
在设备详情页或编辑页新增「接口管理」Tab：
- 接口列表表格：接口名 / 简称 / 类型 / 速率 / 状态 / IP地址 / 描述 / 操作
- 新增接口按钮 → 弹窗录入
- 在接口行操作列增加「连接到」按钮 → 弹出选择对话框：
    选择对端设备（下拉，按站点筛选）
    选择对端接口
    选择线缆类型和速率
    保存后自动创建 DeviceConnection 记录
```

---

## 拓扑模块导航结构

```
网络拓扑（侧边栏一级菜单）
├── 站点间拓扑   /topology/sites
├── 站点内拓扑   /topology/sites/:siteId  （从站点间拓扑钻取进入）
└── 连接管理     /topology/connections    （手动管理设备连接关系的表格页）
```

**连接管理页** `frontend/src/features/topology/ConnectionList.vue`：
```
提供表格化的连接关系管理，作为拓扑图录入的替代入口
列：A端设备 / A端接口 / B端设备 / B端接口 / 线缆类型 / 速率 / 状态 / 操作
支持搜索、新增、编辑、删除
```

---

## 开发顺序

请按以下顺序实现，每步完成后验证再继续：

**Step 1**：安装 `@antv/g6`，新建 topology 路由和空页面骨架，验证 G6 画布可正常渲染

**Step 2**：后端 `GET /api/v1/topology/site-graph` 聚合接口，复用 sites + circuits 现有数据

**Step 3**：站点间拓扑页面 `SiteTopology.vue`
- G6 画布渲染节点和边
- 节点/边样式（颜色/粗细/状态）
- 力导向自动布局

**Step 4**：站点间拓扑交互
- 悬停 Tooltip
- 点击节点/边展示右侧详情面板
- 工具栏（缩放/全屏/导出PNG）
- 布局切换（力导向/层次/环形）
- 搜索定位
- 布局位置持久化

**Step 5**：数据库 migration（device_interfaces + device_connections 两张表）

**Step 6**：接口和连接关系后端 CRUD API

**Step 7**：设备详情页新增「接口管理」Tab + 「连接到」功能

**Step 8**：连接管理表格页 `ConnectionList.vue`

**Step 9**：后端 `GET /api/v1/topology/site/{site_id}/graph` 接口

**Step 10**：站点内拓扑页面 `SiteInternalTopology.vue`（样式 + 交互同站点间拓扑逻辑）

---

## 注意事项

- G6 v5 与 v4 API 差异较大，请使用 v5 文档，不要混用 v4 写法
- G6 画布容器需设置明确的宽高，使用 `ResizeObserver` 监听容器尺寸变化自动 `graph.changeSize()`
- 站点间拓扑若某条专线的 `site_id` 为空（未关联站点），该专线不参与拓扑渲染，不报错
- 节点拖拽后坐标保存到 localStorage 时，key 包含 site_id 区分不同站点布局
- 导出 PNG 使用 G6 内置的 `graph.toFullDataURL('image/png')` 方法
- 右侧详情面板使用 Element Plus `el-drawer` 组件，`direction="rtl"`，宽度 400px
- 所有写操作（新增接口、新增连接）写入 audit_logs 表
- 连接关系是双向的，`device_connections` 一条记录代表一根线缆，A/B 端无方向之分，查询时需 `WHERE device_a_id=? OR device_b_id=?`
- 站点内拓扑数据量通常不大（几十台设备），不需要分页，全量返回即可
