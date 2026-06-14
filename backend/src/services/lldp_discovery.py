from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.device import Device
from src.models.device_link import DeviceLink
from src.models.credential import Credential
from src.models.ip_address import IPAddress
from src.utils.device_connection import connect_device, get_lldp_neighbors
from src.utils.crypto import decrypt_password


async def discover_device_neighbors(device: Device, credential: Credential, db: AsyncSession):
    """
    发现单个设备的邻居信息
    当当前凭证失败时，自动尝试其他可用凭证
    """
    try:
        # 获取设备的IP地址
        ip_query = select(IPAddress).where(IPAddress.id == device.mgmt_ip_id)
        ip_result = await db.execute(ip_query)
        ip_addr = ip_result.scalar_one_or_none()
        
        if not ip_addr:
            print(f"设备 {device.name} 没有配置管理IP")
            return []
        
        # 根据设备厂商确定Netmiko设备类型
        device_type = get_netmiko_device_type(device.vendor)
        
        # 获取所有可用凭证（用于自动重试）
        all_credentials = await get_all_credentials(db)
        
        # 先尝试传入的凭证，然后尝试其他凭证
        credentials_to_try = [credential] if credential else []
        for cred in all_credentials:
            if credential is None or cred.id != credential.id:
                credentials_to_try.append(cred)
        
        print(f"设备 {device.name} ({ip_addr.address}) 将尝试 {len(credentials_to_try)} 个凭证")
        
        for idx, cred in enumerate(credentials_to_try):
            print(f"  尝试凭证 [{idx+1}/{len(credentials_to_try)}]: {cred.name} (用户: {cred.username})")
            
            # 构建设备连接信息（密码需要解密）
            device_info = {
                "ip": ip_addr.address,
                "username": cred.username,
                "password": decrypt_password(cred.password) if cred.password else None,
                "device_type": device_type,
                "port": cred.port or 22,
                "secret": decrypt_password(cred.enable_password) if cred.enable_password else None
            }
            
            # 连接设备
            conn = connect_device(device_info)
            if conn:
                print(f"    ✓ 认证成功")
                # 获取 LLDP 邻居
                neighbors = get_lldp_neighbors(conn)
                conn.disconnect()
                
                if not neighbors:
                    print(f"    ✗ 未发现 LLDP 邻居")
                    return []
                
                # 处理邻居信息
                results = []
                for neighbor in neighbors:
                    # 尝试根据设备名查找目标设备
                    target_device = await find_device_by_name_or_ip(db, neighbor.get('remote_device'))
                    
                    if target_device:
                        results.append({
                            "source_device_id": device.id,
                            "source_interface": neighbor.get('local_interface'),
                            "target_device_id": target_device.id,
                            "target_interface": neighbor.get('remote_port'),
                            "link_type": "lldp",
                            "confidence": 100
                        })
                    else:
                        print(f"    未找到邻居设备: {neighbor.get('remote_device')}")
                
                print(f"    ✓ 成功发现 {len(results)} 条连接")
                return results
            else:
                print(f"    ✗ 认证失败")
        
        print(f"  所有凭证均尝试失败，跳过设备 {device.name}")
        return []
        
    except Exception as e:
        print(f"发现设备 {device.name} 邻居时出错: {str(e)}")
        return []


async def get_all_credentials(db: AsyncSession) -> list:
    """
    获取所有可用凭证
    """
    query = select(Credential)
    result = await db.execute(query)
    return result.scalars().all()


async def find_device_by_name_or_ip(db: AsyncSession, name_or_ip: str) -> Optional[Device]:
    """
    根据设备名或IP查找设备
    支持带后缀的设备名称匹配（如 PEK-SW-401-4-4.13 匹配 PEK-SW-401-4）
    """
    if not name_or_ip:
        return None
    
    # 尝试按名称查找（精确匹配优先）
    query = select(Device).where(Device.name == name_or_ip)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if device:
        return device
    
    # 尝试按名称模糊匹配（取第一个匹配的）
    query = select(Device).where(Device.name.ilike(f"%{name_or_ip}%")).limit(1)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if device:
        return device
    
    # 尝试反向匹配：获取所有设备，然后在Python中进行后缀匹配
    # 例如：PEK-SW-401-4-4.13 应该匹配数据库中的 PEK-SW-401-4
    query = select(Device)
    result = await db.execute(query)
    all_devices = result.scalars().all()
    
    # 按名称长度降序排序，优先匹配较长的名称（避免部分匹配）
    all_devices.sort(key=lambda d: len(d.name), reverse=True)
    
    for dev in all_devices:
        if name_or_ip.startswith(dev.name):
            print(f"  设备名称匹配（后缀匹配）: {name_or_ip} -> {dev.name}")
            return dev
    
    # 尝试按IP查找（需要关联IP地址表）
    from src.models.ip_address import IPAddress
    query = select(Device).join(IPAddress, Device.mgmt_ip_id == IPAddress.id).where(IPAddress.address == name_or_ip).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_or_create_device_links(db: AsyncSession, links_data: List[dict]):
    """
    更新或创建设备连接关系
    """
    for link_data in links_data:
        source_device_id = link_data['source_device_id']
        target_device_id = link_data['target_device_id']
        source_interface = link_data['source_interface']
        target_interface = link_data['target_interface']
        
        # 检查是否已存在相同的连接
        query = select(DeviceLink).where(
            (DeviceLink.source_device_id == source_device_id) &
            (DeviceLink.target_device_id == target_device_id)
        )
        result = await db.execute(query)
        existing_link = result.scalar_one_or_none()
        
        if existing_link:
            # 更新现有连接的接口信息
            existing_link.source_interface = source_interface
            existing_link.target_interface = target_interface
            existing_link.link_type = link_data['link_type']
            existing_link.confidence = link_data['confidence']
            existing_link.verified_at = datetime.now()
        else:
            # 检查反向连接是否存在
            query_reverse = select(DeviceLink).where(
                (DeviceLink.source_device_id == target_device_id) &
                (DeviceLink.target_device_id == source_device_id)
            )
            result_reverse = await db.execute(query_reverse)
            reverse_link = result_reverse.scalar_one_or_none()
            
            if reverse_link:
                # 更新反向连接的接口信息
                reverse_link.source_interface = target_interface
                reverse_link.target_interface = source_interface
                reverse_link.link_type = link_data['link_type']
                reverse_link.confidence = link_data['confidence']
                reverse_link.verified_at = datetime.now()
            else:
                # 创建新连接
                new_link = DeviceLink(
                    source_device_id=source_device_id,
                    source_interface=source_interface,
                    target_device_id=target_device_id,
                    target_interface=target_interface,
                    link_type=link_data['link_type'],
                    confidence=link_data['confidence'],
                    discovered_at=datetime.now()
                )
                db.add(new_link)
    
    await db.commit()


async def get_device_credential(db: AsyncSession, device: Device) -> Optional[Credential]:
    """
    获取设备的凭证（优先设备专用凭证，其次全局凭证）
    """
    # 先尝试获取设备专用凭证
    query = select(Credential).where(Credential.device_id == device.id).limit(1)
    result = await db.execute(query)
    credential = result.scalar_one_or_none()
    
    if credential:
        return credential
    
    # 再尝试获取全局凭证（device_id为空的凭证）
    query = select(Credential).where(Credential.device_id.is_(None)).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


def get_netmiko_device_type(vendor: str) -> str:
    """
    根据厂商获取Netmiko设备类型
    """
    vendor = vendor.lower() if vendor else ""
    if "huawei" in vendor:
        return "huawei"
    elif "h3c" in vendor or "hp" in vendor:
        return "hp_comware"
    elif "cisco" in vendor:
        return "cisco_ios"
    elif "juniper" in vendor:
        return "juniper_junos"
    elif "arista" in vendor:
        return "arista_eos"
    else:
        return "cisco_ios"


async def run_full_discovery(db: AsyncSession):
    """
    运行完整的设备发现
    """
    # 获取所有设备（排除离线设备）
    query = select(Device).where(Device.status != "offline")
    result = await db.execute(query)
    devices = result.scalars().all()
    
    if not devices:
        print("没有找到可用设备")
        return
    
    # 检查是否有凭证
    cred_query = select(Credential)
    cred_result = await db.execute(cred_query)
    credentials = cred_result.scalars().all()
    if not credentials:
        raise Exception("系统中没有配置任何设备凭证，请先在系统设置中添加SSH登录凭证")
    
    # 检查是否有设备配置了管理IP
    devices_with_ip = []
    devices_without_ip = []
    for device in devices:
        if device.mgmt_ip_id:
            devices_with_ip.append(device)
        else:
            devices_without_ip.append(device)
    
    if not devices_with_ip:
        raise Exception(f"没有设备配置了管理IP，无法进行LLDP发现。{len(devices_without_ip)}台设备需要配置管理IP：{', '.join([d.name for d in devices_without_ip])}")
    
    # 遍历所有设备进行发现
    all_links = []
    for device in devices_with_ip:
        # 获取设备凭证
        credential = await get_device_credential(db, device)
        if not credential:
            print(f"设备 {device.name} 没有配置凭证，跳过")
            continue
        
        print(f"正在发现设备: {device.name}")
        links = await discover_device_neighbors(device, credential, db)
        all_links.extend(links)
    
    # 更新或创建设备连接关系
    if all_links:
        await update_or_create_device_links(db, all_links)
        print(f"发现完成，共更新/创建 {len(all_links)} 条连接关系")
    else:
        # 如果没有发现任何连接，检查是否因为无法连接设备
        print("未发现任何新的连接关系。可能原因：")
        print("1. 无法通过SSH连接到设备")
        print("2. 设备未启用LLDP协议")
        print("3. 设备没有邻居设备")
        raise Exception("未发现任何LLDP邻居。请确保：\n1. 设备已配置管理IP\n2. 设备凭证正确\n3. 设备可达且启用了LLDP协议\n4. 设备有邻居设备")
