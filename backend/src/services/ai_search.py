"""
AI 自然语言查询核心服务
将用户的自然语言问题转换为结构化查询，执行数据库查询，并用 AI 格式化回答
"""
import json
import ipaddress
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Site, Circuit, Device, IPAddress, Prefix, Backup, InspectionDeviceResult, InspectionResult
from .ai_client import call_ai, get_ai_config

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 系统 Prompt：告诉 AI 如何解析用户问题
# ──────────────────────────────────────────────
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


async def parse_user_query(question: str) -> dict:
    """
    调用大模型解析用户问题为结构化查询意图
    失败时返回降级查询（full text search fallback）
    """
    prompt = f"请解析以下查询：{question}"

    ai_config = None  # 先尝试从全局获取，如果没有配置则返回降级
    from ..database import async_session
    from ..models.setting import Setting
    from sqlalchemy import select

    try:
        async with async_session() as db:
            ai_config = await get_ai_config(db)
    except Exception:
        pass

    if ai_config and ai_config.is_configured():
        try:
            raw = await call_ai(prompt, SYSTEM_PROMPT, ai_config, max_tokens=1000, timeout=10)
            # 提取 JSON
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            intent = json.loads(raw)
            return intent
        except Exception as e:
            logger.warning(f"AI parse failed, fallback to keyword search: {e}")

    # 降级：关键字匹配
    return _fallback_parse(question)


def _fallback_parse(question: str) -> dict:
    """降级解析：通过关键字匹配确定查询类型"""
    q = question.lower()

    if any(k in q for k in ["站点", "办公室", "site"]):
        data_type = "sites"
    elif any(k in q for k in ["专线", "电路", "circuit", "带宽"]):
        data_type = "circuits"
    elif any(k in q for k in ["设备", "交换机", "路由器", "防火墙", "device", "保修"]):
        data_type = "devices"
    elif any(k in q for k in ["ip", "地址", "ip地址"]):
        data_type = "ip_addresses"
    elif any(k in q for k in ["子网", "网段", "prefix", "可用"]):
        data_type = "prefixes"
    elif any(k in q for k in ["备份", "backup"]):
        data_type = "backups"
    elif any(k in q for k in ["巡检", "离线", "在线"]):
        data_type = "inspection_results"
    else:
        data_type = "devices"

    answer_format = "summary" if any(k in q for k in ["多少", "几个", "统计"]) else "list"

    return {
        "intent": "query",
        "entities": {
            "type": data_type,
            "filters": {},
            "time_range": {},
            "sort": {},
            "limit": 20,
        },
        "answer_format": answer_format,
        "original_question": question,
    }


# ──────────────────────────────────────────────
# 执行查询
# ──────────────────────────────────────────────
async def execute_query(intent: dict, db: AsyncSession) -> list:
    """根据解析出的查询意图执行数据库查询"""
    entities = intent.get("entities", {})
    data_type = entities.get("type", "devices")
    filters = entities.get("filters", {})
    time_range = entities.get("time_range", {})
    sort = entities.get("sort", {})
    limit = entities.get("limit", 20)

    if data_type == "sites":
        return await _query_sites(db, filters)
    elif data_type == "circuits":
        return await _query_circuits(db, filters, time_range, sort, limit)
    elif data_type == "devices":
        return await _query_devices(db, filters, time_range, sort, limit)
    elif data_type == "ip_addresses":
        return await _query_ip_addresses(db, filters, limit)
    elif data_type == "prefixes":
        return await _query_prefixes(db, filters, limit)
    elif data_type == "backups":
        return await _query_backups(db, filters, time_range, sort, limit)
    elif data_type == "inspection_results":
        return await _query_inspection(db, filters, time_range, limit)
    return []


async def _query_sites(db: AsyncSession, filters: dict) -> list:
    stmt = select(Site)
    if "name" in filters:
        stmt = stmt.where(Site.name.contains(filters["name"]))
    if "status" in filters:
        stmt = stmt.where(Site.status == filters["status"])
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {"id": s.id, "name": s.name, "city": s.city, "location": s.location,
         "contact": s.contact, "status": s.status, "alert_count": s.alert_count}
        for s in rows
    ]


async def _query_circuits(db: AsyncSession, filters: dict, time_range: dict, sort: dict, limit: int) -> list:
    stmt = select(Circuit)
    if "status" in filters:
        stmt = stmt.where(Circuit.status == filters["status"])

    # 处理时间范围（如合同即将到期）
    if time_range.get("field") == "contract_end":
        if time_range.get("end") == "now" or "soon" in str(time_range.get("start", "")):
            soon = datetime.now(timezone.utc) + timedelta(days=30)
            stmt = stmt.where(Circuit.contract_end <= soon)
            stmt = stmt.where(Circuit.contract_end >= datetime.now(timezone.utc))
        elif "expired" in str(time_range.get("start", "")):
            stmt = stmt.where(Circuit.contract_end < datetime.now(timezone.utc))

    if sort and sort.get("field"):
        col = getattr(Circuit, sort["field"], None)
        if col:
            stmt = stmt.order_by(col.desc() if sort.get("order") == "desc" else col.asc())

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {"id": c.id, "name": c.name, "provider": c.provider, "type": c.type,
         "bandwidth": c.bandwidth, "status": c.status,
         "contract_end": c.contract_end.isoformat() if c.contract_end else None,
         "monthly_cost": c.monthly_cost}
        for c in rows
    ]


async def _query_devices(db: AsyncSession, filters: dict, time_range: dict, sort: dict, limit: int) -> list:
    stmt = select(Device)
    if "name" in filters:
        stmt = stmt.where(Device.name.contains(filters["name"]))
    if "type" in filters:
        stmt = stmt.where(Device.type.contains(filters["type"]))
    if "status" in filters:
        stmt = stmt.where(Device.status == filters["status"])

    # 保修到期查询
    if time_range.get("field") == "warranty_end":
        if "soon" in str(time_range):
            soon = datetime.now(timezone.utc) + timedelta(days=30)
            stmt = stmt.where(Device.warranty_end <= soon)
        elif "expired" in str(time_range):
            stmt = stmt.where(Device.warranty_end < datetime.now(timezone.utc))

    if sort and sort.get("field"):
        col = getattr(Device, sort["field"], None)
        if col:
            stmt = stmt.order_by(col.desc() if sort.get("order") == "desc" else col.asc())

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {"id": d.id, "name": d.name, "type": d.type, "brand": d.brand,
         "model": d.model, "sn": d.sn, "location": d.location,
         "status": d.status, "owner": d.owner,
         "warranty_end": d.warranty_end.isoformat() if d.warranty_end else None,
         "purchase_date": d.purchase_date.isoformat() if d.purchase_date else None}
        for d in rows
    ]


async def _query_ip_addresses(db: AsyncSession, filters: dict, limit: int) -> list:
    stmt = select(IPAddress)
    if "address" in filters:
        stmt = stmt.where(IPAddress.address.contains(filters["address"]))
    if "status" in filters:
        stmt = stmt.where(IPAddress.status == filters["status"])
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {"id": ip.id, "address": ip.address, "status": ip.status,
         "usage": ip.usage, "owner": ip.owner, "device_id": ip.device_id}
        for ip in rows
    ]


async def _query_prefixes(db: AsyncSession, filters: dict, limit: int) -> list:
    stmt = select(Prefix)
    if "network" in filters:
        stmt = stmt.where(Prefix.network.contains(filters["network"]))
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    # 汇总每个子网的 IP 使用情况
    output = []
    for p in rows:
        total_ips = 0
        try:
            net = ipaddress.ip_network(p.network, strict=False)
            total_ips = net.num_addresses - 2  # 减去网络地址和广播地址
        except Exception:
            pass
        used_count = await db.execute(
            select(func.count(IPAddress.id)).where(IPAddress.prefix_id == p.id)
        )
        used = used_count.scalar() or 0
        output.append({
            "id": p.id, "network": p.network, "vlan": p.vlan,
            "usage": p.usage, "site_id": p.site_id,
            "total_ips": total_ips, "used_ips": used,
            "usage_rate": round(used / total_ips * 100, 1) if total_ips > 0 else 0,
        })
    return output


async def _query_backups(db: AsyncSession, filters: dict, time_range: dict, sort: dict, limit: int) -> list:
    stmt = select(Backup)
    if time_range:
        if "last_7_days" in str(time_range):
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            stmt = stmt.where(Backup.created_at >= cutoff)
        elif time_range.get("start"):
            stmt = stmt.where(Backup.created_at >= time_range["start"])
    if sort and sort.get("field"):
        col = getattr(Backup, sort["field"], None)
        if col:
            stmt = stmt.order_by(col.desc() if sort.get("order") == "desc" else col.asc())
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {"id": b.id, "device_id": b.device_id, "version": b.version,
         "status": b.status, "has_change": b.has_change, "note": b.note}
        for b in rows
    ]


async def _query_inspection(db: AsyncSession, filters: dict, time_range: dict, limit: int) -> list:
    stmt = select(InspectionDeviceResult)

    # 离线查询
    if "offline" in str(filters) or "offline" in str(time_range):
        stmt = stmt.where(InspectionDeviceResult.is_online == False)

    if time_range:
        if "last_7_days" in str(time_range):
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            stmt = stmt.where(InspectionDeviceResult.scanned_at >= cutoff)

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {"id": r.id, "ip_address": r.ip_address, "device_id": r.device_id,
         "is_online": r.is_online, "sys_name": r.sys_name,
         "has_fingerprint_change": r.has_fingerprint_change}
        for r in rows
    ]


# ──────────────────────────────────────────────
# 格式化回答
# ──────────────────────────────────────────────
async def format_answer(intent: dict, raw_data: list, question: str) -> dict:
    """
    将查询结果格式化为自然语言回答
    返回 answer_text + 原始数据 + data_type + suggestions
    """
    data_type = intent.get("entities", {}).get("type", "devices")

    # 尝试用 AI 生成自然语言回答
    ai_config = None
    try:
        from ..database import async_session
        async with async_session() as db:
            ai_config = await get_ai_config(db)
    except Exception:
        pass

    if ai_config and ai_config.is_configured() and raw_data:
        format_prompt = (
            f"用户问题：{question}\n"
            f"查询数据类型：{data_type}\n"
            f"查询结果（JSON）：{json.dumps(raw_data, ensure_ascii=False)}\n\n"
            f"请用简洁的中文回答用户的问题，基于以上数据。"
            f"同时给出 2-3 个进一步追问的建议（JSON数组）。"
            f"返回严格 JSON：{{\"answer_text\": \"...\", \"suggestions\": [...]}}"
        )
        format_system = "你是一位IT运维助手。根据数据和用户问题，生成简洁的自然语言回答和建议追问。只返回JSON。"
        try:
            raw = await call_ai(format_prompt, format_system, ai_config, max_tokens=1000, timeout=10)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            result = json.loads(raw)
            return {
                "answer_text": result.get("answer_text", _generate_fallback_answer(data_type, raw_data, question)),
                "data": raw_data,
                "data_type": data_type,
                "suggestions": result.get("suggestions", []),
            }
        except Exception:
            pass

    # 降级生成
    return {
        "answer_text": _generate_fallback_answer(data_type, raw_data, question),
        "data": raw_data,
        "data_type": data_type,
        "suggestions": [],
    }


def _generate_fallback_answer(data_type: str, raw_data: list, question: str) -> str:
    """降级回答生成"""
    count = len(raw_data)
    name_map = {
        "sites": "站点", "circuits": "专线", "devices": "设备",
        "ip_addresses": "IP地址", "prefixes": "子网", "backups": "备份记录",
        "inspection_results": "巡检结果",
    }
    label = name_map.get(data_type, data_type)

    if count == 0:
        return f"没有找到相关的{label}信息。"
    return f"找到 {count} 条{label}记录。"