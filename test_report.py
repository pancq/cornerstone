
#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class MonthlyReportData:
    year: int
    month: int
    company_name: str = ""
    company_short_name: str = ""
    it_department: str = "信息技术部"
    it_contact: str = ""
    generated_at: datetime = None

    availability_pct: float = 100.0
    circuit_cost_total: int = 87393
    incident_count: int = 0
    max_duration_hours: float = 0
    circuit_count: int = 0

    urgent_items: List[Dict] = None
    warning_items: List[Dict] = None
    incidents: List[Dict] = None
    cost_by_type: List[Dict] = None
    cost_history: List[Dict] = None


def main():
    # 模拟数据
    data = MonthlyReportData(
        year=2026,
        month=6,
        generated_at=datetime.now(),
        circuit_cost_total=87393,
        availability_pct=99.5,
        cost_by_type=[
            {"type": "internet", "cost": 55000, "pct": 63.0},
            {"type": "mpls", "cost": 32393, "pct": 37.0},
        ],
        cost_history=[
            {"month": "2026-01", "cost": 87393},
            {"month": "2026-02", "cost": 87393},
            {"month": "2026-03", "cost": 87393},
            {"month": "2026-04", "cost": 87393},
            {"month": "2026-05", "cost": 87393},
            {"month": "2026-06", "cost": 87393},
        ],
        urgent_items=[],
        warning_items=[],
        incidents=[],
        circuit_count=1,
    )

    # 临时添加到路径
    backend_dir = Path(__file__).parent / "backend"
    sys.path.insert(0, str(backend_dir))

    try:
        from src.services.report_generator import generate_report_pdf
        output_file = Path(__file__).parent / "test_output.pdf"
        if output_file.exists():
            output_file.unlink()

        print("开始生成PDF...")
        generate_report_pdf(data, str(output_file))

        if output_file.exists() and output_file.stat().st_size > 0:
            print(f"✅ PDF生成成功！文件大小: {output_file.stat().st_size} bytes")
            return 0
        else:
            print("❌ PDF生成失败，文件为空或不存在")
            return 1

    except Exception as e:
        import traceback
        print("❌ 发生异常！")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
