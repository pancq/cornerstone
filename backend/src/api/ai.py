"""
AI 智能功能 API 路由
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..api.dependencies import get_current_active_user
from ..models import User, Device, Backup
from ..models.backup_analysis import BackupAnalysis
from ..services.ai_client import get_ai_config
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


class BackupAnalysisResponse(BaseModel):
    status: str  # ready / pending / unavailable / error
    summary: str = ""
    changes: list = []
    risk_level: str = "low"
    risk_detail: str = ""
    total_added: int = 0
    total_removed: int = 0


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