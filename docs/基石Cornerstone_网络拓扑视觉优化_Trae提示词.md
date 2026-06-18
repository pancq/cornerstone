# 基石 Cornerstone · 网络拓扑视觉优化
## Trae 开发提示词

---

## 背景说明

当前网络拓扑模块已实现基础功能，本次任务针对以下视觉和交互问题进行优化：
1. 不同设备类型图标颜色相同，区分度低
2. 连线颜色语义混乱（正常链路使用红色）
3. 告警状态只有红点，信息量不足
4. 节点信息密度低，缺少状态摘要
5. 布局算法优化，节点聚拢更合理

请在现有拓扑代码基础上修改，不重写整体架构。

---

## 改动一：设备图标颜色区分

### 问题
所有设备图标均使用相同蓝色（#409EFF），交换机、路由器、防火墙无法快速区分。

### 修改方案

在现有图标配置中，按设备类型赋予独立颜色：

```javascript
// 设备类型颜色映射表
// 文件位置：前端拓扑相关配置文件或常量文件

export const DEVICE_TYPE_CONFIG = {
  // 核心网络设备
  router:          { color: '#E6A23C', label: '路由器',    bgOpacity: 0.15 },
  'core-switch':   { color: '#409EFF', label: '核心交换机', bgOpacity: 0.15 },
  'access-switch': { color: '#79BBFF', label: '接入交换机', bgOpacity: 0.15 },
  firewall:        { color: '#F56C6C', label: '防火墙',    bgOpacity: 0.15 },
  'load-balancer': { color: '#9B59B6', label: '负载均衡',  bgOpacity: 0.15 },
  ap:              { color: '#67C23A', label: '无线AP',    bgOpacity: 0.15 },
  ac:              { color: '#4CAF50', label: '无线控制器', bgOpacity: 0.15 },

  // 服务器与终端
  server:          { color: '#36CFC9', label: '服务器',    bgOpacity: 0.15 },
  pc:              { color: '#8899AA', label: 'PC',        bgOpacity: 0.15 },
  printer:         { color: '#909399', label: '打印机',    bgOpacity: 0.12 },
  nas:             { color: '#2D5BE3', label: 'NAS/存储',  bgOpacity: 0.15 },

  // 安全设备
  'ids-ips':       { color: '#E85F5C', label: 'IDS/IPS',  bgOpacity: 0.15 },
  vpn:             { color: '#7B61FF', label: 'VPN网关',   bgOpacity: 0.15 },
  waf:             { color: '#FF7A45', label: 'WAF',       bgOpacity: 0.15 },

  // 逻辑节点
  internet:        { color: '#40A9FF', label: '互联网',    bgOpacity: 0.10 },
  isp:             { color: '#606266', label: '运营商',    bgOpacity: 0.10 },
  datacenter:      { color: '#1F4E79', label: '数据中心',  bgOpacity: 0.20 },
  site:            { color: '#1D9E75', label: '站点',      bgOpacity: 0.15 },

  // 默认（未知）
  unknown:         { color: '#909399', label: '未知设备',  bgOpacity: 0.10 },
}
```

### G6 节点样式更新

在现有 G6 自定义节点的 `draw` 或 `setState` 方法中，根据 `cfg.deviceType` 读取颜色配置：

```javascript
// 节点背景色 = 设备颜色 + 低透明度
// 节点边框色 = 设备颜色
// 图标填充色 = 设备颜色

const config = DEVICE_TYPE_CONFIG[cfg.deviceType] || DEVICE_TYPE_CONFIG.unknown
const deviceColor = config.color

// 卡片背景
group.addShape('rect', {
  attrs: {
    fill: deviceColor,
    fillOpacity: config.bgOpacity,
    stroke: deviceColor,
    strokeOpacity: 0.6,
    radius: 8,
    // ... 其他属性
  }
})

// 图标颜色也使用 deviceColor
```

---

## 改动二：连线颜色语义修正

### 问题
正常链路使用红色虚线，和「故障/告警」的语义冲突。

### 修改方案

```javascript
// 链路状态颜色映射
export const LINK_STATUS_CONFIG = {
  up: {
    color: '#5B8DB8',        // 灰蓝色，正常链路
    lineWidth: 2,
    lineDash: null,          // 实线
    label: '正常',
  },
  down: {
    color: '#F56C6C',        // 红色，故障链路
    lineWidth: 2,
    lineDash: [6, 3],        // 虚线
    label: '故障',
  },
  unknown: {
    color: '#606266',        // 深灰色，状态未知
    lineWidth: 1.5,
    lineDash: [4, 4],        // 短虚线
    label: '未知',
  },
  degraded: {
    color: '#E6A23C',        // 橙色，链路降级（有丢包但未完全断）
    lineWidth: 2,
    lineDash: [8, 3],        // 长虚线
    label: '降级',
  },
}

// 链路粗细按带宽
function getLinkWidth(bandwidthMbps) {
  if (!bandwidthMbps) return 1.5
  if (bandwidthMbps >= 10000) return 5   // 10G+
  if (bandwidthMbps >= 1000)  return 3   // 1G
  if (bandwidthMbps >= 100)   return 2   // 100M
  return 1.5                             // < 100M
}
```

在现有 G6 边配置中应用以上样式，将硬编码的颜色替换为动态读取。

---

## 改动三：告警状态点优化

### 问题
右上角红点位置偏移、信息量不足。

### 修改方案

**位置调整**：状态点改为节点右上角内嵌，不超出节点边界。

```javascript
// 在 G6 节点 draw 方法中，状态点绘制位置：
// 节点右上角，距右边 8px，距上边 8px，半径 5px

group.addShape('circle', {
  name: 'status-dot',
  attrs: {
    x: cfg.width - 8,    // 右侧内嵌
    y: 8,                // 顶部内嵌
    r: 5,
    fill: statusColor,
    stroke: '#1a2035',   // 深色描边，和背景分离
    strokeWidth: 1.5,
  }
})
```

**状态颜色**：
```javascript
const STATUS_DOT_COLOR = {
  online:  '#67C23A',   // 绿色：在线正常
  offline: '#F56C6C',   // 红色：离线
  warning: '#E6A23C',   // 橙色：有告警但在线
  unknown: '#909399',   // 灰色：状态未知
}
```

**Tooltip 内容**（鼠标悬停节点时显示）：

使用 G6 的 tooltip 插件或自定义 DOM tooltip，显示以下内容：

```
┌─────────────────────────────┐
│ SW-DEMO-CORE-01             │
│ ─────────────────────────── │
│ 类型：核心交换机             │
│ IP：192.0.2.65              │
│ 状态：🔴 离线               │
│ 告警：设备无响应 · 2小时前   │
│ 最后备份：昨天 02:00         │
│ 位置：上海总部-A栋-机柜01    │
│ ─────────────────────────── │
│ 点击查看详情 →               │
└─────────────────────────────┘
```

实现要求：
- 使用自定义 HTML DOM tooltip（不用 G6 内置，样式更可控）
- 跟随鼠标位置显示，距光标 12px 偏移
- 延迟 200ms 显示（防止快速移过节点时闪烁）
- 移出节点后 100ms 消失

---

## 改动四：节点卡片增加状态摘要行

### 问题
节点只显示设备名 + IP，缺少关键状态信息。

### 修改方案

节点卡片从两行扩展为三行：

```
┌──────────────────────────┐
│  [图标]              ●   │  ← 图标 + 状态点
│  SW-DEMO-CORE-01         │  ← 设备名（白色，加粗）
│  192.0.2.65              │  ← IP地址（灰色，小字）
│  在线 · 备份2h前          │  ← 状态摘要（更小字，颜色按状态）
└──────────────────────────┘
```

**状态摘要文字规则**：
```javascript
function getStatusSummary(device) {
  if (device.status === 'offline') {
    return `离线 · ${timeAgo(device.lastSeenAt)}`
    // 示例：「离线 · 2小时前」
  }
  if (device.hasAlert) {
    return `告警 · ${device.alertCount}条未处理`
    // 示例：「告警 · 3条未处理」
  }
  if (device.lastBackupAt) {
    return `在线 · 备份${timeAgo(device.lastBackupAt)}`
    // 示例：「在线 · 备份2h前」
  }
  return '在线'
}
```

**节点尺寸调整**：
```javascript
// 增加第三行后，节点高度从当前值增加 16px
// 宽度保持不变，确保三行文字不溢出
const NODE_WIDTH = 180
const NODE_HEIGHT = 90   // 原来约 74px，增加 16px
```

---

## 改动五：布局算法优化

### 问题
节点过于分散，中间大片空白，网络层级关系不直观。

### 修改方案

**默认布局改为层次布局（dagre）**，核心设备在上，接入设备在下：

```javascript
// 安装依赖（若未安装）：npm install @antv/layout

import { DagreLayout } from '@antv/layout'

const dagreLayout = new DagreLayout({
  type: 'dagre',
  rankdir: 'TB',        // 从上到下（Top to Bottom）
  align: 'UL',
  nodesep: 40,          // 同层节点间距
  ranksep: 80,          // 层间距
  controlPoints: true,
})
```

**布局优先级规则**（节点 rank 分配）：
```javascript
// 根据设备类型自动分配层级
const DEVICE_RANK = {
  internet:        0,   // 第0层：互联网/云
  isp:             0,
  router:          1,   // 第1层：路由器/出口设备
  firewall:        1,
  'load-balancer': 1,
  'core-switch':   2,   // 第2层：核心交换机
  'access-switch': 3,   // 第3层：接入交换机
  ap:              3,
  server:          4,   // 第4层：终端设备
  pc:              4,
  unknown:         3,
}

// 在图数据初始化时，为每个节点设置 rank：
nodes.forEach(node => {
  node.rank = DEVICE_RANK[node.deviceType] ?? 3
})
```

**布局切换**：工具栏保留布局切换按钮，支持：
- 层次布局（Dagre，新默认）
- 力导向布局（Force，原默认）
- 环形布局（Circular）

**布局记忆**：用户手动拖拽节点后，记录每个节点的自定义坐标到 localStorage：
```javascript
// key: topology_layout_{graphId}
// value: { nodeId: { x, y }, ... }
// 下次打开时恢复自定义布局
// 工具栏「重置布局」按钮清除 localStorage 并重新自动布局
```

---

## 改动六：图例更新

在画布右下角图例区域更新：

```
节点状态：
● 在线    ● 告警    ● 离线    ● 未知

链路状态：
─── 正常    - - 故障    ··· 未知    ─·─ 降级

设备类型：
🔶 路由器  🔵 核心交换  🔷 接入交换  🔴 防火墙
🟢 无线AP  🔵 服务器   ···
```

图例支持点击过滤（点击某个设备类型，隐藏/显示该类型的所有节点）。

---

## 开发顺序

**Step 1**：新增 `DEVICE_TYPE_CONFIG` 和 `LINK_STATUS_CONFIG` 常量文件

**Step 2**：G6 节点颜色按设备类型动态渲染（改动一）

**Step 3**：连线颜色语义修正，正常链路改为灰蓝色实线（改动二）

**Step 4**：状态点位置内嵌 + 颜色更新（改动三前半部分）

**Step 5**：自定义 HTML Tooltip 实现（改动三后半部分）

**Step 6**：节点卡片增加第三行状态摘要（改动四）

**Step 7**：Dagre 层次布局替换默认布局 + 布局记忆（改动五）

**Step 8**：图例区域更新 + 点击过滤功能（改动六）

---

## 注意事项

- 所有改动在现有 G6 画布代码基础上修改，不重写拓扑组件
- `DEVICE_TYPE_CONFIG` 和图标库提示词中的颜色体系保持一致，统一从同一个常量文件引用
- 节点高度增加后，检查连线起止点坐标是否需要同步调整
- Tooltip 使用 Vue 的 `teleport` 挂载到 `body`，避免被画布容器裁切
- 层次布局中，若设备类型为 `unknown`，rank 默认为 3（接入层），不报错
- 布局记忆的 localStorage key 包含站点 ID，不同站点的拓扑布局独立保存
- 图例点击过滤只影响画布显示，不修改数据，刷新后恢复全部显示
