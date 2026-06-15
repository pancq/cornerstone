"""
配置变更 AI 解读服务
分析配置备份的 diff 内容，用自然语言解释变更
"""
import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Device
from ..models.backup_analysis import BackupAnalysis
from .ai_client import call_ai, get_ai_config

logger = logging.getLogger(__name__)

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


async def analyze_config_change(
    diff_text: str,
    device: Device,
    db: AsyncSession,
) -> dict:
    """
    分析配置变更 diff，返回 AI 解读结果
    失败时返回 None
    """
    ai_config = await get_ai_config(db)
    if not ai_config or not ai_config.is_configured():
        return None

    # 截取过长 diff
    if len(diff_text) > 3000:
        diff_text = diff_text[:3000] + "\n...(已截取)"
        logger.warning(f"Diff for {device.name} truncated to 3000 chars")

    prompt = (
        f"设备名称：{device.name}\n"
        f"设备类型：{device.type}\n"
        f"设备型号：{device.model}\n\n"
        f"变更内容（diff）：\n```\n{diff_text}\n```\n"
    )

    try:
        raw = await call_ai(prompt, BACKUP_ANALYSIS_PROMPT, ai_config, max_tokens=1500, timeout=15)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except Exception as e:
        logger.error(f"AI backup analysis failed for {device.name}: {e}")
        return None


async def save_change_analysis(
    backup_id: int,
    analysis: dict,
    model_used: str,
    db: AsyncSession,
):
    """将分析结果保存到 backup_analyses 表"""
    existing = await db.execute(
        select(BackupAnalysis).where(BackupAnalysis.backup_id == backup_id)
    )
    if existing.scalar_one_or_none():
        return  # 已存在，不重复写入

    record = BackupAnalysis(
        backup_id=backup_id,
        summary=analysis.get("summary", ""),
        changes_json=json.dumps(analysis.get("changes", []), ensure_ascii=False),
        risk_level=analysis.get("risk_level", "low"),
        risk_detail=analysis.get("risk_detail", ""),
        total_added=analysis.get("total_added", 0),
        total_removed=analysis.get("total_removed", 0),
        model_used=model_used,
    )
    db.add(record)
    await db.commit()