"""运营月报 PDF 生成服务"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import json
import calendar

from sqlalchemy import select, func, and_, or_, Date, cast
from sqlalchemy.ext.asyncio import AsyncSession

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.graphics.shapes import Drawing, Rect, Line, Circle, String
from reportlab.pdfgen import canvas

from src.models.circuit import Circuit
from src.models.circuit_incident import CircuitIncident
from src.models.device import Device
from src.models.setting import Setting


REPORT_DIR = Path(__file__).parent.parent.parent / "data" / "reports"
COMPANY_INFO_KEY = "company_info"


@dataclass
class MonthlyReportData:
    year: int
    month: int
    company_name: str = ""
    company_short_name: str = ""
    it_department: str = "信息技术部"
    it_contact: str = ""
    generated_at: datetime = field(default_factory=datetime.now)

    # 本月概况
    availability_pct: Optional[float] = None
    circuit_cost_total: int = 0
    incident_count: int = 0
    max_duration_hours: float = 0
    circuit_count: int = 0

    # 下月行动项
    urgent_items: list = field(default_factory=list)
    warning_items: list = field(default_factory=list)

    # 故障明细
    incidents: list = field(default_factory=list)
    avg_recovery_hours: float = 0

    # 费用分析
    cost_by_type: list = field(default_factory=list)  # [{"type": "互联网专线", "cost": 22000, "pct": 51.4}]
    cost_history: list = field(default_factory=list)   # [{"month": "2026-01", "cost": 40000}, ...]


async def get_company_info(db: AsyncSession) -> dict:
    """从数据库获取公司信息"""
    result = await db.execute(select(Setting).filter(Setting.key == COMPANY_INFO_KEY))
    setting = result.scalars().first()
    if setting:
        try:
            return json.loads(setting.value)
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


async def collect_report_data(year: int, month: int, db: AsyncSession) -> MonthlyReportData:
    """从数据库收集月报所需数据"""
    # 所有时间统一用 UTC 时区感知，避免 PostgreSQL DateTime(timezone=True) 列不匹配
    utc = timezone.utc
    month_start = datetime(year, month, 1, tzinfo=utc)
    next_month = datetime(
        year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1,
        tzinfo=utc
    )

    # 用于展示的北京时间
    beijing_tz = timezone(timedelta(hours=8))
    bj_now = datetime.now(beijing_tz)

    # 公司信息
    company = await get_company_info(db)

    # 专线统计
    cost_result = await db.execute(
        select(func.coalesce(func.sum(Circuit.monthly_cost), 0))
        .where(or_(Circuit.status == 'active', Circuit.status == '正常'))
    )
    total_cost = int(cost_result.scalar() or 0)

    circuit_count_result = await db.execute(
        select(func.count(Circuit.id))
        .where(or_(Circuit.status == 'active', Circuit.status == '正常'))
    )
    circuit_count = circuit_count_result.scalar() or 0

    # 费用按类型分组
    cost_by_type_result = await db.execute(
        select(Circuit.type, func.coalesce(func.sum(Circuit.monthly_cost), 0))
        .where(and_(
            or_(Circuit.status == 'active', Circuit.status == '正常'),
            Circuit.type != None,
            Circuit.type != ''
        ))
        .group_by(Circuit.type)
    )
    raw_cost_by_type = cost_by_type_result.all()
    cost_by_type = []
    for t, c in raw_cost_by_type:
        pct = round(c / total_cost * 100, 1) if total_cost > 0 else 0
        cost_by_type.append({"type": t, "cost": int(c), "pct": pct})

    # 近6个月费用历史（从现有专线数据推算）
    cost_history = []
    for i in range(5, -1, -1):
        ym = bj_now.replace(day=1) - timedelta(days=30 * i)
        cost_history.append({
            "month": ym.strftime("%Y-%m"),
            "cost": total_cost  # 静态取当前月费用作为近似
        })

    # 计算网络可用性：从 inspection_device_results 表统计本月在线率
    from src.models.inspection import InspectionDeviceResult
    # 使用时区感知区间过滤 scanned_at，避免字段名和时区不一致导致的错误
    avail_result = await db.execute(
        select(func.count(InspectionDeviceResult.id)).where(
            and_(
                InspectionDeviceResult.scanned_at >= month_start,
                InspectionDeviceResult.scanned_at < next_month
            )
        )
    )
    total_count = avail_result.scalar() or 0

    online_result = await db.execute(
        select(func.count(InspectionDeviceResult.id)).where(
            and_(
                InspectionDeviceResult.scanned_at >= month_start,
                InspectionDeviceResult.scanned_at < next_month,
                InspectionDeviceResult.is_online.is_(True)
            )
        )
    )
    online_count = online_result.scalar() or 0

    availability_pct = (online_count / total_count * 100) if total_count > 0 else None

    # 本月故障统计
    incidents_result = await db.execute(
        select(func.count(CircuitIncident.id))
        .where(and_(
            CircuitIncident.created_at >= month_start,
            CircuitIncident.created_at < next_month
        ))
    )
    incident_count = incidents_result.scalar() or 0

    max_duration_min_result = await db.execute(
        select(func.coalesce(func.max(CircuitIncident.duration_minutes), 0))
        .where(and_(
            CircuitIncident.created_at >= month_start,
            CircuitIncident.created_at < next_month
        ))
    )
    max_duration = float(max_duration_min_result.scalar() or 0) / 60.0

    avg_recovery_min_result = await db.execute(
        select(func.coalesce(func.avg(CircuitIncident.duration_minutes), 0))
        .where(and_(
            CircuitIncident.created_at >= month_start,
            CircuitIncident.created_at < next_month,
            CircuitIncident.duration_minutes > 0
        ))
    )
    avg_recovery = float(avg_recovery_min_result.scalar() or 0) / 60.0

    # 故障明细
    incidents_list_result = await db.execute(
        select(
            CircuitIncident.title,
            CircuitIncident.severity,
            CircuitIncident.started_at,
            CircuitIncident.duration_minutes,
            CircuitIncident.status,
            CircuitIncident.id
        )
        .where(and_(
            CircuitIncident.created_at >= month_start,
            CircuitIncident.created_at < next_month
        ))
        .order_by(CircuitIncident.started_at.desc())
    )
    incidents_list = incidents_list_result.all()

    # 到期事项（使用 date 比较，避免 datetime 时区兼容问题）
    thirty_days_later = bj_now.date() + timedelta(days=30)
    sixty_days_later = bj_now.date() + timedelta(days=60)
    bj_today = bj_now.date()

    urgent_circuits_result = await db.execute(
        select(Circuit.name, Circuit.contract_end, Circuit.provider)
        .where(and_(
            Circuit.contract_end != None,
            cast(Circuit.contract_end, Date) <= thirty_days_later
        ))
    )
    urgent_items = []
    for c in urgent_circuits_result.all():
        end_date = c.contract_end.date() if hasattr(c.contract_end, 'date') else c.contract_end
        days_left = (end_date - bj_today).days if end_date else -1
        if days_left >= 0:
            urgent_items.append({
                "type": "专线合同",
                "name": c.name,
                "expire_date": end_date.strftime("%Y-%m-%d") if end_date else "",
                "days_left": days_left
            })

    urgent_warranties_result = await db.execute(
        select(Device.name, Device.warranty_end, Device.model)
        .where(and_(
            Device.warranty_end != None,
            cast(Device.warranty_end, Date) <= thirty_days_later
        ))
    )
    for d in urgent_warranties_result.all():
        end_date = d.warranty_end.date() if hasattr(d.warranty_end, 'date') else d.warranty_end
        days_left = (end_date - bj_today).days if end_date else -1
        if days_left >= 0:
            urgent_items.append({
                "type": "设备保修",
                "name": d.name,
                "expire_date": end_date.strftime("%Y-%m-%d") if end_date else "",
                "days_left": days_left
            })

    warning_items = []
    warning_circuits_result = await db.execute(
        select(Circuit.name, Circuit.contract_end, Circuit.provider)
        .where(and_(
            Circuit.contract_end != None,
            cast(Circuit.contract_end, Date) <= sixty_days_later,
            cast(Circuit.contract_end, Date) > thirty_days_later
        ))
    )
    for c in warning_circuits_result.all():
        end_date = c.contract_end.date() if hasattr(c.contract_end, 'date') else c.contract_end
        days_left = (end_date - bj_today).days if end_date else -1
        if days_left >= 0:
            warning_items.append({
                "type": "专线合同",
                "name": c.name,
                "expire_date": end_date.strftime("%Y-%m-%d") if end_date else "",
                "days_left": days_left
            })

    warning_warranties_result = await db.execute(
        select(Device.name, Device.warranty_end, Device.model)
        .where(and_(
            Device.warranty_end != None,
            cast(Device.warranty_end, Date) <= sixty_days_later,
            cast(Device.warranty_end, Date) > thirty_days_later
        ))
    )
    for d in warning_warranties_result.all():
        end_date = d.warranty_end.date() if hasattr(d.warranty_end, 'date') else d.warranty_end
        days_left = (end_date - bj_today).days if end_date else -1
        if days_left >= 0:
            warning_items.append({
                "type": "设备保修",
                "name": d.name,
                "expire_date": end_date.strftime("%Y-%m-%d") if end_date else "",
                "days_left": days_left
            })

    return MonthlyReportData(
        year=year,
        month=month,
        company_name=company.get("company_name", ""),
        company_short_name=company.get("company_short_name", ""),
        it_department=company.get("it_department_name", "信息技术部"),
        it_contact=company.get("it_contact_name", ""),
        generated_at=bj_now,
        availability_pct=availability_pct,
        circuit_cost_total=total_cost,
        incident_count=incident_count,
        max_duration_hours=max_duration,
        circuit_count=circuit_count,
        avg_recovery_hours=avg_recovery,
        urgent_items=sorted(urgent_items, key=lambda x: x["days_left"]),
        warning_items=sorted(warning_items, key=lambda x: x["days_left"]),
        cost_by_type=cost_by_type,
        cost_history=cost_history,
        incidents=[{
            "title": i.title or "-",
            "severity": i.severity or "low",
            "started_at": (i.started_at + timedelta(hours=8)).strftime("%m-%d %H:%M") if i.started_at else "-",
            "duration": f"{(i.duration_minutes or 0)/60.0:.1f}" if i.duration_minutes else "-",
            "status": "已恢复" if i.status == "resolved" else "处理中"
        } for i in incidents_list]
    )


def _register_fonts():
    """注册中文字体。优先使用项目内开源中文字体（Noto Sans SC），如果不存在再尝试系统字体路径。"""
    import os
    # 项目内字体优先：backend/fonts/noto-sans-sc-regular.ttf（开源免费商用）
    # 放在 backend/fonts/ 而非 data/fonts/，避免 Docker 卷挂载 data/ 覆盖字体
    project_font = Path(__file__).parent.parent.parent / "fonts" / "noto-sans-sc-regular.ttf"

    font_candidates = [str(project_font),
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for path in font_candidates:
        try:
            if not path or not os.path.exists(path):
                continue
            pdfmetrics.registerFont(TTFont("WenQuanYi", path))
            pdfmetrics.registerFont(TTFont("WenQuanYi-Bold", path))
            return True
        except Exception:
            continue
    return False


def draw_cover_page(c, data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm

    width, height = A4  # 595.28 x 841.89

    # === 第一步：画蓝色背景块，必须在所有其他绘图之前 ===
    c.setFillColor(HexColor('#1F4E79'))
    c.rect(0, height * 0.55, width, height * 0.45, fill=1, stroke=0)

    # === 第二步：蓝色区域内的白色文字 ===
    # 公司简称（左上角白色小字）
    if hasattr(data, 'company_short_name') and data.company_short_name:
        c.setFillColor(HexColor('#FFFFFF'))
        c.setFont('WenQuanYi', 12)
        c.drawString(25*mm, height - 22*mm, data.company_short_name)

    # 报告主标题（居中白色大字）
    c.setFillColor(HexColor('#FFFFFF'))
    try:
        c.setFont('WenQuanYi-Bold', 26)
    except:
        c.setFont('WenQuanYi', 26)
    c.drawCentredString(width / 2, height * 0.73, 'IT基础设施运营月报')

    # 年月副标题（居中淡蓝色）
    c.setFont('WenQuanYi', 16)
    c.setFillColor(HexColor('#BDD7EE'))
    subtitle = f"{data.year}年{data.month}月"
    c.drawCentredString(width / 2, height * 0.65, subtitle)

    # === 第三步：白色区域内容 ===
    # 分隔线
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.setLineWidth(0.5)
    c.line(25*mm, height * 0.53, width - 25*mm, height * 0.53)

    # 公司信息（左对齐）
    y = height * 0.49
    info_items = []
    if hasattr(data, 'company_name') and data.company_name:
        info_items.append(('公司名称', data.company_name))
    last_day = calendar.monthrange(data.year, data.month)[1]
    info_items.append(('报告周期',
        f"{data.year}年{data.month}月1日 至 {data.year}年{data.month}月{last_day}日"))
    info_items.append(('生成时间', data.generated_at.strftime('%Y年%m月%d日 %H:%M')))
    info_items.append(('生成系统', '基石 Cornerstone · IT基础设施资源管理平台'))

    for label, value in info_items:
        c.setFont('WenQuanYi', 10)
        c.setFillColor(HexColor('#888888'))
        c.drawString(25*mm, y, f"{label}：")
        c.setFillColor(HexColor('#333333'))
        c.drawString(25*mm + 48, y, value)
        y -= 18

    # === 第四步：底部蓝色装饰条 ===
    c.setFillColor(HexColor('#1F4E79'))
    c.rect(0, 0, width, 8, fill=1, stroke=0)

    # === 最后：换页（只能调用一次）===
    c.showPage()


def draw_summary_page(c, data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm

    width, height = A4
    left_margin = 25*mm
    y = height - 25*mm

    # 标题
    try:
        c.setFont('WenQuanYi-Bold', 16)
    except:
        c.setFont('WenQuanYi', 16)
    c.setFillColor(HexColor('#1F4E79'))
    c.drawString(left_margin, y, '执行摘要')
    y -= 8*mm

    # 动态要点列表
    icon_ok = "✔"
    icon_warn = "⚠"
    icon_crit = "🔴"

    summary_points = []
    if data.availability_pct is not None:
        if data.availability_pct >= 99:
            summary_points.append((icon_ok, f"网络整体运行稳定，可用性达{data.availability_pct:.1f}%", "#67C23A"))
        else:
            summary_points.append((icon_warn, f"网络可用性{data.availability_pct:.1f}%，低于目标值99%", "#E6A23C"))
    if data.incident_count == 0:
        summary_points.append((icon_ok, "本月未发生专线故障", "#67C23A"))
    else:
        summary_points.append((icon_warn, f"发生故障{data.incident_count}次，平均恢复时长{data.avg_recovery_hours:.1f}小时", "#E6A23C"))
    if data.circuit_cost_total > 0:
        summary_points.append((icon_ok, f"本月专线月租总费用 ¥{data.circuit_cost_total:,}", "#1F4E79"))
    if data.urgent_items:
        summary_points.append((icon_crit, f"下月有{len(data.urgent_items)}项合同/保修即将到期（30天内）", "#F56C6C"))

    c.setFont('WenQuanYi', 12)
    for icon, text, color in summary_points:
        c.setFillColor(HexColor(color))
        c.drawString(left_margin, y, f"{icon} {text}")
        y -= 18

    y -= 6*mm

    # 水平分隔线
    c.setStrokeColor(HexColor('#E0E0E0'))
    c.setLineWidth(0.5)
    c.line(left_margin, y, width - 20*mm, y)
    y -= 10*mm

    # 关键指标标题
    try:
        c.setFont('WenQuanYi-Bold', 16)
    except:
        c.setFont('WenQuanYi', 16)
    c.setFillColor(HexColor('#1F4E79'))
    c.drawString(left_margin, y, '关键指标')
    y -= 10*mm

    c.showPage()


def draw_overview_page(c, data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm

    width, height = A4
    left_margin = 25*mm
    y = height - 25*mm

    # 标题
    try:
        c.setFont('WenQuanYi-Bold', 16)
    except:
        c.setFont('WenQuanYi', 16)
    c.setFillColor(HexColor('#1F4E79'))
    c.drawString(left_margin, y, '本月运营概况')
    y -= 15*mm

    # 左侧：网络可用性标题
    try:
        c.setFont('WenQuanYi-Bold', 18)
    except:
        c.setFont('WenQuanYi', 18)
    c.setFillColor(HexColor('#1F4E79'))
    c.drawString(left_margin, y, '网络可用性')
    y -= 15*mm

    # 修复可用性数字断开问题 - 合并绘制
    if data.availability_pct is not None:
        if data.availability_pct >= 99:
            color = '#67C23A'
        else:
            color = '#E6A23C'
        availability_str = f"{data.availability_pct:.1f}%"
        try:
            c.setFont('WenQuanYi-Bold', 64)
        except:
            c.setFont('WenQuanYi', 64)
        c.setFillColor(HexColor(color))
        c.drawString(left_margin, y, availability_str)
    else:
        c.setFont('WenQuanYi', 24)
        c.setFillColor(HexColor('#999999'))
        c.drawString(left_margin, y, '暂无数据')
    y -= 30*mm

    # 说明文字
    c.setFont('WenQuanYi', 12)
    c.setFillColor(HexColor('#999999'))
    if data.availability_pct is not None:
        c.drawString(left_margin, y, '基于巡检记录统计')
    else:
        c.drawString(left_margin, y, '请配置巡检任务获取数据')

    c.showPage()


def draw_action_items_page(c, data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm

    width, height = A4
    left_margin = 25*mm
    y = height - 25*mm

    # 标题
    try:
        c.setFont('WenQuanYi-Bold', 16)
    except:
        c.setFont('WenQuanYi', 16)
    c.setFillColor(HexColor('#1F4E79'))
    c.drawString(left_margin, y, '下月重点关注事项')
    y -= 15*mm

    # 第一节：必须处理（30天内到期）
    if data.urgent_items:
        c.setFont('WenQuanYi', 11)
        c.setFillColor(HexColor('#F56C6C'))
        c.drawString(left_margin, y, '🔴 必须处理（30天内到期）')
        y -= 12*mm

        for item in data.urgent_items:
            text = f"● [{item['type']}] {item['name']} {item['expire_date']} 到期，还有 {item['days_left']} 天"
            c.setFont('WenQuanYi', 11)
            c.setFillColor(HexColor('#F56C6C'))
            c.drawString(left_margin + 5*mm, y, text)
            y -= 18

    y -= 8*mm

    # 第二节：建议关注（31-60天内到期）
    if data.warning_items:
        c.setFont('WenQuanYi', 11)
        c.setFillColor(HexColor('#E6A23C'))
        c.drawString(left_margin, y, '🟡 建议关注（31-60天内到期）')
        y -= 12*mm

        for item in data.warning_items:
            text = f"◇ [{item['type']}] {item['name']} {item['expire_date']} 到期，还有 {item['days_left']} 天"
            c.setFont('WenQuanYi', 11)
            c.setFillColor(HexColor('#E6A23C'))
            c.drawString(left_margin + 5*mm, y, text)
            y -= 18

    c.showPage()


def draw_cost_analysis_page(c, data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm

    width, height = A4
    left_margin = 25*mm
    y = height - 25*mm

    # 标题
    try:
        c.setFont('WenQuanYi-Bold', 16)
    except:
        c.setFont('WenQuanYi', 16)
    c.setFillColor(HexColor('#1F4E79'))
    c.drawString(left_margin, y, '专线费用分析')
    y -= 15*mm

    # 费用概览
    if data.circuit_cost_total > 0:
        c.setFont('WenQuanYi', 11)
        c.setFillColor(HexColor('#1F4E79'))
        c.drawString(left_margin, y, '本月费用概览')
        y -= 8*mm

        try:
            c.setFont('WenQuanYi-Bold', 24)
        except:
            c.setFont('WenQuanYi', 24)
        c.setFillColor(HexColor('#1F4E79'))
        c.drawString(left_margin, y, f"¥{data.circuit_cost_total:,}")
        y -= 15*mm

        c.setFont('WenQuanYi', 11)
        c.setFillColor(HexColor('#1F4E79'))
        c.drawString(left_margin, y, '费用构成')
        y -= 12*mm

        # 费用构成彩色条形图
        TYPE_COLORS = {
            'internet':  '#378ADD',
            'mpls':      '#1D9E75',
            'sdwan':     '#EF9F27',
            'fiber':     '#9B59B6',
            'cloud':     '#36CFC9',
            'other':     '#909399',
        }
        TYPE_LABELS = {
            'internet': '互联网专线',
            'mpls':     'MPLS',
            'sdwan':    'SD-WAN',
            'fiber':    '裸光纤',
            'cloud':    '云专线',
            'other':    '其他',
        }

        # 条形图参数
        label_col_width = 52   # 左侧标签列宽度（points）
        bar_max_width = 200    # 条形最大宽度（points）
        bar_height = 12        # 条形高度
        row_gap = 20           # 行间距
        total_cost = data.circuit_cost_total or 1

        # 按金额从大到小排序
        sorted_types = sorted(data.cost_by_type, key=lambda x: x.get('cost', 0), reverse=True)

        for item in sorted_types:
            type_key = item.get('type', 'other')
            amount = item.get('cost', 0)
            if amount <= 0:
                continue

            pct = amount / total_cost * 100
            bar_w = bar_max_width * (amount / total_cost)
            color_hex = TYPE_COLORS.get(type_key, '#909399')
            label = TYPE_LABELS.get(type_key, type_key)

            # 左侧标签（右对齐，固定列宽）
            c.setFont('WenQuanYi', 9)
            c.setFillColor(HexColor('#555555'))
            # 截断过长标签，避免换行
            if c.stringWidth(label, 'WenQuanYi', 9) > label_col_width - 4:
                label = label[:4] + '..'
            c.drawRightString(left_margin + label_col_width, y + 2, label)

            # 彩色条形色块
            c.setFillColor(HexColor(color_hex))
            c.rect(left_margin + label_col_width + 4, y, bar_w, bar_height, fill=1, stroke=0)

            # 右侧数值（金额+百分比）
            c.setFont('WenQuanYi', 9)
            c.setFillColor(HexColor('#333333'))
            value_str = f"¥{amount:,}  {pct:.1f}%"
            c.drawString(left_margin + label_col_width + 4 + bar_w + 6, y + 2, value_str)

            y -= row_gap

    c.showPage()


def draw_incident_page(c, data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm

    width, height = A4
    left_margin = 25*mm
    y = height - 25*mm

    # 标题
    try:
        c.setFont('WenQuanYi-Bold', 16)
    except:
        c.setFont('WenQuanYi', 16)
    c.setFillColor(HexColor('#1F4E79'))
    c.drawString(left_margin, y, '本月故障记录')
    y -= 15*mm

    if data.incidents:
        # 顶部统计
        c.setFont('WenQuanYi', 9)
        c.setFillColor(HexColor('#666666'))

        # 三列统计
        col1_x = left_margin
        col2_x = left_margin + 50*mm
        col3_x = left_margin + 100*mm

        c.drawCentredString(col1_x + 25*mm, y, '故障次数')
        c.drawCentredString(col2_x + 25*mm, y, '平均恢复')
        c.drawCentredString(col3_x + 25*mm, y, '最长中断')
        y -= 12*mm

        try:
            c.setFont('WenQuanYi-Bold', 16)
        except:
            c.setFont('WenQuanYi', 16)
        c.setFillColor(HexColor('#1F4E79'))
        c.drawCentredString(col1_x + 25*mm, y, str(data.incident_count))
        c.drawCentredString(col2_x + 25*mm, y, f"{data.avg_recovery_hours:.1f}h")
        c.drawCentredString(col3_x + 25*mm, y, f"{data.max_duration_hours:.1f}h")
        y -= 15*mm

    y -= 10*mm

    if data.incidents:
        # 表格标题
        c.setFont('WenQuanYi-Bold', 10)
        c.setFillColor(HexColor('#FFFFFF'))
        # 绘制表头背景
        c.setFillColor(HexColor('#1F4E79'))
        c.rect(left_margin, y - 8, width - left_margin - 20*mm, 20, fill=1, stroke=0)

        # 表头文字
        c.setFillColor(HexColor('#FFFFFF'))
        c.drawString(left_margin + 5, y + 4, '故障标题')
        c.drawString(left_margin + 60*mm + 5, y + 4, '严重程度')
        c.drawString(left_margin + 80*mm + 5, y + 4, '发生时间')
        c.drawString(left_margin + 110*mm + 5, y + 4, '时长(h)')
        c.drawString(left_margin + 128*mm + 5, y + 4, '状态')
        y -= 20*mm

        # 表格内容
        c.setFont('WenQuanYi', 9)
        sev_map = {'high': '严重', 'medium': '重要', 'low': '轻微'}
        for i, inc in enumerate(data.incidents):
            sev_label = sev_map.get(inc['severity'], inc['severity'])
            if i % 2 == 0:
                c.setFillColor(HexColor('#F5F7FA'))
                c.rect(left_margin, y - 5, width - left_margin - 20*mm, 20, fill=1, stroke=0)

            c.setFillColor(HexColor('#333333'))
            c.drawString(left_margin + 5, y + 2, inc['title'][:25])
            c.drawString(left_margin + 60*mm + 5, y + 2, sev_label)
            c.drawString(left_margin + 80*mm + 5, y + 2, inc['started_at'])
            c.drawString(left_margin + 110*mm + 5, y + 2, inc['duration'])
            c.drawString(left_margin + 128*mm + 5, y + 2, inc['status'])
            y -= 20*mm

    else:
        c.setFont('WenQuanYi', 10)
        c.setFillColor(HexColor('#67C23A'))
        c.drawString(left_margin, y, '本月未发生专线故障，网络运行稳定。')

    c.showPage()


def generate_report_pdf(data: MonthlyReportData, output_path: str):
    """生成运营月报 PDF"""
    # 注册字体
    _register_fonts()

    c = canvas.Canvas(output_path, pagesize=A4)

    # 每个页面函数内部调用一次 showPage
    draw_cover_page(c, data)
    draw_summary_page(c, data)
    draw_overview_page(c, data)
    draw_action_items_page(c, data)
    draw_cost_analysis_page(c, data)
    draw_incident_page(c, data)

    c.save()
    return output_path


def get_report_filename(data: MonthlyReportData) -> str:
    """生成报告文件名"""
    short = data.company_short_name or "基石"
    return f"基石运营月报_{short}_{data.year}年{data.month:02d}月.pdf"
