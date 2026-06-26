"""运营月报 API"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy import delete as sa_delete
from fastapi.responses import FileResponse

from src.database import get_db
from src.models.report import MonthlyReport
from src.models.user import User
from src.api.auth import get_current_active_user
from src.api.dependencies import require_super_admin
from src.services.report_generator import (
    collect_report_data,
    generate_report_pdf,
    get_report_filename,
    REPORT_DIR
)

router = APIRouter(tags=["reports"])


def _require_manager_or_admin(current_user: User):
    """验证用户角色为 viewer 或 super_admin"""
    if current_user.role.name not in ['viewer', 'super_admin']:
        raise HTTPException(status_code=403, detail="需要IT负责人或管理员权限")


@router.get("/monthly/list")
async def list_monthly_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取已生成的月报列表"""
    _require_manager_or_admin(current_user)

    result = await db.execute(
        select(MonthlyReport)
        .order_by(desc(MonthlyReport.year), desc(MonthlyReport.month))
        .limit(12)
    )
    reports = result.scalars().all()

    return [
        {
            "id": r.id,
            "year": r.year,
            "month": r.month,
            "file_size": r.file_size,
            "status": r.status,
            "generated_by": r.generated_by,
            "generated_at": r.generated_at.strftime("%Y-%m-%d %H:%M") if r.generated_at else "",
            "filename": Path(r.file_path).name if r.file_path else "",
        }
        for r in reports
    ]


@router.post("/monthly/generate")
async def generate_monthly_report(
    year: int | None = None,
    month: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """生成指定月份的月报 PDF"""
    _require_manager_or_admin(current_user)

    # 使用北京时间（UTC+8）
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    if not year:
        year = now.year
    if not month:
        month = now.month

    # 收集数据
    data = await collect_report_data(year, month, db)

    # 确保目录存在
    report_dir = REPORT_DIR / str(year)
    report_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    filename = get_report_filename(data)
    output_path = str(report_dir / filename)

    # 生成 PDF
    try:
        generate_report_pdf(data, output_path)
    except Exception as e:
        # 记录失败
        db.add(MonthlyReport(
            year=year, month=month,
            file_path=output_path, file_size=0,
            status="failed", error_message=str(e),
            generated_by=current_user.username
        ))
        await db.commit()
        raise HTTPException(status_code=500, detail=f"月报生成失败: {str(e)}")

    file_size = os.path.getsize(output_path)

    # 保存记录
    # 先删除同月份的旧记录
    await db.execute(
        sa_delete(MonthlyReport).where(
            MonthlyReport.year == year,
            MonthlyReport.month == month
        )
    )
    report_record = MonthlyReport(
        year=year, month=month,
        file_path=output_path, file_size=file_size,
        status="done", generated_by=current_user.username,
        generated_at=now
    )
    db.add(report_record)
    await db.commit()

    return {
        "message": "月报生成成功",
        "filename": filename,
        "file_size": file_size,
    }


@router.get("/monthly/download/{year}/{month}")
async def download_monthly_report(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """下载指定月份的月报 PDF"""
    _require_manager_or_admin(current_user)

    result = await db.execute(
        select(MonthlyReport).where(
            MonthlyReport.year == year,
            MonthlyReport.month == month,
            MonthlyReport.status == "done"
        )
    )
    report = result.scalars().first()

    if not report:
        raise HTTPException(status_code=404, detail="该月份月报未生成，请先生成")

    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="月报文件不存在")

    filename = Path(report.file_path).name
    return FileResponse(
        report.file_path,
        media_type="application/pdf",
        filename=filename
    )


@router.delete("/monthly/{year}/{month}")
async def delete_monthly_report(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除指定月份月报"""
    require_super_admin(current_user, db)

    result = await db.execute(
        select(MonthlyReport).where(
            MonthlyReport.year == year,
            MonthlyReport.month == month
        )
    )
    report = result.scalars().first()

    if not report:
        raise HTTPException(status_code=404, detail="月报记录不存在")

    # 删除文件
    if os.path.exists(report.file_path):
        os.remove(report.file_path)

    await db.delete(report)
    await db.commit()

    return {"message": "月报已删除"}