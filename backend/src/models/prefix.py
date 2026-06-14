from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from ..database import Base

class Prefix(Base):
    __tablename__ = "prefixes"
    
    id = Column(Integer, primary_key=True, index=True)
    aggregate_id = Column(Integer, ForeignKey("aggregates.id"))
    network = Column(String(50), nullable=False)  # CIDR格式
    site_id = Column(Integer, ForeignKey("sites.id"))
    vlan = Column(String(20))
    usage = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
