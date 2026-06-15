# 基石 Cornerstone · AI 智能功能
## Trae 开发提示词

---

## 背景说明

当前项目已有：
- 前端：Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- 后端：FastAPI + SQLAlchemy（异步）+ SQLite/PostgreSQL + JWT认证
- 现有数据：站点、专线、IP地址、网络设备、配置备份、巡检记录
- AI设置模块：已有 AI 配置页面，存储大模型 API Key 和模型选择

本次任务实现三个 AI 能力：
1. **自然语言查询**（P0，优先实现）
2. **配置变更 AI 解读**（P1）
3. **巡检异常 AI 分析**（P2）

AI 接口统一调用系统已配置的大模型（OpenAI / Claude / 通义千问等），从 AI 设置中读取配置，不硬编码任何模型。

---

## 功能一：自然语言查询（P0）

### 效果描述

用户在任意页面按 `Ctrl+K`（或点击顶部搜索框），输入自然语言问题，系统理解意图后查询数据库，直接返回结构化答案。

**示例：**
```
输入：上周哪些设备离线过
输出：列表展示设备名、离线时间、持续时长

输入：北京办公室有几条专线，哪条快到期了
输出：专线列表 + 高亮即将到期的条目

输入：10.1.1.0/24 还有多少 IP 可以用
输出：已用 N / 总 N，剩余 N 个，使用率 XX%

输入：SW-SHA-01 上次备份是什么时候
输出：最近一次备份时间、状态、版本号

输入：哪些设备保修快到期了
输出：设备列表 + 到期时间 + 剩余天数
```

---

### 后端实现

**新建** `backend/src/services/ai_search.py`：

```python
# AI 自然语言查询核心服务

# 系统 Prompt（发给大模型的角色定义）
SYSTEM_PROMPT = """
你是基石（Cornerstone）IT基础设施管理平台的智能助手。
你的任务是理解用户的自然语言问题，将其转换为结构化的查询意图。

可查询的数据类型：
- sites：站点/办公室信息（名称、城市、联系人）
- circuits：专线信息（运营商、带宽、状态、合同到期日）
- devices：网络设备（名称、类型、位置、管理IP、保修日期）
- ip_addresses：IP地址（地址、状态、绑定设备、用途）
- prefixes：IP子网（网段、使用率、站点）
- backups：配置备份记录（设备、时间、状态、是否有变更）
- inspection_results：巡检记录（设备在线状态、离线记录）

你必须返回严格的 JSON 格式，不要返回任何其他内容：
{
    "intent": "query",
    "entities": {
        "type": "数据类型",
        "filters": {
            "字段名": "过滤值"
        },
        "time_range": {
            "field": "时间字段名",
            "start": "ISO时间或相对时间如last_7_days",
            "end": "ISO时间或now"
        },
        "sort": {
            "field": "排序字段",
            "order": "asc或desc"
        },
        "limit": 20
    },
    "answer_format": "list或summary或single",
    "original_question": "用户原始问题"
}
"""

async def parse_user_query(question: str, ai_config: AIConfig) -> QueryIntent:
    """
    调用大模型解析用户问题为结构化查询意图
    使用 ai_config 中配置的模型和 API Key
    超时设置 10 秒，失败时返回错误提示
    """

async def execute_query(intent: QueryIntent, db: AsyncSession) -> QueryResult:
    """
    根据解析出的查询意图执行数据库查询
    返回结构化结果数据
    不同 type 对应不同的查询逻辑：
    - devices：查 devices 表，支持按站点、类型、保修日期过滤
    - circuits：查 circuits 表，支持按状态、到期日过滤
    - ip_addresses：查 ip_addresses + prefixes 表
    - backups：查 backups 表，支持按时间范围过滤
    - inspection_results：查 inspection_device_results 表
    """

async def format_answer(intent: QueryIntent, raw_data: list,
                         question: str, ai_config: AIConfig) -> SearchAnswer:
    """
    将查询结果格式化为自然语言回答
    调用大模型将数据组织成友好的回答文本
    同时返回原始数据供前端渲染结构化展示

    返回格式：
    {
        "answer_text": "北京办公室共有2条专线，其中「北京电信100M」将于30天后到期。",
        "data": [...],          # 原始数据，前端用于渲染卡片/列表
        "data_type": "circuits", # 数据类型，前端据此选择展示组件
        "suggestion": [          # 追问建议
            "查看北京电信专线详情",
            "哪些专线本月到期"
        ]
    }
    """
```

**新增 API 接口** `backend/src/api/ai.py`：

```
POST /api/v1/ai/search
    自然语言查询主接口
    Body: { "question": "上周哪些设备离线过" }
    返回：
    {
        "code": 0,
        "data": {
            "answer_text": "上周共有3台设备发生离线...",
            "data": [...],
            "data_type": "inspection_results",
            "suggestions": ["查看SW-SHA-01详情", "查看本周巡检报告"]
        }
    }
    权限：所有登录用户可访问
    超时：15秒（AI调用较慢）

GET /api/v1/ai/config/status
    检查 AI 是否已配置可用
    返回：{ "configured": true, "model": "gpt-4o", "provider": "openai" }
    未配置时自然语言搜索功能禁用
```

---

### 前端实现

**全局搜索组件** `frontend/src/components/GlobalSearch.vue`：

```
触发方式：
- 键盘快捷键 Ctrl+K（Windows）/ Cmd+K（Mac）
- 点击顶部导航栏的搜索图标

UI 形态：
- 全屏遮罩 + 居中搜索框（参考 Spotlight / Linear 风格）
- 搜索框宽度 600px，圆角，带阴影
- 顶部搜索输入框，placeholder：「搜索设备、IP、专线，或直接提问...」
- 输入框左侧：搜索图标
- 输入框右侧：AI 标识（小星星图标，表示支持自然语言）
- 按 Esc 关闭

搜索行为（两种模式自动切换）：

模式一：普通搜索（输入看起来像精确查询）
- 输入 IP 地址格式（如 10.1.1.100）→ 直接匹配 IP 记录
- 输入设备名关键字 → 匹配设备列表
- 结果实时显示，不需要回车，延迟 300ms 防抖
- 每类结果最多显示 3 条，点击跳转详情页

模式二：AI 自然语言查询（输入超过 8 个字且包含问句特征）
- 识别特征：包含「哪些」「多少」「什么时候」「有没有」「快到期」等词
- 显示「AI 正在理解您的问题...」加载状态（打字机动画）
- 结果区域展示：
    上方：AI 自然语言回答（灰色背景卡片，左侧蓝色竖线）
    下方：结构化数据列表（根据 data_type 渲染对应组件）

结果展示区域（根据 data_type 自动选择）：
- devices    → 设备卡片（名称/类型/位置/状态）
- circuits   → 专线卡片（名称/运营商/到期日）
- ip_addresses → IP卡片（地址/状态/绑定设备）
- backups    → 备份记录行
- inspection_results → 巡检结果行

底部追问建议：
- 最多显示 3 个建议问题（气泡按钮）
- 点击直接填入搜索框并触发查询

历史记录：
- 保存最近 10 条搜索记录到 localStorage
- 搜索框聚焦且为空时显示历史记录
- 历史记录可单条删除
```

**顶部导航栏更新**：
```
在现有顶部导航栏中间位置增加搜索入口：
- 一个假的搜索框（点击触发 GlobalSearch 组件）
- 显示文字：「搜索或提问...」
- 右侧显示「Ctrl+K」快捷键提示
- 宽度 280px，居中
```

**全局快捷键注册** `frontend/src/lib/shortcuts.ts`：
```typescript
// 在 App.vue 中注册全局键盘监听
// Ctrl+K / Cmd+K → 打开 GlobalSearch
// 注意：在 input/textarea 聚焦时不触发
```

---

## 功能二：配置变更 AI 解读（P1）

### 效果描述

每次配置备份检测到变更时，AI 自动解读变更内容，用人话说清楚改了什么、有什么影响。

```
检测到变更：SW-SHA-01（2024-01-15 02:00 自动备份）

AI解读：
本次配置共变更 5 行
• 新增了 2 条 ACL 规则，限制了 192.168.1.0/24 网段的访问
• 修改了 VLAN 10 的描述从「办公网」改为「员工办公网」
• 删除了一条指向 10.2.0.0/16 的静态路由

⚠️ 风险提示：
删除的静态路由可能影响到 10.2.x.x 网段的连通性，
建议确认该路由是否已通过其他方式替代。
```

### 后端实现

**新建** `backend/src/services/ai_backup_analyzer.py`：

```python
BACKUP_ANALYSIS_PROMPT = """
你是一名资深网络工程师，请分析以下网络设备配置变更，用简洁的中文解释：
1. 本次变更了哪些内容（按类型分组：ACL/路由/VLAN/接口/其他）
2. 每项变更的影响是什么
3. 是否存在潜在风险，风险等级（低/中/高）

返回严格的 JSON 格式：
{
    "summary": "一句话总结",
    "changes": [
        {
            "type": "ACL/路由/VLAN/接口/其他",
            "description": "具体变更描述",
            "impact": "影响说明"
        }
    ],
    "risk_level": "low/medium/high",
    "risk_detail": "风险详情，无风险时为空字符串",
    "total_added": 新增行数,
    "total_removed": 删除行数
}
"""

async def analyze_config_change(diff_text: str, device: Device,
                                 ai_config: AIConfig) -> ChangeAnalysis:
    """
    分析配置变更 diff，返回 AI 解读结果
    diff_text：unified diff 格式的变更文本
    超过 3000 行的 diff 截取前 3000 行并注明已截取
    失败时返回 None，不影响备份流程
    """

async def save_change_analysis(backup_id: int, analysis: ChangeAnalysis, db):
    """将分析结果保存到 backup_analyses 表"""
```

**新增数据表** `backup_analyses`：
```python
class BackupAnalysis(Base):
    __tablename__ = "backup_analyses"
    id: int
    backup_id: int          # 关联 backups.id，唯一
    summary: str            # 一句话总结
    changes_json: str       # JSON 数组，变更详情
    risk_level: str         # low / medium / high
    risk_detail: str        # 风险说明
    total_added: int
    total_removed: int
    model_used: str         # 使用的模型名称，记录用
    created_at: datetime
```

**触发时机**：在 `backup_collector.py` 的 `process_backup_change_alert` 函数中，检测到 `has_change=True` 后异步触发 AI 分析，不阻塞备份主流程。

**新增 API**（追加到现有 `backups.py`）：
```
GET /api/v1/backups/{id}/analysis
    获取指定备份的 AI 变更分析结果
    若分析尚未完成返回 { "status": "pending" }
    若 AI 未配置返回 { "status": "unavailable" }
```

### 前端实现

**备份详情页更新**（在现有 Diff 展示页面增加 AI 解读区域）：

```
位置：Diff 对比视图上方

AI 解读卡片：
┌─────────────────────────────────────────┐
│ ✨ AI 变更解读              风险：⚠️ 中  │
├─────────────────────────────────────────┤
│ 本次变更新增了2条ACL规则，删除了1条静态路由 │
│                                          │
│ 变更详情：                               │
│ • [ACL] 新增限制规则，影响192.168.1.0/24  │
│ • [路由] 删除静态路由 10.2.0.0/16         │
│                                          │
│ ⚠️ 风险：删除的静态路由可能影响10.2.x.x   │
│    网段连通性，建议确认是否已替代          │
└─────────────────────────────────────────┘

风险等级颜色：
low    → 绿色
medium → 橙色
high   → 红色，加粗提示

加载状态：显示「AI 正在分析变更内容...」骨架屏
未配置AI：显示「配置 AI 后可自动解读变更内容」+ 跳转 AI 设置链接
```

**备份列表页更新**：
- 有变更的备份行增加风险等级 badge（低/中/高）
- 方便运维人员快速识别高风险变更

---

## 功能三：巡检异常 AI 分析（P2）

### 效果描述

巡检发现设备离线或异常时，AI 结合上下文数据（同站点其他设备状态、专线状态、历史记录）推断可能原因。

```
异常：SW-SHA-01 离线（发现于 14:32）

AI分析：
综合以下信息判断：
• 同站点其他 5 台设备均在线
• 上海电信专线状态正常
• 该设备同机柜的其他设备在线
• 该设备上次离线记录：3个月前，原因：计划维护

推断：设备本身故障可能性较高（约70%）
      不太可能是网络或机房问题

建议排查步骤：
1. 检查设备电源指示灯
2. 尝试 Console 口连接
3. 检查管理口网线连接
```

### 后端实现

**新建** `backend/src/services/ai_inspection_analyzer.py`：

```python
INSPECTION_ANALYSIS_PROMPT = """
你是一名资深网络运维工程师。
设备发生离线异常，请根据提供的上下文信息分析可能原因并给出排查建议。

分析维度：
1. 同站点其他设备是否在线（判断是否机房/电源问题）
2. 关联专线状态（判断是否网络问题）
3. 同机柜其他设备状态（判断是否机柜电源问题）
4. 该设备历史离线记录（判断是否常见问题）

返回 JSON：
{
    "root_cause": "最可能的原因一句话描述",
    "possibilities": [
        { "cause": "设备本身故障", "probability": 70 },
        { "cause": "管理网络中断", "probability": 20 },
        { "cause": "其他", "probability": 10 }
    ],
    "steps": ["排查步骤1", "排查步骤2", "排查步骤3"],
    "urgency": "low/medium/high"
}
"""

async def analyze_device_offline(device_id: int, inspection_result_id: int,
                                  db, ai_config: AIConfig) -> OfflineAnalysis:
    """
    分析设备离线原因
    自动收集上下文：
    - 同站点设备在线状态（本次巡检结果）
    - 关联专线当前状态
    - 同机柜其他设备状态
    - 该设备最近5次历史巡检记录
    """
```

**触发时机**：在巡检告警处理函数 `process_alerts` 中，当 `alert_type=device_offline` 且 AI 已配置时异步触发分析。

**新增 API**（追加到 `inspection.py`）：
```
GET /api/v1/inspection/device-results/{id}/analysis
    获取单台设备异常的 AI 分析结果
```

### 前端实现

**预警中心更新**（设备离线告警详情）：
```
告警详情抽屉中新增「AI 分析」Tab：
- 显示根因推断
- 可能原因概率条形图
- 排查步骤列表（可勾选已完成的步骤）
- 紧急程度标识
```

---

## AI 配置服务

**新建** `backend/src/services/ai_client.py`：

```python
# 统一的 AI 调用客户端
# 从数据库 settings 表读取 AI 配置
# 支持多个提供商，通过 provider 字段区分：

SUPPORTED_PROVIDERS = {
    "openai":    { "base_url": "https://api.openai.com/v1" },
    "anthropic": { "base_url": "https://api.anthropic.com" },
    "qwen":      { "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1" },
    "custom":    { "base_url": None },  # 从配置读取自定义地址
}

async def call_ai(prompt: str, system: str, ai_config: AIConfig,
                  max_tokens: int = 1000, timeout: int = 15) -> str:
    """
    统一 AI 调用入口
    自动适配不同提供商的 API 格式
    超时、重试（最多2次）、错误处理统一在此处理
    返回模型的文本响应
    """

async def get_ai_config(db) -> AIConfig | None:
    """从 settings 表读取 AI 配置，未配置返回 None"""
```

---

## 开发顺序

**Step 1**：`ai_client.py` 统一 AI 调用客户端（支持 OpenAI/Claude/通义千问）

**Step 2**：`ai_search.py` 自然语言查询后端（parse + execute + format 三个函数）

**Step 3**：`POST /api/v1/ai/search` 接口 + `GET /api/v1/ai/config/status` 接口

**Step 4**：前端 `GlobalSearch.vue` 组件（普通搜索 + AI 查询双模式）

**Step 5**：顶部导航栏搜索入口 + `Ctrl+K` 全局快捷键

**Step 6**：`backup_analyses` 表 migration + `ai_backup_analyzer.py`

**Step 7**：备份详情页 AI 解读卡片 + 备份列表风险 badge

**Step 8**：`ai_inspection_analyzer.py` + 预警中心 AI 分析 Tab

---

## 注意事项

- AI 功能全部为**异步非阻塞**，AI 调用失败不影响主流程（备份照常、巡检照常）
- 未配置 AI 时，所有 AI 功能入口显示「配置 AI 后可使用」提示，不报错不隐藏
- 自然语言查询的 `parse_user_query` 失败时（模型返回非 JSON），降级为普通关键字搜索
- AI 调用结果**不缓存**，每次实时调用（查询结果可能随数据变化）
- 备份变更分析结果存库，避免重复调用（同一个 backup_id 只分析一次）
- 所有 AI 调用写入 audit_logs，记录调用时间、使用模型、token消耗（若 API 返回）
- `GlobalSearch` 组件的普通搜索模式不调用 AI，纯本地数据库查询，响应要快（< 500ms）
- 自然语言识别的判断逻辑放在前端（减少无效 AI 调用），确认是自然语言后再请求后端
