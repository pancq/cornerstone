from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.circuit import Circuit
from src.models.device import Device
from src.models.prefix import Prefix
from src.models.ip_address import IPAddress
from src.models.backup import Backup
from src.models.audit_log import AuditLog
from src.models.site import Site
from src.models.link_monitor import LinkMonitor

router = APIRouter(tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    time_range: str = "all",
    db: AsyncSession = Depends(get_db)
):
    """获取仪表盘统计数据"""
    
    # 解析时间范围参数
    now = datetime.now()
    start_time = None
    
    if time_range == "24h":
        start_time = now - timedelta(hours=24)
    elif time_range == "7d":
        start_time = now - timedelta(days=7)
    elif time_range == "15d":
        start_time = now - timedelta(days=15)
    elif time_range == "30d":
        start_time = now - timedelta(days=30)
    elif time_range == "all":
        start_time = None
    else:
        start_time = None
    
    # 1. 站点统计
    total_sites_result = await db.execute(select(func.count(Site.id)))
    total_sites = total_sites_result.scalar() or 0
    
    # 2. 专线统计
    total_circuits_result = await db.execute(select(func.count(Circuit.id)))
    total_circuits = total_circuits_result.scalar() or 0
    
    normal_circuits_result = await db.execute(
        select(func.count(Circuit.id)).where(Circuit.status == '正常')
    )
    normal_circuits = normal_circuits_result.scalar() or 0
    
    # 3. 带宽统计
    bandwidth_result = await db.execute(
        select(func.sum(Circuit.bandwidth)).where(Circuit.status == '正常')
    )
    total_bandwidth = bandwidth_result.scalar() or 0
    
    # 4. 设备统计
    total_devices_result = await db.execute(select(func.count(Device.id)))
    total_devices = total_devices_result.scalar() or 0
    
    # 在线设备（有监控数据且状态为normal的设备）
    online_devices_result = await db.execute(
        select(func.count(func.distinct(LinkMonitor.device_id)))
        .where(LinkMonitor.status == 'normal')
    )
    online_devices = online_devices_result.scalar() or 0
    
    # 5. IP地址统计
    # 获取所有前缀并计算实际可用IP数量
    prefixes_result = await db.execute(select(Prefix.network))
    prefixes = prefixes_result.scalars().all()
    
    # 根据CIDR掩码计算每个子网的可用IP数量
    def calculate_usable_ips(network: str) -> int:
        """根据CIDR格式计算可用IP数量"""
        try:
            if '/' in network:
                prefix_length = int(network.split('/')[1])
                # 可用IP数 = 2^(32-prefix_length) - 2（减去网络地址和广播地址）
                if prefix_length >= 31:
                    return 1 if prefix_length == 32 else 2  # /32只有1个IP，/31有2个
                return 2 ** (32 - prefix_length) - 2
            return 254  # 默认/24
        except:
            return 254
    
    ip_total = sum(calculate_usable_ips(prefix) for prefix in prefixes) if prefixes else 0
    
    ip_used_result = await db.execute(
        select(func.count(IPAddress.id)).where(IPAddress.status == 'assigned')
    )
    ip_used = ip_used_result.scalar() or 0
    
    ip_usage_percent = round((ip_used / ip_total * 100), 1) if ip_total > 0 else 0
    
    # 6. 备份统计
    backup_query = select(func.count(Backup.id))
    if start_time:
        backup_query = backup_query.where(Backup.created_at >= start_time)
    total_backups_result = await db.execute(backup_query)
    total_backups = total_backups_result.scalar() or 0
    
    successful_backup_query = select(func.count(Backup.id)).where(Backup.status == 'success')
    if start_time:
        successful_backup_query = successful_backup_query.where(Backup.created_at >= start_time)
    successful_backups_result = await db.execute(successful_backup_query)
    successful_backups = successful_backups_result.scalar() or 0
    
    failed_backup_query = select(func.count(Backup.id)).where(Backup.status == 'failed')
    if start_time:
        failed_backup_query = failed_backup_query.where(Backup.created_at >= start_time)
    failed_backups_result = await db.execute(failed_backup_query)
    failed_backups = failed_backups_result.scalar() or 0
    
    # 7. 系统健康度计算
    # 基于设备监控状态计算健康度
    health_score = 100
    
    # 获取设备监控状态分布
    health_query = (
        select(
            LinkMonitor.status,
            func.count(LinkMonitor.id).label("count")
        )
        .group_by(LinkMonitor.status)
    )
    health_result = await db.execute(health_query)
    health_data = health_result.all()
    
    total_monitored = sum(count for _, count in health_data) if health_data else 0
    
    # 使用告警占总监控数的比例来计算健康度扣分
    for status, count in health_data:
        if status == 'critical':
            health_score -= (count / total_monitored * 100) * 0.5 if total_monitored > 0 else 0
        elif status == 'warning':
            health_score -= (count / total_monitored * 100) * 0.25 if total_monitored > 0 else 0
    
    health_score = max(0, min(100, round(health_score)))
    
    return {
        "sites": {
            "total": total_sites
        },
        "circuits": {
            "total": total_circuits,
            "normal": normal_circuits,
            "bandwidth": total_bandwidth
        },
        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": total_devices - online_devices
        },
        "ip": {
            "total": ip_total,
            "used": ip_used,
            "percent": ip_usage_percent
        },
        "backups": {
            "total": total_backups,
            "successful": successful_backups,
            "failed": failed_backups
        },
        "health": {
            "score": health_score,
            "status": "excellent" if health_score >= 90 else "good" if health_score >= 70 else "warning" if health_score >= 50 else "critical"
        }
    }


@router.get("/prefixes-usage")
async def get_prefixes_usage(db: AsyncSession = Depends(get_db)):
    """获取子网使用率"""
    
    # 获取所有前缀
    prefixes_result = await db.execute(select(Prefix))
    prefixes = prefixes_result.scalars().all()
    
    # 获取每个前缀的IP使用情况
    usage_list = []
    for prefix in prefixes:
        # 统计该前缀下已分配的IP数量
        ip_count_result = await db.execute(
            select(func.count(IPAddress.id)).where(
                and_(
                    IPAddress.prefix_id == prefix.id,
                    IPAddress.status == 'assigned'
                )
            )
        )
        ip_count = ip_count_result.scalar() or 0
        
        # 计算使用率（假设每个子网254个可用IP）
        usage_percent = round((ip_count / 254) * 100, 1) if 254 > 0 else 0
        
        usage_list.append({
            "id": prefix.id,
            "network": prefix.network,
            "vlan": prefix.vlan,
            "usage": f"{ip_count}/254",
            "usage_percent": usage_percent
        })
    
    return usage_list


@router.get("/recent-logs")
async def get_recent_logs(
    limit: int = 8,
    db: AsyncSession = Depends(get_db)
):
    """获取最近的操作日志"""
    
    logs_result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    logs = logs_result.scalars().all()
    
    return [
        {
            "id": log.id,
            "user": log.user,
            "action": log.action,
            "resource": log.resource,
            "detail": log.detail,
            "success": log.success,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]


@router.get("/circuit-types")
async def get_circuit_types(db: AsyncSession = Depends(get_db)):
    """获取专线类型分布统计（含带宽）"""
    
    # 获取所有专线类型的数量和总带宽
    circuits_result = await db.execute(
        select(Circuit.type, func.count(Circuit.id).label("count"), func.coalesce(func.sum(Circuit.bandwidth), 0).label("bandwidth"))
        .group_by(Circuit.type)
    )
    circuits = circuits_result.all()
    
    # 统计各类型数量和带宽
    type_stats = {}
    for circuit_type, count, bandwidth in circuits:
        if circuit_type:
            type_stats[circuit_type] = {'count': count, 'bandwidth': bandwidth}
        else:
            type_stats['未分类'] = {
                'count': type_stats.get('未分类', {}).get('count', 0) + count,
                'bandwidth': type_stats.get('未分类', {}).get('bandwidth', 0) + bandwidth
            }
    
    # 专线类型中文名映射
    type_labels = {
        '互联网专线': '互联网专线',
        'MPLS': 'MPLS',
        'SD-WAN': 'SD-WAN',
        '光纤专线': '光纤专线',
        '云专线': '云专线',
        '未分类': '未分类'
    }
    
    # 专线类型颜色映射
    type_colors = {
        '互联网专线': '#409EFF',
        'MPLS': '#67C23A',
        'SD-WAN': '#E6A23C',
        '光纤专线': '#9C27B0',
        '云专线': '#00BCD4',
        '未分类': '#909399'
    }
    
    return [
        {
            "name": type_labels.get(name, name),
            "value": stats['count'],
            "bandwidth": stats['bandwidth'],
            "type": name,
            "color": type_colors.get(name, '#909399')
        }
        for name, stats in type_stats.items()
    ]


@router.get("/device-types")
async def get_device_types(db: AsyncSession = Depends(get_db)):
    """获取设备类型分布统计"""
    
    # 获取所有设备的vendor和type字段
    devices_result = await db.execute(select(Device.vendor, Device.type))
    devices = devices_result.all()
    
    # 统计各品牌数量
    brand_counts = {}
    
    def get_brand(vendor: str, device_type: str) -> str:
        """根据vendor和type确定品牌"""
        if not vendor:
            # 如果没有vendor，尝试从type推断
            if device_type:
                normalized_type = device_type.lower()
                if 'huawei' in normalized_type or 'vrp' in normalized_type:
                    return 'huawei'
                elif 'cisco' in normalized_type:
                    return 'cisco'
                elif 'ruijie' in normalized_type or '锐捷' in device_type:
                    return 'ruijie'
                elif 'h3c' in normalized_type:
                    return 'h3c'
                elif 'juniper' in normalized_type:
                    return 'juniper'
                elif 'fortinet' in normalized_type or 'fortigate' in normalized_type:
                    return 'fortinet'
            return 'unknown'
        
        normalized_vendor = vendor.lower()
        if 'huawei' in normalized_vendor or 'vrp' in normalized_vendor:
            return 'huawei'
        elif 'cisco' in normalized_vendor:
            return 'cisco'
        elif 'ruijie' in normalized_vendor or '锐捷' in vendor:
            return 'ruijie'
        elif 'h3c' in normalized_vendor:
            return 'h3c'
        elif 'juniper' in normalized_vendor:
            return 'juniper'
        elif 'fortinet' in normalized_vendor or 'fortigate' in normalized_vendor:
            return 'fortinet'
        elif 'arista' in normalized_vendor:
            return 'arista'
        elif 'mikrotik' in normalized_vendor:
            return 'mikrotik'
        elif 'dell' in normalized_vendor or 'force10' in normalized_vendor:
            return 'dell'
        elif 'hp' in normalized_vendor:
            return 'hp'
        else:
            return 'other'
    
    for vendor, device_type in devices:
        brand = get_brand(vendor, device_type)
        brand_counts[brand] = brand_counts.get(brand, 0) + 1
    
    # 品牌中文名映射
    brand_labels = {
        'huawei': '华为',
        'cisco': '思科',
        'ruijie': '锐捷',
        'h3c': 'H3C',
        'juniper': '瞻博',
        'fortinet': '飞塔',
        'arista': 'Arista',
        'mikrotik': 'MikroTik',
        'dell': '戴尔',
        'hp': '惠普',
        'other': '其他',
        'unknown': '未知'
    }
    
    return [
        {
            "name": brand_labels.get(name, name),
            "value": count,
            "type": name
        }
        for name, count in brand_counts.items()
    ]
