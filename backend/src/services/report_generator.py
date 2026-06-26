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
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.graphics.shapes import Drawing, Rect, Line, Circle, String

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
            pdfmetrics.registerFont(TTFont("ChineseFont", path))
            return True
        except Exception:
            continue
    return False


def _make_bar_cell(width_mm, bar_color, sty):
    """创建一个简单的色块条形图单元格"""
    data = [['']]
    t = Table(data, colWidths=[max(width_mm, 2)])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bar_color)),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def _get_styles():
    """获取样式集合，尝试注册中文字体"""
    styles = getSampleStyleSheet()
    has_cn = _register_fonts()
    font_name = "ChineseFont" if has_cn else "Helvetica"
    font_name_bold = "ChineseFont" if has_cn else "Helvetica-Bold"

    return {
        "title": ParagraphStyle(
            'ReportTitle', fontName=font_name_bold,
            fontSize=18, leading=24, spaceAfter=8*mm,
            textColor=colors.HexColor('#1a1a2e')
        ),
        "subtitle": ParagraphStyle(
            'ReportSubtitle', fontName=font_name,
            fontSize=14, leading=20, spaceAfter=8*mm,
            textColor=colors.HexColor('#666666')
        ),
        "section": ParagraphStyle(
            'SectionTitle', fontName=font_name_bold,
            fontSize=16, leading=22, spaceBefore=6*mm, spaceAfter=4*mm,
            textColor=colors.HexColor('#1F4E79')
        ),
        "body": ParagraphStyle(
            'Body', fontName=font_name,
            fontSize=12, leading=18, spaceAfter=2*mm
        ),
        "body_center": ParagraphStyle(
            'BodyCenter', fontName=font_name,
            fontSize=12, leading=18, alignment=1
        ),
        "small": ParagraphStyle(
            'Small', fontName=font_name,
            fontSize=10, leading=14
        ),
        "footer": ParagraphStyle(
            'Footer', fontName=font_name,
            fontSize=8, textColor=colors.HexColor('#999999'), alignment=1
        ),
        "big_number": ParagraphStyle(
            'BigNumber', fontName=font_name_bold,
            fontSize=32, leading=38, alignment=1,
            textColor=colors.HexColor('#1F4E79')
        ),
        "big_number_green": ParagraphStyle(
            'BigNumberGreen', fontName=font_name_bold,
            fontSize=32, leading=38, alignment=1,
            textColor=colors.HexColor('#67C23A')
        ),
        "big_number_red": ParagraphStyle(
            'BigNumberRed', fontName=font_name_bold,
            fontSize=32, leading=38, alignment=1,
            textColor=colors.HexColor('#F56C6C')
        ),
        "kpi_label": ParagraphStyle(
            'KPILabel', fontName=font_name,
            fontSize=10, leading=14, alignment=1,
            textColor=colors.HexColor('#666666')
        ),
        "item_urgent": ParagraphStyle(
            'ItemUrgent', fontName=font_name,
            fontSize=11, leading=18, leftIndent=0,
            textColor=colors.HexColor('#F56C6C')
        ),
        "item_warning": ParagraphStyle(
            'ItemWarning', fontName=font_name,
            fontSize=11, leading=18, leftIndent=0,
            textColor=colors.HexColor('#E6A23C')
        ),
    }


def _make_header_footer(doc, sty: dict, data: MonthlyReportData):
    """添加页眉和页脚"""
    from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
    from reportlab.platypus import PageBreak

    company_short = data.company_short_name or "基石"
    month_label = f"{data.year}年{data.month}月"
    # 使用注册好的中文字体（如果注册成功）
    font_name = sty['footer'].fontName

    def header_footer(canvas, doc):
        canvas.saveState()
        # 页眉
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor('#999999'))
        canvas.drawString(25*mm, A4[1] - 15*mm, f"基石 · IT基础设施运营月报")
        canvas.drawRightString(A4[0] - 25*mm, A4[1] - 15*mm, month_label)
        canvas.setStrokeColor(colors.HexColor('#E0E0E0'))
        canvas.setLineWidth(0.5)
        canvas.line(25*mm, A4[1] - 18*mm, A4[0] - 25*mm, A4[1] - 18*mm)
        # 页脚
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor('#999999'))
        canvas.drawString(25*mm, 15*mm, f"{company_short} · {data.it_department}")
        canvas.drawRightString(A4[0] - 25*mm, 15*mm, f"第 {doc.page} 页")
        canvas.setStrokeColor(colors.HexColor('#E0E0E0'))
        canvas.setLineWidth(0.5)
        canvas.line(25*mm, 18*mm, A4[0] - 25*mm, 18*mm)
        canvas.restoreState()

    return header_footer


def generate_report_pdf(data: MonthlyReportData, output_path: str):
    """生成运营月报 PDF"""
    sty = _get_styles()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=25*mm, bottomMargin=20*mm,
        leftMargin=25*mm, rightMargin=20*mm
    )

    elements = []

    # ===== 第一页：封面 =====
    # 按规范重新设计：顶部深蓝色背景块占页面上方45%，白色文字
    from reportlab.lib.colors import HexColor

    # 使用 Drawing 在整个页面绘制背景（Table方式容易留白边）
    width, height = A4
    cover_d = Drawing(width, height)
    # 顶部深蓝色背景块
    cover_d.add(Rect(0, height * 0.55, width, height * 0.45,
                   fillColor=HexColor('#1F4E79'), strokeColor=None))
    # 底部蓝色装饰线
    cover_d.add(Rect(0, 0, width, 8,
                   fillColor=HexColor('#1F4E79'), strokeColor=None))
    elements.append(cover_d)

    # 蓝色区域内文字（Y从顶部往下递减）
    y = height - 22*mm
    # 公司简称（左上角，Logo区域）
    if data.company_short_name:
        company_short_style = ParagraphStyle(
            'CompanyShort', fontName=sty['title'].fontName,
            fontSize=13, leading=18,
            textColor=colors.white
        )
        p = Paragraph(data.company_short_name, company_short_style)
        # 在蓝色块内靠左上方放置
        cover_header_table = Table([[p]], colWidths=[width], rowHeights=[height * 0.45])
        cover_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.transparent),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 22*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 25*mm),
        ]))
        elements.append(cover_header_table)

    # 主标题（居中）
    elements.append(Spacer(1, int(height * 0.45 * 0.3)))
    cover_title_style = ParagraphStyle(
        'CoverTitle', fontName=sty['title'].fontName,
        fontSize=26, leading=34, alignment=1,
        textColor=colors.white
    )
    elements.append(Paragraph("IT基础设施运营月报", cover_title_style))
    # 年月副标题（淡蓝色）
    cover_sub_style = ParagraphStyle(
        'CoverSub', fontName=sty['body'].fontName,
        fontSize=16, leading=22, alignment=1,
        textColor=HexColor('#BDD7EE')
    )
    elements.append(Paragraph(f"{data.year}年{data.month}月", cover_sub_style))
    elements.append(Spacer(1, int(height * 0.45 * 0.2)))

    # 细线分隔蓝色区域和白色区域
    sep_table = Table([['']], colWidths=[width - 50*mm])
    sep_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#CCCCCC')),
        ('TOPPADDING', (0, 0), (-1, -1), 0.25),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.25),
    ]))
    elements.append(sep_table)
    elements.append(Spacer(1, 4*mm))

    # 白色区域：公司信息
    info_style = ParagraphStyle(
        'CoverInfo', fontName=sty['body'].fontName,
        fontSize=10, leading=18,
        textColor=colors.HexColor('#333333')
    )
    info_label_style = ParagraphStyle(
        'CoverInfoLabel', fontName=sty['body'].fontName,
        fontSize=10, leading=18,
        textColor=colors.HexColor('#888888')
    )

    last_day = calendar.monthrange(data.year, data.month)[1]
    info_lines = [
        ("公司名称", data.company_name or "(请在系统设置中填写)"),
        ("报告周期", f"{data.year}年{data.month}月1日 至 {data.year}年{data.month}月{last_day}日"),
        ("生成时间", data.generated_at.strftime('%Y年%m月%d日 %H:%M')),
        ("生成系统", "基石 Cornerstone · IT基础设施资源管理平台"),
    ]

    for label, value in info_lines:
        if value:
            row_data = [[
                Paragraph(label + "：", info_label_style),
                Paragraph(value, info_style)
            ]]
            t = Table(row_data, colWidths=[50*mm, width - 75*mm])
            t.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(t)
        elements.append(Spacer(1, 1*mm))

    # 封面结束，分页进入正文，后续页面由页眉页脚处理
    elements.append(PageBreak())

    # ===== 第二页：执行摘要 =====
    elements.append(Paragraph("执行摘要", sty['section']))
    elements.append(Spacer(1, 4*mm))

    # 动态要点列表（带状态图标）
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

    # 渲染要点
    # 用 Drawing 画方形图标，避免 Unicode 符号在不同 PDF 阅读器出现空白/方框
    for icon, text, color in summary_points:
        # 左侧自定义勾选框图标
        d = Drawing(10, 10)
        d.add(Rect(0, 0, 9, 9, strokeColor=colors.HexColor(color), fillColor=None, strokeWidth=1))
        # 组装成一行：小图标 + 文本
        row = Table([[d, Paragraph(text, ParagraphStyle(
            'SummaryPoint', fontName=sty['body'].fontName,
            fontSize=12, leading=18,
            textColor=colors.HexColor(color)
        ))]], colWidths=[6*mm, 140*mm])
        row.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))
        elements.append(row)
        elements.append(Spacer(1, 1*mm))

    elements.append(Spacer(1, 4*mm))
    # 水平分隔线
    sep_table = Table([['']], colWidths=[150*mm])
    sep_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E0E0E0')),
        ('TOPPADDING', (0, 0), (-1, -1), 0.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
    ]))
    elements.append(sep_table)
    elements.append(Spacer(1, 6*mm))

    elements.append(Paragraph("关键指标", sty['section']))
    elements.append(Spacer(1, 4*mm))

    # 创建独立KPI卡片：每个卡片有圆角边框，数字放大在上，标签缩小在下
    def kpi_card(label, value, color="#1F4E79"):
        """生成一个独立KPI卡片"""
        # 数字放大在上，标签在下
        card_data = [
            [Paragraph(str(value), ParagraphStyle(
                'KPINum', fontName=sty['big_number'].fontName,
                fontSize=28, leading=32, alignment=1,
                textColor=colors.HexColor(color)
            ))],
            [Paragraph(label, sty['kpi_label'])],
        ]
        t = Table(card_data, colWidths=[45*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), [4, 4, 4, 4]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        return t

    status_green = "#67C23A"
    status_orange = "#E6A23C"
    status_red = "#F56C6C"

    avail_text = "暂无数据" if data.availability_pct is None else f"{data.availability_pct:.1f}%"
    avail_color = status_green if data.availability_pct is None or data.availability_pct >= 99 else status_orange
    incident_color = status_green if data.incident_count == 0 else (status_orange if data.incident_count <= 3 else status_red)
    urgent_color = status_green if not data.urgent_items else (status_orange if len(data.urgent_items) <= 3 else status_red)

    # 第一行三个卡片
    kpi_row1 = [
        kpi_card("网络可用性", avail_text, avail_color),
        kpi_card("专线费用", f"¥{data.circuit_cost_total:,}", "#1F4E79"),
        kpi_card("故障次数", str(data.incident_count), incident_color),
    ]
    # 第二行三个卡片
    kpi_row2 = [
        kpi_card("专线总数", str(data.circuit_count), "#1F4E79"),
        kpi_card("最长中断", f"{data.max_duration_hours:.1f}h", status_orange if data.max_duration_hours > 2 else status_green),
        kpi_card("即将到期", f"{len(data.urgent_items)}项", urgent_color),
    ]

    kpi_grid = Table([kpi_row1, kpi_row2], colWidths=[49*mm, 49*mm, 49*mm])
    kpi_grid.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(kpi_grid)

    elements.append(Spacer(1, 6*mm))
    elements.append(sep_table)
    elements.append(Spacer(1, 4*mm))

    # 一句话结论
    conclusion_parts = []
    if data.availability_pct is None or data.availability_pct >= 99:
        conclusion_parts.append("网络运行稳定")
    else:
        conclusion_parts.append("网络可用性需要关注")
    if data.incident_count == 0:
        conclusion_parts.append("无故障发生")
    if data.urgent_items:
        conclusion_parts.append(f"有{len(data.urgent_items)}项到期事项需处理")
    conclusion = "，".join(conclusion_parts) + "。"
    elements.append(Paragraph("<b>结论：</b> " + conclusion, ParagraphStyle(
        'Conclusion', fontName=sty['body'].fontName,
        fontSize=13, leading=20,
        textColor=colors.HexColor('#333333')
    )))
    elements.append(Spacer(1, 6*mm))
    elements.append(sep_table)
    elements.append(Spacer(1, 4*mm))

    # 本月亮点
    highlights = []
    if data.availability_pct is not None and data.availability_pct >= 99:
        highlights.append(("✔", f"本月网络可用性 {data.availability_pct:.1f}%，达到99%目标", "#67C23A"))
    if data.incident_count == 0:
        highlights.append(("✔", "本月零故障，网络运行连续稳定", "#67C23A"))
    if not data.urgent_items:
        highlights.append(("✔", "本月无紧急到期事项", "#67C23A"))

    if highlights:
        elements.append(Paragraph("本月亮点", sty['section']))
        elements.append(Spacer(1, 2*mm))
        for icon, text, color in highlights:
            elements.append(Paragraph(f"{icon} {text}", ParagraphStyle(
                'Highlight', fontName=sty['body'].fontName,
                fontSize=12, leading=20,
                textColor=colors.HexColor(color)
            )))
            elements.append(Spacer(1, 1*mm))

    elements.append(PageBreak())
    elements.append(Paragraph("本月运营概况", sty['section']))
    elements.append(Spacer(1, 4*mm))

    # 左侧：网络可用性
    avail_data = [[Paragraph("网络可用性", ParagraphStyle(
        'SectionLabel', fontName=sty['section'].fontName, fontSize=18, leading=24,
        textColor=colors.HexColor('#1F4E79')
    ))]]
    avail_text_big = "暂无数据" if data.availability_pct is None else f"{data.availability_pct:.1f}%"
    avail_c = "#E6A23C" if data.availability_pct is None else ("#67C23A" if data.availability_pct >= 99 else "#E6A23C")
    avail_data.append([Paragraph(avail_text_big, ParagraphStyle(
        'BigAvail', fontName=sty['big_number'].fontName,
        fontSize=64, leading=72, alignment=0,
        textColor=colors.HexColor(avail_c)
    ))])
    avail_detail = "基于巡检记录统计" if data.availability_pct is not None else "请配置巡检任务获取数据"
    avail_data.append([Paragraph(avail_detail, ParagraphStyle(
        'AvailNote', fontName=sty['body'].fontName, fontSize=12, leading=16,
        textColor=colors.HexColor('#999999')
    ))])

    avail_table = Table(avail_data, colWidths=[74*mm])
    avail_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))

    # 右侧：专线运行状态
    right_data = [[Paragraph("专线运行状态", ParagraphStyle(
        'SectionLabelR', fontName=sty['section'].fontName, fontSize=12, leading=16,
        textColor=colors.HexColor('#1F4E79')
    ))]]
    right_data.append([Paragraph(
        f"运行正常：{data.circuit_count} 条<br/>"
        f"发生故障：{data.incident_count} 条<br/>"
        f"专线总费用：¥{data.circuit_cost_total:,}",
        ParagraphStyle('StatusText', fontName=sty['body'].fontName, fontSize=10, leading=18)
    )])

    right_table = Table(right_data, colWidths=[75*mm])
    right_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))

    overview_layout = Table([[avail_table, right_table]], colWidths=[74*mm, 74*mm])
    overview_layout.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(overview_layout)

    elements.append(PageBreak())

    # ===== 第四页：下月行动项 =====
    elements.append(Paragraph("下月重点关注事项", sty['section']))
    elements.append(Spacer(1, 4*mm))

    # 第一节：必须处理
    if data.urgent_items:
        urgent_bg_data = [[Paragraph(
            "🔴 必须处理（30天内到期）",
            ParagraphStyle('UrgentTitle', fontName=sty['item_urgent'].fontName,
                           fontSize=11, leading=16, textColor=colors.HexColor('#F56C6C'))
        )]]
        for item in data.urgent_items:
            text = f"● [{item['type']}] {item['name']} {item['expire_date']} 到期，还有 {item['days_left']} 天"
            urgent_bg_data.append([Paragraph(text, sty['item_urgent'])])
            if item['type'] == '专线合同':
                urgent_bg_data.append([Paragraph(
                    "  建议：到期前7天完成续签",
                    ParagraphStyle('Sug', fontName=sty['body'].fontName,
                                   fontSize=9, leading=13, leftIndent=10*mm,
                                   textColor=colors.HexColor('#909399'))
                )])
            elif item['type'] == '设备保修':
                urgent_bg_data.append([Paragraph(
                    "  建议：确认是否续保，或列入更换计划",
                    ParagraphStyle('Sug', fontName=sty['body'].fontName,
                                   fontSize=9, leading=13, leftIndent=10*mm,
                                   textColor=colors.HexColor('#909399'))
                )])
        urgent_box = Table(urgent_bg_data, colWidths=[150*mm])
        urgent_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF2F0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F56C6C')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(urgent_box)
    else:
        elements.append(Paragraph("本月无紧急到期事项",
            ParagraphStyle('NoUrgent', fontName=sty['body'].fontName,
                           fontSize=10, leading=16, leftIndent=8*mm,
                           textColor=colors.HexColor('#67C23A'))))

    elements.append(Spacer(1, 8*mm))

    # 第二节：建议关注
    if data.warning_items:
        warn_bg_data = [[Paragraph(
            "🟡 建议关注（31-60天内到期）",
            ParagraphStyle('WarnTitle', fontName=sty['item_warning'].fontName,
                           fontSize=11, leading=16, textColor=colors.HexColor('#E6A23C'))
        )]]
        for item in data.warning_items:
            text = f"◇ [{item['type']}] {item['name']} {item['expire_date']} 到期，还有 {item['days_left']} 天"
            warn_bg_data.append([Paragraph(text, sty['item_warning'])])
        warn_box = Table(warn_bg_data, colWidths=[150*mm])
        warn_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFDF0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E6A23C')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(warn_box)
    else:
        elements.append(Paragraph("暂无需关注事项",
            ParagraphStyle('NoWarn', fontName=sty['body'].fontName,
                           fontSize=10, leading=16, leftIndent=8*mm,
                           textColor=colors.HexColor('#909399'))))

    elements.append(PageBreak())

    # ===== 第五页：费用分析 =====
    elements.append(Paragraph("专线费用分析", sty['section']))
    elements.append(Spacer(1, 4*mm))

    # 费用概览
    if data.circuit_cost_total > 0:
        elements.append(Paragraph("本月费用概览", ParagraphStyle(
            'CostSub', fontName=sty['body'].fontName, fontSize=11, leading=16,
            textColor=colors.HexColor('#1F4E79')
        )))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(
            f"¥{data.circuit_cost_total:,}",
            ParagraphStyle('BigCost', fontName=sty['title'].fontName,
                           fontSize=24, leading=30, textColor=colors.HexColor('#1F4E79'))
        ))
        elements.append(Spacer(1, 6*mm))

        # 费用构成-水平条形图（按要求替换为色块条形图）
        from reportlab.lib.colors import HexColor

        elements.append(Paragraph("费用构成", ParagraphStyle(
            'CostSub2', fontName=sty['body'].fontName, fontSize=11, leading=16,
            textColor=colors.HexColor('#1F4E79')
        )))
        elements.append(Spacer(1, 2*mm))

        if data.cost_by_type and data.circuit_cost_total > 0:
            # 类型 → 颜色/中文标签映射，和管理看板统一
            TYPE_COLORS = {
                'internet':  '#378ADD',  # 互联网专线：蓝色
                'mpls':      '#1D9E75',  # MPLS：绿色
                'sdwan':     '#EF9F27',  # SD-WAN：橙色
                'fiber':     '#9B59B6',  # 裸光纤：紫色
                'cloud':     '#36CFC9',  # 云专线：青色
                'other':     '#909399',  # 其他：灰色
            }

            TYPE_LABELS = {
                'internet': '互联网专线',
                'mpls':     'MPLS',
                'sdwan':    'SD-WAN',
                'fiber':    '裸光纤',
                'cloud':    '云专线',
                'other':    '其他',
            }

            label_width = 55    # 左侧标签宽度
            bar_area_width = 150*mm - label_width - 80  # 条形图区域宽度
            bar_height = 14
            row_height = 22
            total = data.circuit_cost_total

            for item in data.cost_by_type:
                type_key = item.get('type', 'other')
                amount = item.get('cost', 0)
                if amount == 0:
                    continue

                pct = amount / total * 100
                bar_width = bar_area_width * (amount / total)
                color = TYPE_COLORS.get(type_key, '#909399')
                label = TYPE_LABELS.get(type_key, type_key)

                # 用Drawing绘制水平条形，添加到elements需要通过Table包装
                bar_d = Drawing(bar_width, bar_height)
                bar_d.add(Rect(0, 0, bar_width, bar_height,
                              fillColor=HexColor(color), strokeColor=None))
                row_data = [[label, bar_d, f"¥{amount:,}  ({pct:.1f}%)"]]
                t = Table(row_data, colWidths=[label_width, bar_area_width, 70])
                t.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (0, 0), 0),
                    ('RIGHTPADDING', (1, 0), (1, 0), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('FONTSIZE', (0, 0), (0, 0), 10),
                    ('TEXTCOLOR', (0, 0), (0, 0), HexColor('#666666')),
                    ('FONTSIZE', (2, 0), (2, 0), 10),
                    ('TEXTCOLOR', (2, 0), (2, 0), HexColor('#333333')),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 2*mm))

        elements.append(Spacer(1, 8*mm))

        # 近6个月费用趋势（折线图）
        elements.append(Paragraph("近6个月费用趋势", ParagraphStyle(
            'CostSub3', fontName=sty['body'].fontName, fontSize=11, leading=16,
            textColor=colors.HexColor('#1F4E79')
        )))
        elements.append(Spacer(1, 2*mm))

        # 使用原生 Canvas 坐标绘制折线图（Drawing 在platypus中定位不方便）
        from reportlab.lib.colors import HexColor

        if not data.cost_history or len(data.cost_history) < 2:
            elements.append(Paragraph("暂无费用历史数据", ParagraphStyle(
                'NoData', fontName=sty['body'].fontName,
                fontSize=10, leading=16, leftIndent=8*mm,
                textColor=colors.HexColor('#909399')
            )))
        else:
            amounts = [h['cost'] for h in data.cost_history]
            # 判断数据是否全部相同
            if len(set(amounts)) == 1:
                # 全相同：不画折线图，改为文字说明
                elements.append(Paragraph(
                    f"近6个月费用稳定，每月 ¥{amounts[0]:,}",
                    ParagraphStyle('CostStable', fontName=sty['body'].fontName,
                                  fontSize=11, leading=16, textColor=HexColor('#333333'))
                ))
                elements.append(Paragraph(
                    "※ 趋势基于当前所有专线静态月租估算，仅供参考",
                    ParagraphStyle('CostNote', fontName=sty['body'].fontName,
                                  fontSize=9, leading=14, textColor=HexColor('#909399'))
                ))
            else:
                # 有变化：绘制折线图
                from reportlab.graphics.shapes import Drawing, Line, Circle

                width = 140*mm
                height = 100*mm
                padding_x = 8*mm
                padding_y = 10*mm
                d = Drawing(width + padding_x*2, height + padding_y*2 + 20)

                max_amount = max(amounts)
                min_amount = min(amounts)
                amount_range = max_amount - min_amount or 1

                plot_width = width
                plot_height = height
                step_x = plot_width / (len(data.cost_history) - 1)

                # 网格线（横向）
                for i in range(0, 6):
                    yy = padding_y + height * i / 5
                    d.add(Rect(padding_x, yy, plot_width, 0, fill=0, strokeColor=HexColor('#E0E0E0')))

                # X轴和Y轴
                d.add(Line(padding_x, padding_y, padding_x + plot_width, padding_y,
                          strokeWidth=1, strokeColor=HexColor('#999999')))
                d.add(Line(padding_x, padding_y, padding_x, padding_y + plot_height,
                          strokeWidth=1, strokeColor=HexColor('#999999')))

                # 计算每个点坐标
                points = []
                for i, item in enumerate(data.cost_history):
                    px = padding_x + (i / (len(data.cost_history) - 1)) * plot_width
                    # Y坐标：数据范围映射到图表高度，留10%上下边距
                    py = padding_y + (item['cost'] - min_amount) / amount_range * (plot_height * 0.8) + plot_height * 0.1
                    points.append((px, py, item))

                # 绘制折线
                d.setStrokeColor(HexColor('#2E75B6'))
                d.setLineWidth(1.5)
                path = d.beginPath()
                path.moveTo(points[0][0], points[0][1])
                for px, py, _ in points[1:]:
                    path.lineTo(px, py)
                d.drawPath(path, stroke=1, fill=0)

                # 绘制数据点和标注（修复标注位置）
                for px, py, item in points:
                    # 数据点圆点
                    d.setFillColor(HexColor('#2E75B6'))
                    d.circle(px, py, 3, fill=1, stroke=0)
                    # 金额标注（数据点正上方8px）
                    amount = item['cost']
                    if amount >= 10000:
                        label = f"¥{amount/10000:.1f}万"
                    else:
                        label = f"¥{amount:,}"
                    d.add(String(px, py + 8, label,
                               fontSize=8, fillColor=HexColor('#333333'),
                               fontName=sty['body'].fontName))
                    # 月份标签（图表底部）
                    d.add(String(px, padding_y - 14, item['month'][-2:],
                               fontSize=9, fillColor=HexColor('#909399'),
                               fontName=sty['body'].fontName))


    else:
        elements.append(Paragraph(
            "专线费用数据暂未录入，请在专线管理中补充月租费用信息",
            ParagraphStyle('NoCost', fontName=sty['body'].fontName,
                           fontSize=10, leading=16, leftIndent=8*mm,
                           textColor=colors.HexColor('#909399'))
        ))

    elements.append(PageBreak())

    # ===== 第六页：故障记录 =====
    elements.append(Paragraph("本月故障记录", sty['section']))
    elements.append(Spacer(1, 4*mm))

    # 顶部统计
    if data.incidents:
        stat_style = ParagraphStyle('StatLabel', fontName=sty['body'].fontName,
                                    fontSize=9, leading=12, alignment=1,
                                    textColor=colors.HexColor('#666666'))
        stat_val_style = ParagraphStyle('StatVal', fontName=sty['title'].fontName,
                                        fontSize=16, leading=22, alignment=1,
                                        textColor=colors.HexColor('#1F4E79'))
        stat_data = [[
            [Paragraph("故障次数", stat_style), Paragraph(str(data.incident_count), stat_val_style)],
            [Paragraph("平均恢复", stat_style), Paragraph(f"{data.avg_recovery_hours:.1f}h", stat_val_style)],
            [Paragraph("最长中断", stat_style), Paragraph(f"{data.max_duration_hours:.1f}h", stat_val_style)],
        ]]
        stat_table = Table(stat_data, colWidths=[50*mm, 50*mm, 50*mm])
        stat_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F7FA')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(stat_table)
        elements.append(Spacer(1, 6*mm))

        # 故障明细表格
        detail_header = ['故障标题', '严重程度', '发生时间', '时长(h)', '状态']
        detail_rows = [detail_header]
        sev_map = {'high': '严重', 'medium': '重要', 'low': '轻微'}
        for inc in data.incidents:
            sev_label = sev_map.get(inc['severity'], inc['severity'])
            detail_rows.append([
                inc['title'],
                sev_label,
                inc['started_at'],
                inc['duration'],
                inc['status'],
            ])

        detail_table = Table(detail_rows, colWidths=[60*mm, 20*mm, 30*mm, 18*mm, 18*mm])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F7FA')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('FONTNAME', (0, 0), (-1, -1), sty['body'].fontName),
        ]))
        elements.append(detail_table)

        # 分析文字
        elements.append(Spacer(1, 6*mm))
        top_circuit = data.incidents[0]['title'] if data.incidents and data.incidents[0]['title'] != "-" else ""
        analysis = f"本月共发生故障{data.incident_count}次"
        if top_circuit:
            analysis += f"，主要集中在「{top_circuit}」"
        analysis += "。平均恢复时长{:.1f}小时。建议持续关注网络运行状态。".format(data.avg_recovery_hours)
        elements.append(Paragraph(analysis, ParagraphStyle(
            'Analysis', fontName=sty['body'].fontName, fontSize=10, leading=16,
            textColor=colors.HexColor('#666666')
        )))
    else:
        elements.append(Paragraph("本月未发生专线故障，网络运行稳定。",
            ParagraphStyle('NoIncident', fontName=sty['body'].fontName,
                           fontSize=10, leading=16, leftIndent=8*mm,
                           textColor=colors.HexColor('#67C23A'))))

    # 页脚
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph("本报告由基石 IT 资源管理系统自动生成", sty['footer']))

    doc.build(elements, onFirstPage=lambda c, d: None, onLaterPages=hf)

    return output_path


def get_report_filename(data: MonthlyReportData) -> str:
    """生成报告文件名"""
    short = data.company_short_name or "基石"
    return f"基石运营月报_{short}_{data.year}年{data.month:02d}月.pdf"