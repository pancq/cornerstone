from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base

class DeviceLink(Base):
    __tablename__ = "device_links"
    
    id = Column(Integer, primary_key=True, index=True)
    source_device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    source_interface = Column(String(100))  # 如 GigabitEthernet0/1
    target_device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    target_interface = Column(String(100))
    link_type = Column(String(20), nullable=False, default="manual")  # lldp, cdp, manual, inferred
    confidence = Column(Integer, default=100)  # 置信度 0-100
    discovered_at = Column(DateTime)
    verified_at = Column(DateTime)
    note = Column(Text)
    
    # 关联关系
    source_device = relationship("Device", foreign_keys=[source_device_id], back_populates="source_links")
    target_device = relationship("Device", foreign_keys=[target_device_id], back_populates="target_links")
