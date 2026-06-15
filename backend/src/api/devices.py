from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete

from ..database import get_db
from ..models import Device, Credential
from ..schemas import (
    DeviceCreate, DeviceUpdate, DeviceResponse,
    CredentialCreate, CredentialUpdate, CredentialResponse
)
from ..utils import backup_config
from .dependencies import get_current_active_user

router = APIRouter()

# Device routes
@router.get("/", response_model=list[DeviceResponse])
async def read_devices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Device).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{device_id}", response_model=DeviceResponse)
async def read_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    stmt = insert(Device).values(**device.model_dump()).returning(Device)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    stmt = update(Device).where(Device.id == device_id).values(**device.model_dump(exclude_unset=True)).returning(Device)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.commit()
    return device

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.execute(delete(Device).where(Device.id == device_id))
    await db.commit()

@router.post("/{device_id}/backup")
async def backup_device_config(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    cred_result = await db.execute(select(Credential).where(Credential.device_id == device_id))
    credential = cred_result.scalar_one_or_none()
    if credential is None:
        raise HTTPException(status_code=400, detail="No credential found for device")
    
    device_info = {
        "ip": device.mgmt_ip_id,
        "username": credential.username,
        "password": credential.password,
        "device_type": "cisco_ios",
        "port": credential.port
    }
    
    config = backup_config(device_info)
    if config is None:
        raise HTTPException(status_code=500, detail="Failed to backup device config")
    
    return {"message": "Backup successful", "config_size": len(config)}

# Credential routes
@router.get("/{device_id}/credentials", response_model=list[CredentialResponse])
async def read_credentials(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Credential).where(Credential.device_id == device_id))
    return result.scalars().all()

@router.post("/{device_id}/credentials", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    device_id: int,
    credential: CredentialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    data = credential.model_dump()
    data["device_id"] = device_id
    stmt = insert(Credential).values(**data).returning(Credential)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()

@router.put("/credentials/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: int,
    credential: CredentialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    stmt = update(Credential).where(Credential.id == credential_id).values(**credential.model_dump(exclude_unset=True)).returning(Credential)
    result = await db.execute(stmt)
    credential = result.scalar_one_or_none()
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    await db.commit()
    return credential

@router.delete("/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    result = await db.execute(select(Credential).where(Credential.id == credential_id))
    credential = result.scalar_one_or_none()
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    await db.execute(delete(Credential).where(Credential.id == credential_id))
    await db.commit()
