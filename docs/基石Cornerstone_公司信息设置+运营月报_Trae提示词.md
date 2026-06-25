# 基石 Cornerstone · 公司信息设置 + 运营月报PDF生成
## Trae 开发提示词

---

## 背景说明

当前系统缺少两个功能：
1. 公司信息统一配置（公司名称、部门、联系人等，供全系统复用）
2. IT运营月报自动生成（PDF格式，供IT负责人每月下载汇报）

两个功能合并实现，公司信息配置完成后直接用于月报生成。

---

## 一、系统设置新增「公司信息」

### 后端

在现有 `settings` 表中新增以下配置项（复用已有 key-value 存储结构）：

```python
# 新增配置项及默认值
COMPANY_SETTINGS = {
    "company_name":       "",   # 公司全称，如「简一致远科技有限公司」
    "company_short_name": "",   # 公司简称，如「简一致远」
    "it_department_name": "信息技术部",  # IT部门名称
    "it_contact_name":    "",   # IT负责人姓名
    "it_contact_email":   "",   # IT负责人邮箱
}
```

追加到 `backend/src/api/settings.py`：

```
GET  /api/v1/settings/company      获取公司信息配置
PUT  /api/v1/settings/company      保存公司信息配置
     权限：仅 super_admin
     Body: { company_name, company_short_name, it_department_name,
             it_contact_name, it_contact_email }
```

### 前端

在「系统设置」页面新增「公司信息」卡片（放在现有设置卡片之前，第一个显示）：

```
卡片标题：公司信息

字段：
- 公司全称（必填，文本输入框，placeholder：如「简一致远科技有限公司」）
- 公司简称（必填，文本输入框，placeholder：如「简一致远」）
- IT部门名称（选填，默认「信息技术部」）
- IT负责人姓名（选填）
- IT负责人邮箱（选填，邮箱格式校验）

底部：「保存」按钮，保存成功提示「公司信息已更新」

提示文字（卡片顶部灰色小字）：
「公司信息将用于运营月报封面、邮件通知落款等场景，请确保信息准确」
```

---

## 二、运营月报PDF生成

### 依赖安装

```bash
pip install reportlab==4.0.9 pillow==10.0.0
```

### 月报数据结构

新建 `backend/src/services/report_generator.py`，实现月报数据收集和PDF生成：

```python
# 月报数据结构（从各模块接口聚合）
@dataclass
class MonthlyReportData:
    # 基本信息
    year: int
    month: int
    company_name: str
    company_short_name: str
    it_department: str
    it_contact: str
    generated_at: datetime

    # 第一页：本月概况
    availability_pct: float         # 网络可用性百分比
    availability_status: str        # good/warning/bad
    availability_trend: str         # up/down/same
    circuit_cost_total: int         # 专线月租总费用（元）
    circuit_cost_trend_pct: float   # 费用环比变化百分比
    incident_count: int             # 故障次数
    incident_trend: int             # 较上月增减（正数增加，负数减少）
    config_change_count: int        # 配置变更次数
    unresolved_alerts: int          # 未处理告警数

    # 第二页：下月行动项
    urgent_items: list              # 必须处理（30天内到期）
    attention_items: list           # 建议关注（31-60天内）

    # 第三页：费用分析
    cost_by_type: dict              # 按专线类型分组费用
    cost_history: list              # 近6个月费用历史

    # 第四页：故障详情
    incidents: list                 # 本月故障列表
    avg_recovery_hours: float       # 平均恢复时长

async def collect_report_data(year: int, month: int, db) -> MonthlyReportData:
    """
    从数据库各表收集月报所需数据：
    - availability：从 inspection_device_results 计算本月在线率
      若无巡检数据则标记为 None（报告中显示「暂无数据」）
    - circuit_cost：从 circuits 表 monthly_cost 字段求和
      若所有专线均未填费用则显示「¥0（未录入费用信息）」
    - incidents：从 circuit_incidents 表查本月记录
    - config_changes：从 backups 表查 has_change=True 的本月记录
    - expiring_items：查 circuits.contract_end 和 devices.warranty_end
      30天内：urgent_items，31-60天：attention_items
    - cost_history：近6个月每月费用（当前专线费用静态计算）
    """
```

### PDF生成

```python
def generate_pdf(data: MonthlyReportData, output_path: str):
    """
    使用 reportlab 生成PDF，共6页：
    封面 + 执行摘要 + 本月概况 + 下月行动项 + 费用分析 + 故障记录
    """
```

**页面设计规范**：

```
页面尺寸：A4（210×297mm）
页边距：上25mm 下20mm 左25mm 右20mm
主色调：#1F4E79（深蓝，标题和重点）
辅色：#2E75B6（蓝色，图表和分隔线）
正文字体：使用系统内置中文字体（reportlab 注册 SimSun 或 STSong）
数字字体：加粗，比正文大2pt

页眉（除封面外每页）：
  左：基石 · IT基础设施运营月报
  右：XXXX年X月
  下方细线分隔

页脚（除封面外每页）：
  左：{company_short_name} {it_department}
  右：第X页 / 共X页
  上方细线分隔
```

---

**第一页：封面**

```
布局（从上到下）：

顶部1/3：深蓝色背景块（#1F4E79）
  - 若有公司Logo：左上角显示Logo（高度40px）
  - 无Logo：显示公司简称文字

中部：
  大标题：IT基础设施运营月报（白色，28pt，加粗）
  副标题：XXXX年X月（白色，16pt）

中下部：白色背景
  公司全称：{company_name}（14pt，深灰）
  报告周期：{year}年{month}月1日 至 {year}年{month}月{last_day}日
  生成时间：{generated_at}
  生成系统：基石 Cornerstone · IT基础设施资源管理平台
```

---

**第二页：执行摘要**

```
标题：执行摘要

用3-5句话概括本月重点（根据数据动态生成文字）：

模板逻辑：
- 可用性 >= 99%：「本月网络整体运行稳定，可用性达{X}%。」
- 可用性 < 99%：「本月网络可用性为{X}%，低于目标值99%，需关注。」
- 故障次数 = 0：「本月未发生专线故障。」
- 故障次数 > 0：「发生故障{N}次，平均恢复时长{X}小时。」
- 费用环比上涨 > 5%：「专线费用较上月增加{X}%，建议关注费用趋势。」
- 有紧急到期事项：「下月有{N}项合同/保修即将到期，请尽快处理。」

下方关键指标速览表（2×3网格）：
┌──────────────┬──────────────┬──────────────┐
│ 网络可用性    │ 专线费用      │ 故障次数      │
│ 99.2% 🟢    │ ¥42,800      │ 3次 🟡        │
├──────────────┼──────────────┼──────────────┤
│ 配置变更      │ 未处理告警    │ 即将到期      │
│ 8次 🟢       │ 0条 🟢       │ 3项 🟡        │
└──────────────┴──────────────┴──────────────┘

状态图标规则：
🟢 绿色：正常/达标
🟡 橙色：需关注
🔴 红色：异常/超标
```

---

**第三页：本月概况（详细指标）**

```
标题：本月运营概况

分为两栏：

左栏：网络可用性
  大数字：99.2%（绿色，24pt）
  说明：较上月 +0.3%
  数据说明：基于 N 次巡检记录统计
  若无巡检数据：显示「本月暂无巡检数据，请配置巡检任务」

右栏：专线运行状态
  运行正常：N条
  发生故障：N条
  当前停用：N条

中间分隔线

下方：各站点可用性列表
  站点名称 | 在线设备数/总设备数 | 可用性 | 状态
```

---

**第四页：下月行动项**

```
标题：下月重点关注事项

第一节：必须处理（30天内）
  若有：红色背景提示框 + 清单列表
  格式：
  ● [合同到期] 上海电信专线合同 2026-07-10 到期，还有 18 天
               建议：7月5日前完成续签
  ● [保修到期] SW-SHA-01 设备保修 2026-07-15 到期，还有 23 天
               建议：确认是否续保，或列入更换计划

  若无：绿色提示「本月无紧急事项」

第二节：建议关注（31-60天内）
  若有：橙色背景提示框 + 清单列表
  格式：
  ◇ [合同到期] 北京联通专线合同 2026-08-05 到期，还有 43 天
  ◇ [设备老化] 3台设备使用年限超过5年，建议纳入采购计划

  若无：灰色提示「暂无需关注事项」
```

---

**第五页：费用分析**

```
标题：专线费用分析

第一节：本月费用概览
  本月总费用：¥42,800（大字，20pt）
  较上月：+¥2,100（+5.2%）  使用红色/绿色标注
  较去年同期：+¥4,800（+12.6%）

第二节：费用构成（水平条形图）
  互联网专线  ¥22,000  51.4%  ████████████████
  MPLS        ¥12,000  28.0%  ████████
  SD-WAN      ¥8,800   20.6%  ██████
  （使用 reportlab 绘制简单色块条形图，不用复杂图表库）

第三节：近6个月费用趋势（折线图）
  X轴：月份
  Y轴：费用（元）
  数据点标注具体金额
  使用 reportlab 绘制简单折线图

  若所有专线均未填写费用：
  显示「专线费用数据暂未录入，请在专线管理中补充月租费用信息」
```

---

**第六页：故障记录**

```
标题：本月故障记录

顶部统计：
  本月故障：N次  |  平均恢复时长：Xh  |  最长中断：Xh

故障明细表格：
  列：序号 | 专线名称 | 严重程度 | 故障开始时间 | 持续时长 | 根因 | 状态

  严重程度用文字标注：严重/重要/轻微
  根因若为空则显示「待分析」
  状态：已解决/处理中

底部分析文字（根据数据动态生成）：
  - 无故障：「本月未发生专线故障，网络运行稳定。」
  - 有故障：「本月共发生故障N次，主要集中在[故障最多的专线名称]，
             建议重点关注该线路稳定性。」
```

---

### 月报 API 接口

追加到 `backend/src/api/reports.py`（新建文件）：

```
GET  /api/v1/reports/monthly/list
     获取已生成的月报列表
     返回：[{ year, month, file_size, generated_at, download_url }]

POST /api/v1/reports/monthly/generate
     生成指定月份的月报
     Body: { "year": 2026, "month": 6 }
     异步执行，立即返回 { "task_id": "xxx" }

GET  /api/v1/reports/monthly/status/{task_id}
     查询月报生成状态
     返回：{ "status": "generating/done/failed", "progress": 80,
             "download_url": "/api/v1/reports/download/xxx.pdf" }

GET  /api/v1/reports/download/{filename}
     下载月报文件
     返回 PDF 文件流，Content-Disposition: attachment
     权限：viewer 和 super_admin 可下载

DELETE /api/v1/reports/monthly/{year}/{month}
     删除指定月报文件
     权限：仅 super_admin
```

月报文件存储路径：`./data/reports/{year}/report_{year}_{month:02d}.pdf`
文件名格式：`基石运营月报_{company_short_name}_{year}年{month}月.pdf`

---

### 月报数据库记录

新建 `backend/src/models/report.py`：

```python
class MonthlyReport(Base):
    __tablename__ = "monthly_reports"
    id: int
    year: int
    month: int
    file_path: str          # 存储路径
    file_size: int          # 文件大小（字节）
    status: str             # generating / done / failed
    error_message: str      # 生成失败原因
    generated_by: str       # 操作人
    generated_at: datetime
```

---

## 三、前端实现

### 系统设置页面

在现有「系统设置」页面顶部新增「公司信息」卡片：

```
位置：所有设置卡片的最上方
字段：公司全称、公司简称、IT部门名称、IT负责人姓名、IT负责人邮箱
保存按钮：独立保存，不影响其他设置卡片
```

### 管理看板月报区域

在 `ManagerDashboard.vue` 的月报下载区域：

```
标题：运营报告

月报列表（最近6份）：
┌─────────────────────────────────────────┐
│ 2026年6月运营报告  1.2MB  生成于07-01   [↓ 下载] │
│ 2026年5月运营报告  1.1MB  生成于06-01   [↓ 下载] │
│ 2026年4月运营报告  1.0MB  生成于05-01   [↓ 下载] │
└─────────────────────────────────────────┘

底部按钮区：
[生成本月报告]

点击「生成本月报告」后：
1. 按钮变为加载状态「正在生成...」
2. 前端每3秒轮询 /status/{task_id}
3. 生成完成后刷新月报列表，新报告出现在顶部
4. 失败时显示红色错误提示「生成失败：{error_message}」

注意：若 company_name 为空，弹出提示：
「请先在系统设置中填写公司信息，再生成月报」
并提供跳转链接到系统设置页面
```

---

## 开发顺序

**Step 1**：`settings` 表新增公司信息字段 + GET/PUT 接口
**Step 2**：系统设置页面新增「公司信息」卡片
**Step 3**：安装 reportlab + pillow，验证中文字体可用
**Step 4**：`report_generator.py` 数据收集函数（collect_report_data）
**Step 5**：PDF 封面和执行摘要页生成
**Step 6**：PDF 概况、行动项、费用、故障四页生成
**Step 7**：`monthly_reports` 表 migration + reports API 接口
**Step 8**：管理看板月报下载区域前端实现（列表 + 生成按钮 + 轮询）

---

## 注意事项

- reportlab 中文字体：在 Docker 容器中需确认有可用的中文字体文件
  推荐方案：在 Dockerfile 中安装 `fonts-wqy-zenhei`（文泉驿正黑）
  ```dockerfile
  RUN apt-get install -y fonts-wqy-zenhei
  ```
  然后在 reportlab 中注册：
  ```python
  from reportlab.pdfbase import pdfmetrics
  from reportlab.pdfbase.ttfonts import TTFont
  pdfmetrics.registerFont(TTFont('WenQuanYi', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'))
  ```

- 月报生成是耗时操作（数据收集+PDF渲染），放入后台异步任务，不阻塞请求
  使用 asyncio 或 ThreadPoolExecutor 执行 reportlab（reportlab 是同步库）

- 若某月数据不完整（无巡检记录、无故障记录等），对应页面显示「暂无数据」
  不报错，不影响其他页面的正常生成

- 月报文件路径加入 .gitignore，不提交到代码库
  ```gitignore
  data/reports/
  ```

- 每个月只能生成一份报告，重复点击「生成」时：
  若已有该月报告，弹出确认：「本月报告已存在，是否重新生成？重新生成将覆盖原文件」

- 公司名称为空时不阻止其他功能使用，只在生成月报时提示填写
