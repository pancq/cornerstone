from pydantic import BaseModel
from datetime import datetime

class CredentialCreate(BaseModel):
    name: str
    device_id: int | None = None
    protocol: str = "ssh"
    port: int = 22
    username: str
    password: str
    enable_password: str | None = None
    auth_type: str = "password"
    private_key: str | None = None
    jump_host: str | None = None
    jump_port: int = 22
    jump_username: str | None = None
    jump_password: str | None = None
    description: str | None = None

class CredentialUpdate(BaseModel):
    name: str | None = None
    device_id: int | None = None
    protocol: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    enable_password: str | None = None
    auth_type: str | None = None
    private_key: str | None = None
    jump_host: str | None = None
    jump_port: int | None = None
    jump_username: str | None = None
    jump_password: str | None = None
    description: str | None = None

class CredentialResponse(BaseModel):
    id: int
    name: str
    device_id: int | None
    protocol: str
    port: int
    username: str
    password: str
    enable_password: str | None
    auth_type: str
    private_key: str | None
    jump_host: str | None
    jump_port: int
    jump_username: str | None
    jump_password: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True