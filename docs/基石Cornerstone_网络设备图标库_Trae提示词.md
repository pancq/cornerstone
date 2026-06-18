# 基石 Cornerstone · 网络设备图标库
## Trae 开发提示词

---

## 背景说明

当前网络拓扑模块使用基础色块或简单图标区分设备类型，视觉效果不专业。
本次任务：创建一套完整的网络设备 SVG 图标库，集成到网络拓扑、设备台账、智能巡检等模块中。

图标风格：扁平彩色风格，适配深色主题，每种设备有独立颜色，三种状态（正常/离线/告警）。

---

## 一、图标设计规范

### 基础规范
```
画布尺寸：48×48px（viewBox="0 0 48 48"）
图标主体：居中，占画布 70%（约 34×34px 范围内）
圆角：统一使用 rx="4" 或 rx="6"
线条粗细：stroke-width="2"
风格：扁平，无渐变，无阴影，纯色填充
```

### 三种状态的视觉规则
```
正常状态：标准颜色填充，实线边框
离线状态：填充色改为 #606266，边框改为 #909399 虚线（stroke-dasharray="4 2"）
告警状态：填充色改为 #E6A23C，边框改为 #E6A23C，外层加橙色光晕圆圈
```

### 颜色体系
```css
/* 核心网络设备 */
--color-router:          #E6A23C;  /* 路由器：橙色 */
--color-core-switch:     #409EFF;  /* 核心交换机：蓝色 */
--color-access-switch:   #79BBFF;  /* 接入交换机：浅蓝 */
--color-firewall:        #F56C6C;  /* 防火墙：红色 */
--color-load-balancer:   #9B59B6;  /* 负载均衡：紫色 */
--color-ap:              #67C23A;  /* 无线AP：绿色 */
--color-ac:              #4CAF50;  /* 无线控制器：深绿 */

/* 服务器与终端 */
--color-server:          #36CFC9;  /* 服务器：青色 */
--color-pc:              #8899AA;  /* PC/工作站：灰蓝 */
--color-printer:         #909399;  /* 打印机：灰色 */
--color-nas:             #2D5BE3;  /* NAS/存储：深蓝 */
--color-camera:          #7B61FF;  /* 摄像头：紫蓝 */

/* 安全设备 */
--color-ids-ips:         #E85F5C;  /* IDS/IPS：红橙 */
--color-vpn:             #7B61FF;  /* VPN网关：紫蓝 */
--color-waf:             #FF7A45;  /* WAF：橙红 */
--color-sandbox:         #C41D7F;  /* 沙箱：玫红 */

/* 逻辑节点 */
--color-internet:        #40A9FF;  /* 互联网/云：天蓝 */
--color-isp:             #606266;  /* 运营商：深灰 */
--color-datacenter:      #1F4E79;  /* 数据中心：深蓝 */
--color-site:            #1D9E75;  /* 站点/机房：青绿 */
```

---

## 二、图标清单（共26个）

新建目录 `frontend/src/assets/icons/network/`，每个图标一个 SVG 文件：

### 核心网络设备（7个）

**router.svg** — 路由器
```svg
<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <!-- 主体：圆角矩形设备 -->
  <rect x="6" y="16" width="36" height="16" rx="4"
        fill="#E6A23C" fill-opacity="0.15" stroke="#E6A23C" stroke-width="2"/>
  <!-- 左侧接口指示灯 3个 -->
  <circle cx="13" cy="24" r="2" fill="#E6A23C"/>
  <circle cx="20" cy="24" r="2" fill="#E6A23C" fill-opacity="0.6"/>
  <circle cx="27" cy="24" r="2" fill="#E6A23C" fill-opacity="0.3"/>
  <!-- 右侧天线 -->
  <line x1="38" y1="16" x2="38" y2="8" stroke="#E6A23C" stroke-width="2" stroke-linecap="round"/>
  <line x1="42" y1="16" x2="44" y2="9" stroke="#E6A23C" stroke-width="2" stroke-linecap="round"/>
  <!-- 底部接口 -->
  <line x1="14" y1="32" x2="14" y2="38" stroke="#E6A23C" stroke-width="2" stroke-linecap="round"/>
  <line x1="20" y1="32" x2="20" y2="38" stroke="#E6A23C" stroke-width="2" stroke-linecap="round"/>
  <line x1="26" y1="32" x2="26" y2="38" stroke="#E6A23C" stroke-width="2" stroke-linecap="round"/>
  <line x1="32" y1="32" x2="32" y2="38" stroke="#E6A23C" stroke-width="2" stroke-linecap="round"/>
</svg>
```

**core-switch.svg** — 核心交换机
```
主体：扁平矩形，高度较矮（设备形态）
特征：顶部一排密集的接口点（8-12个小方块），左侧有SFP槽位标识
颜色：#409EFF
```

**access-switch.svg** — 接入交换机
```
主体：比核心交换机略小的矩形
特征：底部一排接口（24口密集排列简化为线条），顶部有上行链路标识
颜色：#79BBFF
```

**firewall.svg** — 防火墙
```
主体：盾牌形状（上方圆弧+下方尖角）
特征：盾牌中间有锁形或火焰形标识
颜色：#F56C6C
```

**load-balancer.svg** — 负载均衡
```
主体：圆角矩形
特征：中间有分叉箭头（1进3出的分流示意）
颜色：#9B59B6
```

**ap.svg** — 无线AP
```
主体：半圆形（天线信号波形）
特征：底部小矩形底座，上方3条弧线表示WiFi信号
颜色：#67C23A
```

**ac.svg** — 无线控制器（AC）
```
主体：圆角矩形
特征：内部有WiFi图标+控制线条
颜色：#4CAF50
```

---

### 服务器与终端（6个）

**server.svg** — 服务器
```
主体：竖向或横向机架形态矩形
特征：正面有光驱槽、指示灯、电源按钮细节
颜色：#36CFC9
```

**pc.svg** — PC/工作站
```
主体：显示器+主机组合
特征：显示器梯形底座，主机矩形放旁边
颜色：#8899AA
```

**laptop.svg** — 笔记本电脑
```
主体：开盖笔记本形态（屏幕+键盘两部分）
颜色：#8899AA
```

**printer.svg** — 打印机
```
主体：打印机侧视图
特征：纸张从顶部出纸口出来
颜色：#909399
```

**nas.svg** — NAS/存储
```
主体：竖向矩形，多层磁盘叠加
特征：正面有多个磁盘槽位
颜色：#2D5BE3
```

**camera.svg** — 网络摄像头
```
主体：摄像头镜头+支架
特征：圆形镜头+矩形机身
颜色：#7B61FF
```

---

### 安全设备（4个）

**ids-ips.svg** — IDS/IPS
```
主体：盾牌形（和防火墙区分：内部是眼睛图标，表示检测）
颜色：#E85F5C
```

**vpn.svg** — VPN网关
```
主体：圆角矩形
特征：中间有隧道/锁链图标
颜色：#7B61FF
```

**waf.svg** — WAF
```
主体：盾牌形（内部有W字母或Web图标）
颜色：#FF7A45
```

**sandbox.svg** — 沙箱
```
主体：正方形容器
特征：内部有隔离框图案
颜色：#C41D7F
```

---

### 逻辑节点（5个）

**internet.svg** — 互联网/云
```
主体：云朵形状（3个圆弧组合）
特征：标准云图标
颜色：#40A9FF
```

**isp.svg** — 运营商
```
主体：信号塔形状（三角形底座+塔身+顶部信号弧线）
颜色：#606266
```

**datacenter.svg** — 数据中心
```
主体：建筑轮廓（矩形+顶部天线）
特征：正面有服务器排列示意
颜色：#1F4E79
```

**site.svg** — 站点/办公室
```
主体：房屋形状（五边形，三角屋顶+矩形主体）
特征：正面有门和窗户
颜色：#1D9E75
```

**unknown.svg** — 未知设备
```
主体：圆角矩形
特征：中间有问号
颜色：#909399
```

---

### 线路类型图标（4个，用于拓扑图边的图例）

**cable-fiber.svg** — 光纤（黄色线条+光波纹）
**cable-copper.svg** — 铜缆（蓝色线条+电流波形）
**cable-dac.svg** — DAC线缆（绿色线条）
**cable-wireless.svg** — 无线（弧线+点）

---

## 三、Vue 图标组件

新建 `frontend/src/components/icons/NetworkIcon.vue`：

```vue
<template>
  <div class="network-icon" :class="[`device-${type}`, `status-${status}`, sizeClass]">
    <!-- 告警状态光晕 -->
    <div v-if="status === 'warning'" class="icon-glow"></div>

    <!-- SVG图标（动态加载） -->
    <component :is="iconComponent" class="icon-svg"/>

    <!-- 设备名称标签（可选显示） -->
    <span v-if="showLabel" class="icon-label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
// Props:
// type: 设备类型，如 'router' | 'firewall' | 'server' 等
// status: 'online' | 'offline' | 'warning' | 'unknown'
// size: 'sm'(24px) | 'md'(48px，默认) | 'lg'(64px)
// showLabel: 是否显示名称标签
// label: 标签文字

// 图标映射表：type → SVG组件
// 状态通过 CSS class 控制颜色变化
</script>

<style scoped>
/* 正常状态：标准颜色 */
.status-online .icon-svg { opacity: 1; }

/* 离线状态：灰色 + 虚线效果 */
.status-offline .icon-svg {
  filter: grayscale(100%);
  opacity: 0.5;
}

/* 告警状态：橙色光晕 */
.status-warning .icon-glow {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  box-shadow: 0 0 12px 4px rgba(230, 162, 60, 0.6);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 未知状态：低透明度 */
.status-unknown .icon-svg { opacity: 0.4; }

/* 尺寸变体 */
.size-sm { width: 24px; height: 24px; }
.size-md { width: 48px; height: 48px; }
.size-lg { width: 64px; height: 64px; }

/* 标签样式 */
.icon-label {
  display: block;
  text-align: center;
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
}
</style>
```

---

## 四、图标选择器组件

新建 `frontend/src/components/icons/IconPicker.vue`：

```
用途：设备台账新增/编辑时，让用户选择设备图标

UI：
- 触发：点击当前图标区域弹出选择器
- 弹出层：El-Popover，显示所有图标分组
- 分组：核心网络设备 / 服务器与终端 / 安全设备 / 逻辑节点
- 每组图标以网格形式排列（每行6个）
- 鼠标悬停显示设备类型名称
- 点击选中，高亮选中状态
- 支持搜索（输入「路由」「防火墙」等关键字过滤）
```

---

## 五、集成到现有模块

### 1. 网络设备列表页

在现有 `frontend/src/features/devices/` 中：
- 设备列表表格第一列增加图标列，根据设备类型（type字段）显示对应图标
- 图标尺寸：`size="sm"`（24px）
- 状态根据设备在线状态映射：在线→online，离线→offline

新增/编辑设备弹窗：
- 「设备类型」字段改为图标选择器（IconPicker），选择图标同时自动填入类型名称
- 保存时存储 `icon_type` 字段到数据库

### 2. 网络拓扑（G6画布）

在现有拓扑模块中替换节点图标：

```javascript
// G6 自定义节点注册
G6.registerNode('network-device', {
  draw(cfg, group) {
    // 根据 cfg.deviceType 选择对应SVG图标
    // 根据 cfg.status 应用对应样式
    // 节点大小：48×48，下方显示设备名称
  }
})

// 节点数据格式：
{
  id: 'device_1',
  deviceType: 'firewall',    // 对应图标类型
  status: 'online',          // online/offline/warning/unknown
  label: 'FW-SHA-01',
  // ...其他数据
}
```

### 3. 智能巡检结果页

巡检结果列表中，IP地址列前增加图标列：
- 已识别厂商的设备：显示对应设备类型图标
- 未识别/新发现设备：显示 unknown.svg 图标（问号）
- 离线设备：图标显示 status="offline"（灰色）

### 4. 预警中心

设备离线/告警预警列表中，设备名称前显示图标，status="warning"（橙色光晕）。

---

## 六、后端数据模型更新

在现有 `devices` 表新增字段：

```python
# Alembic migration
icon_type: str = Column(String(50), default="unknown")
# 存储图标类型字符串，如 "router" / "firewall" / "server"
# 前端根据此字段选择显示哪个SVG
```

新增API（追加到 `backend/src/api/devices.py`）：
```
GET /api/v1/devices/icon-types
    返回所有可用图标类型列表，供前端 IconPicker 使用
    返回：[
        { "type": "router", "label": "路由器", "color": "#E6A23C", "group": "核心网络设备" },
        { "type": "firewall", "label": "防火墙", "color": "#F56C6C", "group": "核心网络设备" },
        ...
    ]
```

---

## 七、图标与设备类型自动映射

SNMP 巡检识别厂商后，自动推断图标类型：

```python
# backend/src/services/inspector.py 中新增映射逻辑

SNMP_TO_ICON_MAP = {
    # 根据 sysDescr 关键字推断图标类型
    "keywords": {
        "router":       ["router", "路由", "ISR", "ASR", "AR", "NE"],
        "firewall":     ["firewall", "防火墙", "ASA", "FortiGate", "USG", "Hillstone"],
        "core-switch":  ["core", "核心", "Catalyst 9", "S12", "S57", "S67"],
        "access-switch":["switch", "交换机", "Catalyst 2", "S23", "S53"],
        "ap":           ["AP", "access point", "无线"],
        "server":       ["server", "服务器", "ProLiant", "PowerEdge"],
        "load-balancer":["F5", "BIG-IP", "负载"],
        "vpn":          ["VPN", "SSL"],
        "waf":          ["WAF", "web application"],
    }
}

def infer_icon_type(sys_descr: str, sys_object_id: str) -> str:
    """
    根据 SNMP 采集到的设备描述推断图标类型
    匹配不到时返回 "unknown"
    """
```

---

## 开发顺序

**Step 1**：创建所有26个 SVG 图标文件到 `frontend/src/assets/icons/network/`

**Step 2**：`NetworkIcon.vue` 组件（动态加载SVG + 三种状态样式）

**Step 3**：`IconPicker.vue` 组件（分组网格 + 搜索过滤）

**Step 4**：后端 `icon_type` 字段 migration + `/devices/icon-types` 接口

**Step 5**：设备列表页集成图标（表格 + 新增编辑弹窗改为 IconPicker）

**Step 6**：网络拓扑 G6 自定义节点替换为 SVG 图标

**Step 7**：智能巡检结果页图标集成

**Step 8**：预警中心图标集成

**Step 9**：SNMP 巡检自动推断图标类型（`infer_icon_type` 函数）

---

## 注意事项

- SVG 文件使用内联方式引入（`import RouterIcon from '@/assets/icons/network/router.svg?component'`），不用 img 标签，方便 CSS 控制颜色
- Vite 配置需安装 `vite-plugin-svgr` 以支持 SVG 作为 Vue 组件导入
- 所有图标必须在深色背景（#1a2035）和浅色背景（#ffffff）下都清晰可见
- 图标颜色使用 fill 属性而非 stroke 为主，确保小尺寸（24px）下清晰
- G6 中使用 SVG 图标时，通过 `image` 类型节点加载 SVG URL，或使用 G6 自定义节点绘制
- `icon_type` 字段默认值为 `unknown`，已有设备不需要强制修改，界面显示问号图标
- 图标选择器中的搜索支持中英文，「router」和「路由器」都能找到路由器图标
