from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.site import Site
from src.models.circuit import Circuit
from src.models.device import Device
from src.models.device_link import DeviceLink
from src.schemas import DeviceLinkCreate, DeviceLinkUpdate, DeviceLinkResponse

router = APIRouter(tags=["topology"])


@router.get("/site-graph")
async def get_site_graph(db: AsyncSession = Depends(get_db)):
    """获取站点间拓扑数据"""
    # 获取所有站点
    sites_result = await db.execute(select(Site))
    sites = sites_result.scalars().all()
    
    # 获取所有专线
    circuits_result = await db.execute(select(Circuit))
    circuits = circuits_result.scalars().all()
    
    # 统计每个站点的设备数量
    device_counts = {}
    device_result = await db.execute(
        select(Device.site_id, func.count(Device.id))
        .group_by(Device.site_id)
    )
    for site_id, count in device_result.all():
        device_counts[site_id] = count
    
    # 构建节点
    nodes = []
    for site in sites:
        node = {
            "id": f"site_{site.id}",
            "site_id": site.id,
            "name": site.name,
            "city": site.city,
            "status": site.status,
            "device_count": device_counts.get(site.id, 0),
            "circuit_count": 0,
            "contact": site.contact,
            "phone": site.contact_phone,
            "location": site.location,
            "room": site.room,
        }
        nodes.append(node)
    
    # 统计每个站点的专线数量并构建边
    circuit_counts = {}
    edges = []
    
    for circuit in circuits:
        # 跳过未关联站点的专线
        if not circuit.site_id:
            continue
        
        # 统计站点专线数量
        if circuit.site_id in circuit_counts:
            circuit_counts[circuit.site_id] += 1
        else:
            circuit_counts[circuit.site_id] = 1
        
        # 确定专线类型
        type_map = {
            "internet": "internet",
            "mpls": "mpls",
            "sdwan": "sdwan",
            "fiber": "fiber",
        }
        circuit_type = type_map.get(circuit.type.lower(), "internet")
        
        # 确定带宽标签
        bandwidth = circuit.bandwidth or 0
        if bandwidth >= 1000:
            bandwidth_label = f"{bandwidth // 1000}G"
        elif bandwidth >= 100:
            bandwidth_label = f"{bandwidth}M"
        else:
            bandwidth_label = f"{bandwidth}M"
        
        # 构建边（假设专线连接到总部站点）
        # 实际应用中可能需要存储对端站点信息
        edge = {
            "id": f"circuit_{circuit.id}",
            "circuit_id": circuit.id,
            "source": f"site_{circuit.site_id}",
            "target": "site_hub",  # 虚拟中心节点
            "name": circuit.name,
            "provider": circuit.provider,
            "type": circuit_type,
            "bandwidth": bandwidth,
            "bandwidth_label": bandwidth_label,
            "status": circuit.status,
            "monthly_cost": circuit.monthly_cost,
            "contract_end": circuit.contract_end.isoformat() if circuit.contract_end else None,
            "days_to_expire": None,  # 可后续计算
        }
        edges.append(edge)
    
    # 更新节点的专线数量
    for node in nodes:
        node["circuit_count"] = circuit_counts.get(node["site_id"], 0)
    
    # 添加虚拟中心节点
    hub_node = {
        "id": "site_hub",
        "site_id": 0,
        "name": "网络中心",
        "city": "总部",
        "status": "normal",
        "device_count": 0,
        "circuit_count": len(edges),
        "contact": "-",
        "phone": "-",
        "location": "-",
        "room": "-",
    }
    nodes.append(hub_node)
    
    return {
        "nodes": nodes,
        "edges": edges,
    }


@router.get("/device-graph")
async def get_device_graph(
    site_id: Optional[int] = Query(None, description="站点 ID，不提供则返回所有设备"),
    db: AsyncSession = Depends(get_db)
):
    """获取站点内设备拓扑数据"""
    from src.models.ip_address import IPAddress
    from src.models.link_monitor import LinkMonitor
    
    # 获取设备及其关联的IP地址和站点信息
    query = select(Device, IPAddress, Site).outerjoin(IPAddress, Device.mgmt_ip_id == IPAddress.id).outerjoin(Site, Device.site_id == Site.id)
    if site_id:
        query = query.where(Device.site_id == site_id)
    
    result = await db.execute(query)
    device_ip_site_pairs = result.all()
    
    # 获取设备连接关系
    links_query = select(DeviceLink)
    links_result = await db.execute(links_query)
    links = links_result.scalars().all()
    
    # 获取最新的监控数据
    monitor_query = select(
        LinkMonitor.device_id,
        LinkMonitor.latency,
        LinkMonitor.packet_loss,
        LinkMonitor.status
    ).order_by(LinkMonitor.created_at.desc())
    monitor_result = await db.execute(monitor_query)
    monitor_data = monitor_result.all()
    
    # 构建监控数据字典（按device_id分组，取最新的）
    monitor_dict = {}
    for device_id, latency, packet_loss, status in monitor_data:
        if device_id not in monitor_dict:
            monitor_dict[device_id] = {
                "latency": latency,
                "packet_loss": packet_loss,
                "monitor_status": status
            }
    
    nodes = []
    edges = []
    
    # 构建设备节点
    for device, ip_addr, site in device_ip_site_pairs:
        # 首先获取监控数据
        monitor_info = monitor_dict.get(device.id, {})
        latency = monitor_info.get("latency")
        packet_loss = monitor_info.get("packet_loss")
        monitor_status = monitor_info.get("monitor_status")
        
        # 状态判定优先级：监控状态 > 设备状态 > 默认状态
        status = "unknown"  # 默认状态改为unknown
        
        # 如果有监控状态，优先使用监控状态
        if monitor_status:
            status = monitor_status
        # 否则使用设备模型中的状态
        elif device.status == "offline" or device.status == "decommissioned":
            status = "offline"
        elif device.status == "warning":
            status = "warning"
        elif device.status == "active":
            # 设备状态为active但没有监控数据，标记为未知（保持默认的unknown）
            pass
        
        device_type = "switch"
        if device.type:
            if "router" in device.type.lower():
                device_type = "router"
            elif "firewall" in device.type.lower():
                device_type = "firewall"
            elif "server" in device.type.lower():
                device_type = "server"
        
        node = {
            "id": f"device_{device.id}",
            "device_id": device.id,
            "name": device.name,
            "ip_address": ip_addr.address if ip_addr else None,
            "type": device_type,
            "vendor": device.vendor or "unknown",
            "status": status,
            "site_id": device.site_id,
            "site_name": site.name if site else None,
            "latency": latency,
            "packet_loss": packet_loss,
        }
        nodes.append(node)
    
    # 构建连接边
    for link in links:
        edge = {
            "id": f"link_{link.id}",
            "link_id": link.id,
            "source": f"device_{link.source_device_id}",
            "target": f"device_{link.target_device_id}",
            "source_interface": link.source_interface,
            "target_interface": link.target_interface,
            "link_type": link.link_type,
            "confidence": link.confidence,
        }
        edges.append(edge)
    
    return {
        "nodes": nodes,
        "edges": edges,
    }


# 设备连接关系 CRUD API
@router.get("/device-links", response_model=List[DeviceLinkResponse])
async def read_device_links(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取设备连接关系列表"""
    query = select(DeviceLink).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/device-links/{link_id}", response_model=DeviceLinkResponse)
async def read_device_link(
    link_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取单个设备连接关系"""
    query = select(DeviceLink).where(DeviceLink.id == link_id)
    result = await db.execute(query)
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Device link not found")
    return link


@router.post("/device-links", response_model=DeviceLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_device_link(
    link: DeviceLinkCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建设备连接关系"""
    # 验证源设备和目标设备是否存在
    source_query = select(Device).where(Device.id == link.source_device_id)
    source_result = await db.execute(source_query)
    if not source_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Source device not found")
    
    target_query = select(Device).where(Device.id == link.target_device_id)
    target_result = await db.execute(target_query)
    if not target_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Target device not found")
    
    # 检查是否已存在相同的连接
    existing_query = select(DeviceLink).where(
        ((DeviceLink.source_device_id == link.source_device_id) & 
         (DeviceLink.target_device_id == link.target_device_id)) |
        ((DeviceLink.source_device_id == link.target_device_id) & 
         (DeviceLink.target_device_id == link.source_device_id))
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Device link already exists")
    
    # 创建连接关系
    db_link = DeviceLink(**link.model_dump())
    db_link.discovered_at = datetime.now()
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link


@router.put("/device-links/{link_id}", response_model=DeviceLinkResponse)
async def update_device_link(
    link_id: int,
    link_update: DeviceLinkUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新设备连接关系"""
    query = select(DeviceLink).where(DeviceLink.id == link_id)
    result = await db.execute(query)
    db_link = result.scalar_one_or_none()
    if db_link is None:
        raise HTTPException(status_code=404, detail="Device link not found")
    
    # 更新字段
    update_data = link_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_link, field, value)
    
    await db.commit()
    await db.refresh(db_link)
    return db_link


@router.delete("/device-links/{link_id}")
async def delete_device_link(
    link_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除设备连接关系"""
    query = select(DeviceLink).where(DeviceLink.id == link_id)
    result = await db.execute(query)
    db_link = result.scalar_one_or_none()
    if db_link is None:
        raise HTTPException(status_code=404, detail="Device link not found")
    
    await db.delete(db_link)
    await db.commit()
    return {"message": "Device link deleted successfully"}


@router.post("/discover-lldp")
async def discover_lldp_neighbors(
    db: AsyncSession = Depends(get_db)
):
    """触发 LLDP/CDP 邻居发现"""
    from src.services.lldp_discovery import run_full_discovery
    
    try:
        await run_full_discovery(db)
        return {"message": "LLDP discovery completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")
