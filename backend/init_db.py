#!/usr/bin/env python3
"""初始化数据库"""
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from passlib.context import CryptContext
import sqlalchemy.orm
from src.database import sync_engine, Base
from src.models import Aggregate, AuditLog, Backup, Circuit, Device, IPAddress, Prefix, Site, User, Vlan, VlanGroup
from src.models.alert import AlertRule  # 确保关联模型被加载

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_demo_data(session: sqlalchemy.orm.Session):
    """写入脱敏演示数据，仅在空库中执行。"""
    if session.query(Site).first():
        return

    sites = [
        Site(id=1, name="演示站点A", location="示例园区A · 101机房", city="示例城市A", room="101机房", contact="演示管理员", contact_phone="010-0000-0001", status="online", alert_count=0),
        Site(id=2, name="演示站点B", location="示例园区B · 201机房", city="示例城市B", room="201机房", contact="演示操作员", contact_phone="010-0000-0002", status="alert", alert_count=2),
        Site(id=3, name="演示实验室", location="示例实验室 · 机柜区", city="示例城市C", room="实验室机柜区", contact="演示观察员", contact_phone="010-0000-0003", status="offline", alert_count=0),
    ]
    session.add_all(sites)
    session.flush()

    aggregates = [
        Aggregate(id=1, network="192.0.2.0/24", name="演示管理地址池"),
        Aggregate(id=2, network="198.51.100.0/24", name="演示实验室地址池"),
    ]
    session.add_all(aggregates)

    prefixes = [
        Prefix(id=1, aggregate_id=1, network="192.0.2.0/26", site_id=1, vlan="10", usage="演示办公网络"),
        Prefix(id=2, aggregate_id=1, network="192.0.2.64/26", site_id=1, vlan="20", usage="演示管理网络"),
        Prefix(id=3, aggregate_id=1, network="192.0.2.128/26", site_id=2, vlan="30", usage="演示分支网络"),
        Prefix(id=4, aggregate_id=2, network="198.51.100.0/26", site_id=3, vlan="120", usage="演示实验室网络"),
    ]
    session.add_all(prefixes)
    session.flush()

    devices = [
        Device(id=1, name="SW-DEMO-CORE-01", type="交换机", brand="Cisco", vendor="cisco_ios", model="Catalyst 9300", sn="DEMO-SW-0001", site_id=1, location="演示机柜A-U12", status="active", purchase_date=datetime(2024, 3, 12), warranty_end=datetime(2026, 6, 18), purchase_amount=82000, owner="演示网络组", note="演示核心交换机"),
        Device(id=2, name="FW-DEMO-EDGE-01", type="防火墙", brand="Huawei", vendor="huawei_vrp", model="USG6655E", sn="DEMO-FW-0001", site_id=1, location="演示机柜B-U06", status="active", purchase_date=datetime(2023, 8, 20), warranty_end=datetime(2026, 5, 30), purchase_amount=128000, owner="演示安全组", note="演示互联网边界防火墙"),
        Device(id=3, name="RT-DEMO-WAN-01", type="路由器", brand="H3C", vendor="h3c", model="MSR 5660", sn="DEMO-RT-0001", site_id=2, location="演示机柜C-U08", status="maintenance", purchase_date=datetime(2022, 10, 1), warranty_end=datetime(2026, 12, 1), purchase_amount=64000, owner="演示网络组", note="演示广域网边界路由器"),
    ]
    session.add_all(devices)
    session.flush()

    ip_addresses = [
        IPAddress(id=1, address="192.0.2.65", prefix_id=2, device_id=1, usage="演示核心交换机管理地址", owner="演示网络组", status="assigned"),
        IPAddress(id=2, address="192.0.2.66", prefix_id=2, device_id=2, usage="演示防火墙管理地址", owner="演示安全组", status="assigned"),
        IPAddress(id=3, address="192.0.2.129", prefix_id=3, device_id=3, usage="演示分支路由器管理地址", owner="演示网络组", status="assigned"),
        IPAddress(id=4, address="198.51.100.10", prefix_id=4, usage="演示实验室预留主机", owner="演示实验室", status="reserved"),
    ]
    session.add_all(ip_addresses)
    session.flush()
    for device_id, mgmt_ip_id in [(1, 1), (2, 2), (3, 3)]:
        session.query(Device).filter(Device.id == device_id).update({"mgmt_ip_id": mgmt_ip_id})
    session.flush()

    circuits = [
        Circuit(name="演示站点A互联网专线", provider="演示运营商A", type="互联网专线", site_id=1, bandwidth=1000, monthly_cost=18800, contract_start=datetime(2025, 7, 1), contract_end=datetime(2026, 6, 12), circuit_no="DEMO-INET-001", support_phone="010-0000-1001", public_ip="203.0.113.8/29", status="正常", note="演示主用互联网专线", updated_by="admin"),
        Circuit(name="演示站点A-B MPLS专线", provider="演示运营商B", type="MPLS", site_id=2, bandwidth=500, monthly_cost=22600, contract_start=datetime(2025, 4, 20), contract_end=datetime(2026, 5, 28), circuit_no="DEMO-MPLS-002", support_phone="010-0000-1002", public_ip="", status="正常", note="演示私有广域网专线", updated_by="ops"),
        Circuit(name="演示实验室SD-WAN备份", provider="演示运营商C", type="SD-WAN", site_id=3, bandwidth=200, monthly_cost=5200, contract_start=datetime(2024, 11, 1), contract_end=datetime(2026, 11, 1), circuit_no="DEMO-SDWAN-003", support_phone="010-0000-1003", public_ip="198.51.100.16/28", status="故障", note="演示降级备份链路", updated_by="ops"),
    ]
    session.add_all(circuits)
    session.flush()

    backups = [
        Backup(device_id=1, version=1, content="hostname SW-DEMO-CORE-01\ninterface Vlan20\n ip address 192.0.2.65 255.255.255.192\nspanning-tree mode rapid-pvst\nntp server 192.0.2.10\nline vty 0 4\n transport input ssh", trigger="scheduled", operator="system", status="success", has_change=False, size=1186, note="演示每日备份"),
        Backup(device_id=1, version=2, content="hostname SW-DEMO-CORE-01\ninterface Vlan20\n ip address 192.0.2.65 255.255.255.192\nspanning-tree mode rapid-pvst\nntp server 192.0.2.10\nntp server 192.0.2.11\nline vty 0 4\n transport input ssh", trigger="scheduled", operator="system", status="success", has_change=True, change_summary="演示新增NTP服务器", size=1224, note="演示每日备份"),
        Backup(device_id=2, version=1, content="", trigger="scheduled", operator="system", status="failed", error_message="演示SSH连接超时", has_change=False, size=0, note="演示SSH连接超时"),
    ]
    session.add_all(backups)

    vlan_groups = [
        VlanGroup(id=1, name="演示站点A VLAN组", site_id=1, description="演示站点A的VLAN分组"),
        VlanGroup(id=2, name="演示站点B VLAN组", site_id=2, description="演示站点B的VLAN分组"),
        VlanGroup(id=3, name="演示实验室 VLAN组", site_id=3, description="演示实验室的VLAN分组"),
    ]
    session.add_all(vlan_groups)
    session.flush()

    vlans = [
        Vlan(vid=10, name="演示办公网络", group_id=1, site_id=1, status="active", description="演示办公网络VLAN"),
        Vlan(vid=20, name="演示管理网络", group_id=1, site_id=1, status="active", description="演示设备管理VLAN"),
        Vlan(vid=30, name="演示服务器网络", group_id=1, site_id=1, status="active", description="演示服务器VLAN"),
        Vlan(vid=10, name="演示分支办公网络", group_id=2, site_id=2, status="active", description="演示分支办公网络VLAN"),
        Vlan(vid=120, name="演示实验室网络", group_id=3, site_id=3, status="active", description="演示实验室网络VLAN"),
        Vlan(vid=999, name="演示DMZ网络", status="reserved", description="演示预留DMZ VLAN"),
    ]
    session.add_all(vlans)

    audit_logs = [
        AuditLog(user="ops", action="更新专线状态", resource="演示实验室SD-WAN备份", detail="状态由 正常 改为 故障", ip_address="192.0.2.200", success="true"),
        AuditLog(user="system", action="配置备份", resource="FW-DEMO-EDGE-01", detail="备份失败：SSH连接超时", ip_address="127.0.0.1", success="false"),
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

    with sqlalchemy.orm.Session(sync_engine) as session:
        existing_admin = session.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed_password,
                display_name="管理员",
                is_active=True,
                is_superuser=True,
            )
            session.add(admin_user)

            test_user = User(
                username="user",
                email="user@example.com",
                hashed_password=pwd_context.hash("user123"),
                display_name="测试用户",
                is_active=True,
                is_superuser=False,
            )
            session.add(test_user)
            session.flush()
            print("默认用户创建成功！")
        else:
            print("管理员用户已存在，跳过创建。")

        # 写入演示数据（空库或首次运行）
        seed_demo_data(session)
        session.commit()

    print("\n默认账号:")
    print("  管理员: admin / INITIAL_ADMIN_PASSWORD 环境变量指定的密码（未设置时为开发默认 password）")
    print("  普通用户: user / user123")


if __name__ == "__main__":
    init_db()
