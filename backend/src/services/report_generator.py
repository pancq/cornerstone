"""运营月报 PDF 生成服务"""
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import json

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

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

    # 第一页：本月概况
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
    month_start = datetime(year, month, 1)
    next_month = datetime(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
    now = datetime.now()

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

    # 本月故障统计
    incidents_result = await db.execute(
        select(func.count(CircuitIncident.id))
        .where(and_(
            CircuitIncident.created_at >= month_start,
            CircuitIncident.created_at < next_month
        ))
    )
    incident_count = incidents_result.scalar() or 0

    max_duration_result = await db.execute(
        select(func.coalesce(func.max(CircuitIncident.duration_hours), 0))
        .where(and_(
            CircuitIncident.created_at >= month_start,
            CircuitIncident.created_at < next_month
        ))
    )
    max_duration = float(max_duration_result.scalar() or 0)

    avg_recovery_result = await db.execute(
        select(func.coalesce(func.avg(CircuitIncident.duration_hours), 0))
        .where(and_(
            CircuitIncident.created_at >= month_start,
            CircuitIncident.created_at < next_month,
            CircuitIncident.duration_hours > 0
        ))
    )
    avg_recovery = float(avg_recovery_result.scalar() or 0)

    # 故障明细
    incidents_list_result = await db.execute(
        select(
            CircuitIncident.title,
            CircuitIncident.severity,
            CircuitIncident.started_at,
            CircuitIncident.duration_hours,
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

    # 到期事项
    thirty_days_later = now + timedelta(days=30)
    sixty_days_later = now + timedelta(days=60)

    urgent_circuits_result = await db.execute(
        select(Circuit.name, Circuit.contract_end, Circuit.provider)
        .where(and_(
            Circuit.contract_end != None,
            Circuit.contract_end <= thirty_days_later
        ))
    )
    urgent_items = []
    for c in urgent_circuits_result.all():
        days_left = (c.contract_end.date() - now.date()).days
        if days_left >= 0:
            urgent_items.append({
                "type": "专线合同",
                "name": c.name,
                "expire_date": c.contract_end.strftime("%Y-%m-%d"),
                "days_left": days_left
            })

    urgent_warranties_result = await db.execute(
        select(Device.name, Device.warranty_end, Device.model)
        .where(and_(
            Device.warranty_end != None,
            Device.warranty_end <= thirty_days_later
        ))
    )
    for d in urgent_warranties_result.all():
        days_left = (d.warranty_end.date() - now.date()).days
        if days_left >= 0:
            urgent_items.append({
                "type": "设备保修",
                "name": d.name,
                "expire_date": d.warranty_end.strftime("%Y-%m-%d"),
                "days_left": days_left
            })

    warning_items = []
    warning_circuits_result = await db.execute(
        select(Circuit.name, Circuit.contract_end, Circuit.provider)
        .where(and_(
            Circuit.contract_end != None,
            Circuit.contract_end <= sixty_days_later,
            Circuit.contract_end > thirty_days_later
        ))
    )
    for c in warning_circuits_result.all():
        days_left = (c.contract_end.date() - now.date()).days
        if days_left >= 0:
            warning_items.append({
                "type": "专线合同",
                "name": c.name,
                "expire_date": c.contract_end.strftime("%Y-%m-%d"),
                "days_left": days_left
            })

    warning_warranties_result = await db.execute(
        select(Device.name, Device.warranty_end, Device.model)
        .where(and_(
            Device.warranty_end != None,
            Device.warranty_end <= sixty_days_later,
            Device.warranty_end > thirty_days_later
        ))
    )
    for d in warning_warranties_result.all():
        days_left = (d.warranty_end.date() - now.date()).days
        if days_left >= 0:
            warning_items.append({
                "type": "设备保修",
                "name": d.name,
                "expire_date": d.warranty_end.strftime("%Y-%m-%d"),
                "days_left": days_left
            })

    return MonthlyReportData(
        year=year,
        month=month,
        company_name=company.get("company_name", ""),
        company_short_name=company.get("company_short_name", ""),
        it_department=company.get("it_department_name", "信息技术部"),
        it_contact=company.get("it_contact_name", ""),
        generated_at=now,
        circuit_cost_total=total_cost,
        incident_count=incident_count,
        max_duration_hours=max_duration,
        circuit_count=circuit_count,
        avg_recovery_hours=avg_recovery,
        urgent_items=sorted(urgent_items, key=lambda x: x["days_left"]),
        warning_items=sorted(warning_items, key=lambda x: x["days_left"]),
        incidents=[{
            "title": i.title or "-",
            "severity": i.severity or "low",
            "started_at": i.started_at.strftime("%m-%d %H:%M") if i.started_at else "-",
            "duration": f"{i.duration_hours:.1f}" if i.duration_hours else "-",
            "status": "已恢复" if i.status == "resolved" else "处理中"
        } for i in incidents_list]
    )


def _register_fonts():
    """注册中文字体"""
    import os
    # 尝试多种常见中文字体路径
    font_candidates = [
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
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", path))
                return True
            except Exception:
                continue
    return False


def _get_styles():
    """获取样式集合，尝试注册中文字体"""
    styles = getSampleStyleSheet()
    has_cn = _register_fonts()
    font_name = "ChineseFont" if has_cn else "Helvetica"
    font_name_bold = "ChineseFont" if has_cn else "Helvetica-Bold"

    return {
        "title": ParagraphStyle(
            'ReportTitle', fontName=font_name_bold,
            fontSize=22, leading=28, spaceAfter=6*mm,
            textColor=colors.HexColor('#1a1a2e')
        ),
        "subtitle": ParagraphStyle(
            'ReportSubtitle', fontName=font_name,
            fontSize=12, leading=16, spaceAfter=10*mm,
            textColor=colors.HexColor('#666666')
        ),
        "section": ParagraphStyle(
            'SectionTitle', fontName=font_name_bold,
            fontSize=14, leading=20, spaceBefore=6*mm, spaceAfter=4*mm,
            textColor=colors.HexColor('#1F4E79')
        ),
        "body": ParagraphStyle(
            'Body', fontName=font_name,
            fontSize=10, leading=16, spaceAfter=2*mm
        ),
        "body_center": ParagraphStyle(
            'BodyCenter', fontName=font_name,
            fontSize=10, leading=16, alignment=1
        ),
        "small": ParagraphStyle(
            'Small', fontName=font_name,
            fontSize=9, leading=13
        ),
        "footer": ParagraphStyle(
            'Footer', fontName=font_name,
            fontSize=8, textColor=colors.HexColor('#999999'), alignment=1
        ),
        "big_number": ParagraphStyle(
            'BigNumber', fontName=font_name_bold,
            fontSize=24, leading=30, alignment=1,
            textColor=colors.HexColor('#1F4E79')
        ),
        "big_number_green": ParagraphStyle(
            'BigNumberGreen', fontName=font_name_bold,
            fontSize=24, leading=30, alignment=1,
            textColor=colors.HexColor('#67C23A')
        ),
        "big_number_red": ParagraphStyle(
            'BigNumberRed', fontName=font_name_bold,
            fontSize=24, leading=30, alignment=1,
            textColor=colors.HexColor('#F56C6C')
        ),
        "item_urgent": ParagraphStyle(
            'ItemUrgent', fontName=font_name,
            fontSize=10, leading=16, leftIndent=8*mm,
            textColor=colors.HexColor('#F56C6C')
        ),
        "item_warning": ParagraphStyle(
            'ItemWarning', fontName=font_name,
            fontSize=10, leading=16, leftIndent=8*mm,
            textColor=colors.HexColor('#E6A23C')
        ),
    }


def _make_header_footer(doc, sty: dict, data: MonthlyReportData):
    """添加页眉和页脚"""
    from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
    from reportlab.platypus import PageBreak

    company_short = data.company_short_name or "基石"
    month_label = f"{data.year}年{data.month}月"

    def header_footer(canvas, doc):
        canvas.saveState()
        # 页眉
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor('#999999'))
        canvas.drawString(25*mm, A4[1] - 15*mm, f"基石 · IT基础设施运营月报")
        canvas.drawRightString(A4[0] - 25*mm, A4[1] - 15*mm, month_label)
        canvas.setStrokeColor(colors.HexColor('#E0E0E0'))
        canvas.setLineWidth(0.5)
        canvas.line(25*mm, A4[1] - 18*mm, A4[0] - 25*mm, A4[1] - 18*mm)
        # 页脚
        canvas.setFont("Helvetica", 8)
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
        topMargin=25*mm, bottomMargin=25*mm,
        leftMargin=25*mm, rightMargin=25*mm
    )

    elements = []

    # ===== 第一页：封面 =====
    elements.append(Spacer(1, 60*mm))
    # 深蓝色背景块模拟（用表格实现）
    cover_bg = [['']]
    cover_table = Table(cover_bg, colWidths=[160*mm])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1F4E79')),
        ('TOPPADDING', (0, 0), (-1, -1), 30*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20*mm),
    ]))
    elements.append(cover_table)

    # 封面内容用白色文字
    cover_title_style = ParagraphStyle(
        'CoverTitle', fontName=sty['title'].fontName,
        fontSize=28, leading=36, alignment=1,
        textColor=colors.white
    )
    cover_sub_style = ParagraphStyle(
        'CoverSub', fontName=sty['subtitle'].fontName,
        fontSize=16, leading=22, alignment=1,
        textColor=colors.HexColor('#B0C4DE')
    )

    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("IT基础设施运营月报", cover_title_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(f"{data.year}年{data.month}月", cover_sub_style))
    elements.append(Spacer(1, 15*mm))

    # 底部信息
    info_style = ParagraphStyle(
        'CoverInfo', fontName=sty['body'].fontName,
        fontSize=11, leading=18, alignment=1,
        textColor=colors.HexColor('#333333')
    )
    company_name = data.company_name or "(请设置公司名称)"
    elements.append(Paragraph(company_name, info_style))
    elements.append(Spacer(1, 3*mm))
    import calendar
    last_day = calendar.monthrange(data.year, data.month)[1]
    elements.append(
        Paragraph(
            f"报告周期：{data.year}年{data.month}月1日 至 {data.year}年{data.month}月{last_day}日",
            info_style
        )
    )
    elements.append(Paragraph(f"生成时间：{data.generated_at.strftime('%Y-%m-%d %H:%M')}", info_style))
    elements.append(Spacer(1, 2*mm))
    elements.append(
        Paragraph("生成系统：基石 Cornerstone · IT基础设施资源管理平台",
                   ParagraphStyle('CoverFooter', fontName=sty['body'].fontName,
                                  fontSize=9, leading=14, alignment=1, textColor=colors.HexColor('#999999')))
    )

    elements.append(PageBreak())

    # 页眉页脚（从第二页开始）
    hf = _make_header_footer(doc, sty, data)
    doc.build(elements, onFirstPage=lambda c, d: None, onLaterPages=hf)
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=25*mm, bottomMargin=25*mm,
        leftMargin=25*mm, rightMargin=25*mm
    )
    elements = []

    # ===== 第二页：执行摘要 =====
    elements.append(Paragraph("执行摘要", sty['section']))
    elements.append(Spacer(1, 4*mm))

    # 动态摘要文字
    summary_lines = []
    if data.availability_pct is not None:
        if data.availability_pct >= 99:
            summary_lines.append(f"本月网络整体运行稳定，可用性达{data.availability_pct:.1f}%。")
        else:
            summary_lines.append(f"本月网络可用性为{data.availability_pct:.1f}%，低于目标值99%，需关注。")
    if data.incident_count == 0:
        summary_lines.append("本月未发生专线故障。")
    else:
        summary_lines.append(f"发生故障{data.incident_count}次，平均恢复时长{data.avg_recovery_hours:.1f}小时。")
    if data.circuit_cost_total > 0:
        summary_lines.append(f"本月专线月租总费用为¥{data.circuit_cost_total:,}。")
    if data.urgent_items:
        summary_lines.append(f"下月有{len(data.urgent_items)}项合同/保修即将到期（30天内），请尽快处理。")
    if not summary_lines:
        summary_lines.append("本月暂无运营数据，请确认专线和巡检配置正常。")

    for line in summary_lines:
        elements.append(Paragraph(f"▸ {line}", sty['body']))
        elements.append(Spacer(1, 2*mm))

    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("关键指标速览", sty['section']))

    # 2×3 网格指标
    def metric_cell(label, value, color="#1F4E79"):
        return [
            Paragraph(label, ParagraphStyle('ml', fontName=sty['body'].fontName, fontSize=9, leading=12, alignment=1, textColor=colors.HexColor('#666666'))),
            Paragraph(value, ParagraphStyle('mv', fontName=sty['title'].fontName, fontSize=20, leading=26, alignment=1, textColor=colors.HexColor(color))),
        ]

    status_green = "#67C23A"
    status_orange = "#E6A23C"
    status_red = "#F56C6C"

    # 可用性
    avail_text = "暂无数据" if data.availability_pct is None else f"{data.availability_pct:.1f}%"
    avail_color = status_green if data.availability_pct is None or data.availability_pct >= 99 else status_orange

    # 故障
    incident_color = status_green if data.incident_count == 0 else (status_orange if data.incident_count <= 3 else status_red)

    # 到期
    urgent_color = status_green if not data.urgent_items else (status_orange if len(data.urgent_items) <= 3 else status_red)

    metrics_grid = [
        [metric_cell("网络可用性", avail_text, avail_color),
         metric_cell("专线费用", f"¥{data.circuit_cost_total:,}"),
         metric_cell("故障次数", str(data.incident_count), incident_color)],
        [metric_cell("专线总数", str(data.circuit_count)),
         metric_cell("最长中断", f"{data.max_duration_hours:.1f}h", status_orange if data.max_duration_hours > 2 else status_green),
         metric_cell("即将到期", f"{len(data.urgent_items)}项", urgent_color)],
    ]

    grid_data = []
    for row in metrics_grid:
        grid_row = []
        for cell in row:
            grid_row.extend(cell)
        grid_data.append(grid_row)

    metrics_table = Table(grid_data, colWidths=[50*mm, 50*mm, 50*mm])
    metrics_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(metrics_table)

    elements.append(PageBreak())

    # ===== 第三页：本月概况 =====
    elements.append(Paragraph("本月运营概况", sty['section']))
    elements.append(Spacer(1, 4*mm))

    # 指标表
    overview_data = [
        ['指标', '数值'],
        ['专线总数', f'{data.circuit_count} 条'],
        ['月租总费用', f'¥{data.circuit_cost_total:,}'],
        ['本月故障次数', f'{data.incident_count} 次'],
        ['最长中断时长', f'{data.max_duration_hours:.1f} 小时' if data.max_duration_hours > 0 else '无'],
        ['平均恢复时长', f'{data.avg_recovery_hours:.1f} 小时' if data.avg_recovery_hours > 0 else '-'],
    ]
    overview_table = Table(overview_data, colWidths=[70*mm, 70*mm])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, -1), sty['body'].fontName),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F7FA')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(overview_table)

    elements.append(PageBreak())

    # ===== 第四页：下月行动项 =====
    elements.append(Paragraph("下月重点关注事项", sty['section']))
    elements.append(Spacer(1, 4*mm))

    if data.urgent_items:
        elements.append(Paragraph("🔴 必须处理（30天内到期）", sty['item_urgent']))
        elements.append(Spacer(1, 2*mm))
        for item in data.urgent_items:
            text = f"● [{item['type']}] {item['name']} {item['expire_date']} 到期，还有 {item['days_left']} 天"
            elements.append(Paragraph(text, sty['item_urgent']))
            elements.append(Spacer(1, 1*mm))
    else:
        elements.append(Paragraph("🟢 本月无紧急到期事项", ParagraphStyle(
            'NoUrgent', fontName=sty['body'].fontName,
            fontSize=10, leading=16, leftIndent=8*mm,
            textColor=colors.HexColor('#67C23A')
        )))

    elements.append(Spacer(1, 8*mm))

    if data.warning_items:
        elements.append(Paragraph("🟡 建议关注（31-60天内到期）", sty['item_warning']))
        elements.append(Spacer(1, 2*mm))
        for item in data.warning_items:
            text = f"◇ [{item['type']}] {item['name']} {item['expire_date']} 到期，还有 {item['days_left']} 天"
            elements.append(Paragraph(text, sty['item_warning']))
            elements.append(Spacer(1, 1*mm))
    else:
        elements.append(Paragraph("⚪ 暂无需关注事项", ParagraphStyle(
            'NoWarning', fontName=sty['body'].fontName,
            fontSize=10, leading=16, leftIndent=8*mm,
            textColor=colors.HexColor('#909399')
        )))

    elements.append(PageBreak())

    # ===== 第五页：故障明细 =====
    elements.append(Paragraph("本月故障记录", sty['section']))
    elements.append(Spacer(1, 4*mm))

    if data.incidents:
        detail_header = ['故障标题', '严重程度', '发生时间', '时长(h)', '状态']
        detail_rows = [detail_header]
        for inc in data.incidents:
            sev_label = {'high': '严重', 'medium': '重要', 'low': '轻微'}.get(inc['severity'], inc['severity'])
            detail_rows.append([
                Paragraph(inc['title'], sty['body_center']),
                Paragraph(sev_label, sty['body_center']),
                inc['started_at'],
                inc['duration'],
                Paragraph(inc['status'], sty['body_center']),
            ])

        detail_table = Table(detail_rows, colWidths=[60*mm, 20*mm, 30*mm, 18*mm, 18*mm])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, -1), sty['body'].fontName),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F7FA')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(detail_table)

        # 分析文字
        elements.append(Spacer(1, 6*mm))
        if data.incident_count > 0:
            # 找故障最多的标题
            top_circuit = data.incidents[0]['title'] if data.incidents else ""
            analysis = f"本月共发生故障{data.incident_count}次"
            if top_circuit and top_circuit != "-":
                analysis += f"，主要集中在「{top_circuit}」"
            analysis += "，建议持续关注网络运行状态。"
            elements.append(Paragraph(analysis, sty['body']))
    else:
        elements.append(Paragraph("本月未发生专线故障，网络运行稳定。", sty['body']))

    # 页脚
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph("本报告由基石 IT 资源管理系统自动生成", sty['footer']))

    doc.build(elements, onFirstPage=lambda c, d: None, onLaterPages=hf)

    return output_path


def get_report_filename(data: MonthlyReportData) -> str:
    """生成报告文件名"""
    short = data.company_short_name or "基石"
    return f"基石运营月报_{short}_{data.year}年{data.month:02d}月.pdf"