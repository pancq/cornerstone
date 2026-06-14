from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from ..database import Base


class CircuitChange(Base):
    __tablename__ = "circuit_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    circuit_id = Column(Integer, ForeignKey("circuits.id"), nullable=False)
    change_type = Column(String(50), nullable=False)  # create, update, delete
    field_name = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    operator = Column(String(50))
    remark = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())