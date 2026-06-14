#!/usr/bin/env python3
"""初始化数据库"""
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from src.database import sync_engine, Base
from src.models import Aggregate, AuditLog, Backup, Circuit, Device, IPAddress, Prefix, Site, User, Vlan, VlanGroup

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_demo_data(session: Session):
    """写入脱敏演示数据，仅在空库中执行。"""
    if session.query(Site).first():
        return

    sites = [
        Site(id=1, name="Demo Site A", location="Example Campus A · Room 101", city="Example City A", room="Room 101", contact="Demo Admin", contact_phone="010-0000-0001", status="online", alert_count=0),
        Site(id=2, name="Demo Site B", location="Example Campus B · Room 201", city="Example City B", room="Room 201", contact="Demo Operator", contact_phone="010-0000-0002", status="alert", alert_count=2),
        Site(id=3, name="Demo Lab", location="Example Lab · Rack Zone", city="Example City C", room="Lab Rack Zone", contact="Demo Viewer", contact_phone="010-0000-0003", status="offline", alert_count=0),
    ]
    session.add_all(sites)

    aggregates = [
        Aggregate(id=1, network="192.0.2.0/24", name="Demo management address pool"),
        Aggregate(id=2, network="198.51.100.0/24", name="Demo lab address pool"),
    ]
    session.add_all(aggregates)

    prefixes = [
        Prefix(id=1, aggregate_id=1, network="192.0.2.0/26", site_id=1, vlan="10", usage="Demo office network"),
        Prefix(id=2, aggregate_id=1, network="192.0.2.64/26", site_id=1, vlan="20", usage="Demo management network"),
        Prefix(id=3, aggregate_id=1, network="192.0.2.128/26", site_id=2, vlan="30", usage="Demo branch network"),
        Prefix(id=4, aggregate_id=2, network="198.51.100.0/26", site_id=3, vlan="120", usage="Demo lab network"),
    ]
    session.add_all(prefixes)

    devices = [
        Device(id=1, name="SW-DEMO-CORE-01", type="交换机", brand="Cisco", vendor="cisco_ios", model="Catalyst 9300", sn="DEMO-SW-0001", site_id=1, location="Demo Rack A-U12", mgmt_ip_id=1, status="active", purchase_date=datetime(2024, 3, 12), warranty_end=datetime(2026, 6, 18), purchase_amount=82000, owner="Demo NetOps", note="Demo core switch"),
        Device(id=2, name="FW-DEMO-EDGE-01", type="防火墙", brand="Huawei", vendor="huawei_vrp", model="USG6655E", sn="DEMO-FW-0001", site_id=1, location="Demo Rack B-U06", mgmt_ip_id=2, status="active", purchase_date=datetime(2023, 8, 20), warranty_end=datetime(2026, 5, 30), purchase_amount=128000, owner="Demo SecOps", note="Demo internet edge firewall"),
        Device(id=3, name="RT-DEMO-WAN-01", type="路由器", brand="H3C", vendor="h3c", model="MSR 5660", sn="DEMO-RT-0001", site_id=2, location="Demo Rack C-U08", mgmt_ip_id=3, status="maintenance", purchase_date=datetime(2022, 10, 1), warranty_end=datetime(2026, 12, 1), purchase_amount=64000, owner="Demo NetOps", note="Demo WAN edge router"),
    ]
    session.add_all(devices)

    ip_addresses = [
        IPAddress(id=1, address="192.0.2.65", prefix_id=2, device_id=1, usage="Demo core switch management", owner="Demo NetOps", status="assigned"),
        IPAddress(id=2, address="192.0.2.66", prefix_id=2, device_id=2, usage="Demo firewall management", owner="Demo SecOps", status="assigned"),
        IPAddress(id=3, address="192.0.2.129", prefix_id=3, device_id=3, usage="Demo branch router management", owner="Demo NetOps", status="assigned"),
        IPAddress(id=4, address="198.51.100.10", prefix_id=4, usage="Demo reserved lab host", owner="Demo Lab", status="reserved"),
    ]
    session.add_all(ip_addresses)

    circuits = [
        Circuit(name="Demo Site A Internet Circuit", provider="Demo ISP A", type="互联网专线", site_id=1, bandwidth=1000, monthly_cost=18800, contract_start=datetime(2025, 7, 1), contract_end=datetime(2026, 6, 12), circuit_no="DEMO-INET-001", support_phone="010-0000-1001", public_ip="203.0.113.8/29", status="正常", note="Demo primary internet circuit", updated_by="admin"),
        Circuit(name="Demo Site A-B MPLS Circuit", provider="Demo ISP B", type="MPLS", site_id=2, bandwidth=500, monthly_cost=22600, contract_start=datetime(2025, 4, 20), contract_end=datetime(2026, 5, 28), circuit_no="DEMO-MPLS-002", support_phone="010-0000-1002", public_ip="", status="正常", note="Demo private WAN circuit", updated_by="ops"),
        Circuit(name="Demo Lab SD-WAN Backup", provider="Demo ISP C", type="SD-WAN", site_id=3, bandwidth=200, monthly_cost=5200, contract_start=datetime(2024, 11, 1), contract_end=datetime(2026, 11, 1), circuit_no="DEMO-SDWAN-003", support_phone="010-0000-1003", public_ip="198.51.100.16/28", status="故障", note="Demo degraded backup link", updated_by="ops"),
    ]
    session.add_all(circuits)

    backups = [
        Backup(device_id=1, version=1, content="hostname SW-DEMO-CORE-01\ninterface Vlan20\n ip address 192.0.2.65 255.255.255.192\nspanning-tree mode rapid-pvst\nntp server 192.0.2.10\nline vty 0 4\n transport input ssh", trigger="scheduled", operator="system", status="success", has_change=False, size=1186, note="Demo daily backup"),
        Backup(device_id=1, version=2, content="hostname SW-DEMO-CORE-01\ninterface Vlan20\n ip address 192.0.2.65 255.255.255.192\nspanning-tree mode rapid-pvst\nntp server 192.0.2.10\nntp server 192.0.2.11\nline vty 0 4\n transport input ssh", trigger="scheduled", operator="system", status="success", has_change=True, change_summary="Demo NTP server added", size=1224, note="Demo daily backup"),
        Backup(device_id=2, version=1, content="", trigger="scheduled", operator="system", status="failed", error_message="Demo SSH timeout", has_change=False, size=0, note="Demo SSH timeout"),
    ]
    session.add_all(backups)

    vlan_groups = [
        VlanGroup(id=1, name="Demo Site A VLANs", site_id=1, description="Demo Site A VLAN group"),
        VlanGroup(id=2, name="Demo Site B VLANs", site_id=2, description="Demo Site B VLAN group"),
        VlanGroup(id=3, name="Demo Lab VLANs", site_id=3, description="Demo lab VLAN group"),
    ]
    session.add_all(vlan_groups)

    vlans = [
        Vlan(vid=10, name="Demo Office", group_id=1, site_id=1, status="active", description="Demo office network"),
        Vlan(vid=20, name="Demo Management", group_id=1, site_id=1, status="active", description="Demo network management VLAN"),
        Vlan(vid=30, name="Demo Server", group_id=1, site_id=1, status="active", description="Demo server VLAN"),
        Vlan(vid=10, name="Demo Branch Office", group_id=2, site_id=2, status="active", description="Demo branch office network"),
        Vlan(vid=120, name="Demo Lab", group_id=3, site_id=3, status="active", description="Demo lab network"),
        Vlan(vid=999, name="Demo DMZ", status="reserved", description="Demo reserved DMZ VLAN"),
    ]
    session.add_all(vlans)

    audit_logs = [
        AuditLog(user="ops", action="更新专线状态", resource="Demo Lab SD-WAN Backup", detail="状态由 正常 改为 故障", ip_address="192.0.2.200", success="true"),
        AuditLog(user="system", action="配置备份", resource="FW-DEMO-EDGE-01", detail="备份失败：Demo SSH timeout", ip_address="127.0.0.1", success="false"),
    ]
    session.add_all(audit_logs)


def init_db():
    """初始化数据库"""
    print("创建数据库表...")
    Base.metadata.create_all(bind=sync_engine)
    print("数据库表创建成功！")

    print("创建默认管理员用户...")
    initial_admin_password = os.environ.get("INITIAL_ADMIN_PASSWORD", "password")
    hashed_password = pwd_context.hash(initial_admin_password)

    with Session(sync_engine) as session:
        existing_admin = session.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed_password,
                display_name="Administrator",
                is_active=True,
                is_superuser=True,
            )
            session.add(admin_user)

            test_user = User(
                username="user",
                email="user@example.com",
                hashed_password=pwd_context.hash("user123"),
                display_name="Test User",
                is_active=True,
                is_superuser=False,
            )
            session.add(test_user)
            session.flush()
            seed_demo_data(session)
            session.commit()
            print("默认用户和演示数据创建成功！")
        else:
            print("管理员用户已存在，跳过创建。")

    print("\n默认账号:")
    print("  管理员: admin / INITIAL_ADMIN_PASSWORD 环境变量指定的密码（未设置时为开发默认 password）")
    print("  普通用户: user / user123")


if __name__ == "__main__":
    init_db()
