"""
AI 智能功能 API 路由
"""
import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..api.dependencies import get_current_active_user
from ..models import User, Device, Backup, Circuit, Prefix, IPAddress
from ..models.alert import AlertRecord
from ..models.inspection import InspectionResult
from ..models.backup_analysis import BackupAnalysis
from ..services.ai_client import get_ai_config, call_ai
from ..services.ai_search import parse_user_query, execute_query, format_answer
from ..services.ai_backup_analyzer import analyze_config_change, save_change_analysis

logger = logging.getLogger(__name__)

router = APIRouter()


# ── 请求/响应模型 ──────────────────────────────

class SearchRequest(BaseModel):
    question: str


class SearchResponse(BaseModel):
    code: int = 0
    data: dict


class ConfigStatusResponse(BaseModel):
    configured: bool
    provider: str = ""
    model: str = ""


class AIConfigRequest(BaseModel):
    provider: str
    model: str
    api_url: str
    api_key: str
    description: str = ""


class AIConfigResponse(BaseModel):
    provider: str
    model: str
    api_url: str
    description: str = ""


class BackupAnalysisResponse(BaseModel):
    status: str  # ready / pending / unavailable / error
    summary: str = ""
    changes: list = []
    risk_level: str = "low"
    risk_detail: str = ""
    total_added: int = 0
    total_removed: int = 0


class AIPredictionRequest(BaseModel):
    input: str = ""


class AIPredictionResponse(BaseModel):
    id: str
    type: str  # root_cause / trend / summary
    title: str
    content: str
    confidence: float
    suggestion: str
    timestamp: str


# ── 接口 ──────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def ai_search(
    req: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    自然语言查询主接口
    输入自然语言问题，返回结构化答案
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    try:
        # Step 1: 解析意图
        intent = await parse_user_query(req.question.strip())

        # Step 2: 执行查询
        raw_data = await execute_query(intent, db)

        # Step 3: 格式化回答
        result = await format_answer(intent, raw_data, req.question)

        return {"code": 0, "data": result}
    except Exception as e:
        logger.error(f"AI search failed: {e}")
        return {
            "code": 1,
            "data": {
                "answer_text": "查询失败，请稍后重试或换个问法。",
                "data": [],
                "data_type": "unknown",
                "suggestions": [],
            },
        }


@router.get("/config/status", response_model=ConfigStatusResponse)
async def ai_config_status(
    db: AsyncSession = Depends(get_db),
):
    """检查 AI 是否已配置可用"""
    config = await get_ai_config(db)
    if config and config.is_configured():
        return ConfigStatusResponse(
            configured=True,
            provider=config.provider,
            model=config.model,
        )
    return ConfigStatusResponse(configured=False)


@router.get("/config", response_model=AIConfigResponse)
async def get_ai_config_detail(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取 AI 配置详情"""
    config = await get_ai_config(db)
    if config:
        return AIConfigResponse(
            provider=config.provider,
            model=config.model,
            api_url=config.api_base,
            description="",
        )
    return AIConfigResponse(provider="", model="", api_url="")


@router.put("/config", response_model=AIConfigResponse)
async def update_ai_config(
    req: AIConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新 AI 配置"""
    from ..models.setting import Setting
    from ..services.ai_client import AI_CONFIG_KEY

    config_data = {
        "provider": req.provider,
        "api_key": req.api_key,
        "api_base": req.api_url,
        "model": req.model,
        "description": req.description,
    }

    result = await db.execute(
        select(Setting).filter(Setting.key == AI_CONFIG_KEY)
    )
    setting = result.scalars().first()

    if setting:
        setting.value = json.dumps(config_data)
    else:
        setting = Setting(key=AI_CONFIG_KEY, value=json.dumps(config_data))
        db.add(setting)

    await db.commit()

    return AIConfigResponse(
        provider=req.provider,
        model=req.model,
        api_url=req.api_url,
        description=req.description,
    )


@router.get("/backups/{backup_id}/analysis", response_model=BackupAnalysisResponse)
async def get_backup_analysis(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取指定备份的 AI 变更分析结果
    - ready：分析完成
    - pending：等待分析（触发异步分析）
    - unavailable：AI 未配置
    - error：分析失败
    """
    # 检查 AI 是否配置
    ai_config = await get_ai_config(db)
    ai_available = ai_config and ai_config.is_configured()

    # 查询已有的分析结果
    result = await db.execute(
        select(BackupAnalysis).where(BackupAnalysis.backup_id == backup_id)
    )
    analysis = result.scalar_one_or_none()

    if analysis:
        changes = json.loads(analysis.changes_json) if analysis.changes_json else []
        return BackupAnalysisResponse(
            status="ready",
            summary=analysis.summary,
            changes=changes,
            risk_level=analysis.risk_level,
            risk_detail=analysis.risk_detail,
            total_added=analysis.total_added,
            total_removed=analysis.total_removed,
        )

    if not ai_available:
        return BackupAnalysisResponse(status="unavailable")

    # 触发异步分析
    try:
        backup_result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = backup_result.scalar_one_or_none()
        if not backup:
            raise HTTPException(status_code=404, detail="备份记录不存在")

        device_result = await db.execute(select(Device).where(Device.id == backup.device_id))
        device = device_result.scalar_one_or_none()

        # 构造 diff 文本
        diff_text = backup.content or ""
        if backup.change_summary:
            diff_text = f"{backup.change_summary}\n\n{diff_text}"

        analysis_result = await analyze_config_change(
            diff_text=diff_text,
            device=device or Device(id=backup.device_id, name=f"Device-{backup.device_id}", type="", model=""),
            db=db,
        )

        if analysis_result:
            model_name = ai_config.model if ai_config else ""
            await save_change_analysis(backup_id, analysis_result, model_name, db)

            changes_list = analysis_result.get("changes", [])
            return BackupAnalysisResponse(
                status="ready",
                summary=analysis_result.get("summary", ""),
                changes=changes_list,
                risk_level=analysis_result.get("risk_level", "low"),
                risk_detail=analysis_result.get("risk_detail", ""),
                total_added=analysis_result.get("total_added", 0),
                total_removed=analysis_result.get("total_removed", 0),
            )

        return BackupAnalysisResponse(status="error", summary="AI 分析失败，请稍后重试")
    except Exception as e:
        logger.error(f"Backup analysis failed for backup {backup_id}: {e}")
        return BackupAnalysisResponse(status="error", summary=f"分析异常: {str(e)}")


# ── AI 预测辅助函数 ─────────────────────────

def _generate_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().timestamp():.0f}-{datetime.now().microsecond}"


def _now_str() -> str:
    try:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now().isoformat()


def _extract_usage_pct(usage_str: str | None) -> int:
    """从 usage 字符串中提取百分比数值，无法解析返回 0"""
    if not usage_str:
        return 0
    try:
        cleaned = usage_str.replace("%", "").strip()
        return int(cleaned)
    except (ValueError, TypeError):
        return 0


async def _gather_system_stats(db: AsyncSession) -> dict:
    """收集系统统计数据，供 AI 分析使用"""
    # 设备统计
    device_result = await db.execute(
        select(Device.status, func.count(Device.id)).group_by(Device.status)
    )
    device_stats = dict(device_result.all())

    # 告警统计
    alert_result = await db.execute(
        select(AlertRecord.severity, func.count(AlertRecord.id))
        .where(AlertRecord.status == "active")
        .group_by(AlertRecord.severity)
    )
    alert_stats = dict(alert_result.all())

    # 专线统计
    circuit_result = await db.execute(
        select(Circuit.status, func.count(Circuit.id)).group_by(Circuit.status)
    )
    circuit_stats = dict(circuit_result.all())

    # 子网统计
    prefix_total = await db.scalar(select(func.count(Prefix.id)))
    prefix_result = await db.execute(select(Prefix.network, Prefix.usage))
    prefixes = prefix_result.all()
    high_usage_prefixes = [
        p for p in prefixes
        if _extract_usage_pct(p.usage) > 80
    ]

    # 保修到期设备（30天内）
    now = datetime.utcnow()
    thirty_days = now + timedelta(days=30)
    warranty_expiring = await db.scalar(
        select(func.count(Device.id))
        .where(Device.warranty_end.isnot(None))
        .where(Device.warranty_end <= thirty_days)
        .where(Device.warranty_end >= now)
    )

    # 合同到期专线（30天内）
    contract_expiring = await db.scalar(
        select(func.count(Circuit.id))
        .where(Circuit.contract_end.isnot(None))
        .where(Circuit.contract_end <= thirty_days)
        .where(Circuit.contract_end >= now)
    )

    # 最近7天备份统计
    seven_days_ago = now - timedelta(days=7)
    backup_total = await db.scalar(
        select(func.count(Backup.id))
        .where(Backup.created_at >= seven_days_ago)
    )
    backup_failed = await db.scalar(
        select(func.count(Backup.id))
        .where(Backup.created_at >= seven_days_ago)
        .where(Backup.status == "failed")
    )

    # IP地址统计
    ip_total = await db.scalar(select(func.count(IPAddress.id)))
    ip_assigned = await db.scalar(
        select(func.count(IPAddress.id)).where(IPAddress.status == "assigned")
    )

    return {
        "device_stats": device_stats,
        "alert_stats": alert_stats,
        "circuit_stats": circuit_stats,
        "prefix_total": prefix_total or 0,
        "high_usage_prefixes": len(high_usage_prefixes),
        "warranty_expiring": warranty_expiring or 0,
        "contract_expiring": contract_expiring or 0,
        "backup_total_7d": backup_total or 0,
        "backup_failed_7d": backup_failed or 0,
        "ip_total": ip_total or 0,
        "ip_assigned": ip_assigned or 0,
    }


def _build_summary_content(stats: dict) -> tuple[str, str, float]:
    """基于统计数据构建摘要内容"""
    device_stats = stats["device_stats"]
    alert_stats = stats["alert_stats"]
    circuit_stats = stats["circuit_stats"]

    device_online = device_stats.get("active", 0) or device_stats.get("online", 0)
    device_offline = device_stats.get("offline", 0)
    device_alert = device_stats.get("alert", 0)

    critical_alerts = alert_stats.get("critical", 0)
    warning_alerts = alert_stats.get("warning", 0)
    info_alerts = alert_stats.get("info", 0)

    circuit_online = circuit_stats.get("正常", 0)
    circuit_offline = circuit_stats.get("断开", 0)

    content_lines = []
    content_lines.append("当前系统运行状态摘要：\n")

    # 紧急问题
    urgent_items = []
    if device_offline and device_offline > 0:
        urgent_items.append(f"- {device_offline} 台设备离线")
    if circuit_offline and circuit_offline > 0:
        urgent_items.append(f"- {circuit_offline} 条专线断开")
    if critical_alerts and critical_alerts > 0:
        urgent_items.append(f"- {critical_alerts} 个严重告警")

    if urgent_items:
        content_lines.append("🔴 **紧急问题**（需立即处理）")
        content_lines.extend(urgent_items)
        content_lines.append("")

    # 待关注问题
    watch_items = []
    if warning_alerts and warning_alerts > 0:
        watch_items.append(f"- {warning_alerts} 个警告告警")
    if stats["warranty_expiring"] > 0:
        watch_items.append(f"- {stats['warranty_expiring']} 台设备保修即将到期")
    if stats["contract_expiring"] > 0:
        watch_items.append(f"- {stats['contract_expiring']} 条专线合同即将到期")
    if stats["high_usage_prefixes"] > 0:
        watch_items.append(f"- {stats['high_usage_prefixes']} 个子网容量超过 80%")
    if stats["backup_failed_7d"] > 0:
        fail_rate = (stats["backup_failed_7d"] / max(stats["backup_total_7d"], 1)) * 100
        watch_items.append(f"- 近7天备份失败 {stats['backup_failed_7d']} 次（失败率 {fail_rate:.0f}%）")

    if watch_items:
        content_lines.append("🟡 **待关注问题**（本周内处理）")
        content_lines.extend(watch_items)
        content_lines.append("")

    # 正常状态
    ok_items = []
    if device_online and device_online > 0:
        ok_items.append(f"- {device_online} 台设备运行正常")
    if circuit_online and circuit_online > 0:
        ok_items.append(f"- {circuit_online} 条专线状态正常")

    ip_usage = (stats["ip_assigned"] / max(stats["ip_total"], 1)) * 100
    ok_items.append(f"- IP地址使用率 {ip_usage:.0f}%（{stats['ip_assigned']}/{stats['ip_total']}）")

    if ok_items:
        content_lines.append("🟢 **正常状态**")
        content_lines.extend(ok_items)
        content_lines.append("")

    # 建议
    suggestions = []
    if device_offline and device_offline > 0:
        suggestions.append("优先处理设备离线问题")
    if critical_alerts and critical_alerts > 0:
        suggestions.append("立即处理严重告警")
    if stats["warranty_expiring"] > 0:
        suggestions.append("提前规划保修到期设备的续保或替换")
    if stats["high_usage_prefixes"] > 0:
        suggestions.append("规划新子网以缓解容量压力")

    suggestion_text = "；".join(suggestions) if suggestions else "系统整体运行正常，请继续保持"

    # 置信度
    has_issues = device_offline > 0 or circuit_offline > 0 or critical_alerts > 0
    confidence = 0.85 if has_issues else 0.95

    return "\n".join(content_lines), suggestion_text, confidence


async def _call_ai_for_prediction(
    db: AsyncSession,
    system_prompt: str,
    user_message: str,
    default_content: str,
    default_suggestion: str,
) -> tuple[str, str]:
    """尝试调用 AI，失败时返回默认值"""
    try:
        ai_config = await get_ai_config(db)
        if ai_config and ai_config.is_configured():
            raw = await call_ai(user_message, system_prompt, ai_config, max_tokens=1500, timeout=15)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            result = json.loads(raw)
            return (
                result.get("content", default_content),
                result.get("suggestion", default_suggestion),
            )
    except Exception as e:
        logger.warning(f"AI call failed, using fallback: {e}")

    return default_content, default_suggestion


# ── AI 预测接口 ──────────────────────────────

@router.post("/summary", response_model=AIPredictionResponse)
async def ai_summary(
    req: AIPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """智能摘要：基于真实数据生成系统运行状态摘要"""
    stats = await _gather_system_stats(db)
    content, suggestion, confidence = _build_summary_content(stats)

    # 尝试用 AI 润色
    system_prompt = "你是一位IT运维专家。根据系统统计数据，生成简洁的中文运维摘要。返回严格JSON：{\"content\": \"摘要内容\", \"suggestion\": \"建议\"}"
    user_msg = json.dumps(stats, ensure_ascii=False, default=str)
    ai_content, ai_suggestion = await _call_ai_for_prediction(
        db, system_prompt, user_msg, content, suggestion
    )

    return AIPredictionResponse(
        id=_generate_id("sm"),
        type="summary",
        title="智能摘要",
        content=ai_content,
        confidence=confidence,
        suggestion=ai_suggestion,
        timestamp=_now_str(),
    )


@router.post("/trend", response_model=AIPredictionResponse)
async def ai_trend(
    req: AIPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """趋势预测：基于数据分析资源使用趋势"""
    stats = await _gather_system_stats(db)

    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)

    # IP使用趋势 - 按子网统计
    prefix_rows = await db.execute(
        select(Prefix.network, Prefix.usage).limit(10)
    )
    prefix_data = [{"network": p.network, "usage": p.usage} for p in prefix_rows.all()]

    # 最近巡检结果
    recent_inspection = await db.execute(
        select(InspectionResult)
        .order_by(InspectionResult.id.desc())
        .limit(5)
    )
    inspections = recent_inspection.scalars().all()

    ip_usage_rate = (stats["ip_assigned"] / max(stats["ip_total"], 1)) * 100
    backup_success_rate = (
        (1 - stats["backup_failed_7d"] / max(stats["backup_total_7d"], 1)) * 100
        if stats["backup_total_7d"] > 0 else 100
    )

    content_lines = []
    content_lines.append("基于历史数据分析，趋势预测如下：\n")

    content_lines.append("**IP 资源趋势**")
    content_lines.append(f"- 当前 IP 使用率：{ip_usage_rate:.0f}%")
    if ip_usage_rate > 80:
        content_lines.append("- ⚠️ 使用率较高，建议规划新子网")
    else:
        content_lines.append("- IP 资源充足")
    content_lines.append("")

    content_lines.append("**备份趋势**")
    content_lines.append(f"- 近7天备份成功率：{backup_success_rate:.0f}%")
    if stats["backup_failed_7d"] > 0:
        content_lines.append("- ⚠️ 存在备份失败记录，建议检查备份任务配置")
    content_lines.append("")

    if stats["warranty_expiring"] > 0:
        content_lines.append("**设备保修趋势**")
        content_lines.append(f"- {stats['warranty_expiring']} 台设备保修将在30天内到期")
        content_lines.append("- 建议提前安排续保或设备替换计划")
        content_lines.append("")

    if stats["contract_expiring"] > 0:
        content_lines.append("**专线合同趋势**")
        content_lines.append(f"- {stats['contract_expiring']} 条专线合同将在30天内到期")
        content_lines.append("- 建议提前与运营商确认续约")
        content_lines.append("")

    # 巡检趋势
    if inspections:
        online_rates = []
        for ins in inspections:
            total = (ins.online_count or 0) + (ins.offline_count or 0)
            rate = (ins.online_count or 0) / max(total, 1) * 100
            online_rates.append(rate)
        if online_rates:
            avg_rate = sum(online_rates) / len(online_rates)
            content_lines.append("**设备在线率趋势**")
            content_lines.append(f"- 最近 {len(inspections)} 次巡检平均在线率：{avg_rate:.0f}%")
            if len(online_rates) >= 2 and online_rates[-1] < online_rates[0]:
                content_lines.append("- ⚠️ 在线率呈下降趋势，建议关注")
            content_lines.append("")

    # 高使用率子网
    if stats["high_usage_prefixes"] > 0:
        content_lines.append(f"⚠️ **{stats['high_usage_prefixes']}** 个子网使用率超过 80%")
        for p in prefix_data:
            if p["usage"] and any(
                p["usage"].replace("%", "").startswith(str(i))
                for i in range(80, 101)
            ):
                content_lines.append(f"  - {p['network']}（使用率 {p['usage']}）")

    suggestion = "建议持续监控资源使用趋势，提前规划容量"
    if ip_usage_rate > 80:
        suggestion = "建议在30天内完成新子网规划，避免IP耗尽影响业务"
    elif stats["warranty_expiring"] > 0:
        suggestion = "优先处理保修到期设备的续保计划"

    content = "\n".join(content_lines)

    confidence = 0.90 if stats["backup_total_7d"] > 5 else 0.75

    return AIPredictionResponse(
        id=_generate_id("tr"),
        type="trend",
        title="趋势预测结果",
        content=content,
        confidence=confidence,
        suggestion=suggestion,
        timestamp=_now_str(),
    )


@router.post("/root-cause", response_model=AIPredictionResponse)
async def ai_root_cause(
    req: AIPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """根因分析：基于告警和设备状态分析故障根因"""
    # 获取离线设备
    offline_devices = await db.execute(
        select(Device).where(Device.status == "offline").limit(5)
    )
    offline_devices_list = offline_devices.scalars().all()

    # 获取断开专线
    offline_circuits = await db.execute(
        select(Circuit).where(Circuit.status == "断开").limit(5)
    )
    offline_circuits_list = offline_circuits.scalars().all()

    # 获取活跃告警
    active_alerts = await db.execute(
        select(AlertRecord)
        .where(AlertRecord.status == "active")
        .order_by(AlertRecord.severity)
        .limit(10)
    )
    active_alerts_list = active_alerts.scalars().all()

    # 构建分析
    content_lines = []
    content_lines.append("根据系统数据分析，当前主要问题及可能原因如下：\n")

    if offline_devices_list:
        content_lines.append(f"**设备离线分析**（{len(offline_devices_list)} 台）")
        for d in offline_devices_list:
            content_lines.append(f"- {d.name}（{d.type or '未知类型'}）")
        content_lines.append("\n可能原因：")
        content_lines.append("1. **网络连接问题** — 检查网线/光纤连接状态及交换机端口")
        content_lines.append("2. **电源故障** — 检查设备供电及 UPS 状态")
        content_lines.append("3. **设备硬件故障** — 检查设备日志，联系供应商检测")
        content_lines.append("")

    if offline_circuits_list:
        content_lines.append(f"**专线断开分析**（{len(offline_circuits_list)} 条）")
        for c in offline_circuits_list:
            content_lines.append(f"- {c.name}（{c.provider or '未知运营商'}）")
        content_lines.append("\n可能原因：")
        content_lines.append("1. **运营商侧故障** — 联系运营商确认线路状态")
        content_lines.append("2. **端口/光模块故障** — 检查两端设备端口状态")
        content_lines.append("3. **配置变更** — 检查近期配置变更记录")
        content_lines.append("")

    if active_alerts_list:
        content_lines.append(f"**活跃告警分析**（{len(active_alerts_list)} 条）")
        severity_count = {}
        for a in active_alerts_list:
            severity_count[a.severity] = severity_count.get(a.severity, 0) + 1
        for sev, count in sorted(severity_count.items()):
            content_lines.append(f"- {sev} 级别告警：{count} 条")
        content_lines.append("")

    if not offline_devices_list and not offline_circuits_list and not active_alerts_list:
        content_lines.append("✅ 当前系统运行正常，未发现明显故障。\n")
        content = "\n".join(content_lines)
        return AIPredictionResponse(
            id=_generate_id("rc"),
            type="root_cause",
            title="根因分析结果",
            content=content,
            confidence=0.98,
            suggestion="系统运行正常，请继续保持",
            timestamp=_now_str(),
        )

    # 生成建议
    suggestion_parts = []
    if offline_devices_list:
        suggestion_parts.append("优先检查离线设备的网络连接和供电状态")
    if offline_circuits_list:
        suggestion_parts.append("联系运营商确认专线状态")
    if active_alerts_list:
        suggestion_parts.append("逐个确认和处理活跃告警")

    suggestion = "；".join(suggestion_parts)

    content = "\n".join(content_lines)
    confidence = 0.85 if (offline_devices_list or offline_circuits_list) else 0.75

    return AIPredictionResponse(
        id=_generate_id("rc"),
        type="root_cause",
        title="根因分析结果",
        content=content,
        confidence=confidence,
        suggestion=suggestion,
        timestamp=_now_str(),
    )