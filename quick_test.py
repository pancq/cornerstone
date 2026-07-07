
#!/usr/bin/env python3
"""快速测试生成报告"""
from datetime import datetime, timedelta
from dataclasses import dataclass
import sys
sys.path.insert(0, '/Users/pancq/Desktop/trae/基石/backend/src')

from services.report_generator import MonthlyReportData, generate_report_pdf


def main():
    print("开始生成报告...")
    
    # 创建模拟数据
    data = MonthlyReportData(
        year=2026,
        month=6,
        company_name="北京快乐茄",
        company_short_name="快乐茄",
        it_department="信息技术部",
        it_contact="张三",
        generated_at=datetime.now(),
        availability_pct=99.5,
        circuit_cost_total=87393,
        incident_count=0,
        max_duration_hours=0,
        circuit_count=4,
        avg_recovery_hours=0,
        urgent_items=[],
        warning_items=[],
        cost_by_type=[
            {"type": "internet", "cost": 30000, "pct": 34.3},
            {"type": "sdwan", "cost": 21060, "pct": 24.1},
            {"type": "cloud", "cost": 21500, "pct": 24.6},
            {"type": "fiber", "cost": 14833, "pct": 17.0},
        ],
        cost_history=[
            {"month": "2026-01", "cost": 87393},
            {"month": "2026-02", "cost": 87393},
            {"month": "2026-03", "cost": 87393},
            {"month": "2026-04", "cost": 87393},
            {"month": "2026-05", "cost": 87393},
            {"month": "2026-06", "cost": 87393},
        ],
        incidents=[]
    )
    
    # 生成报告
    output_file = "/Users/pancq/Desktop/trae/基石/perfect_test_output.pdf"
    generate_report_pdf(data, output_file)
    print(f"✅ 报告已生成：{output_file}")


if __name__ == "__main__":
    main()
