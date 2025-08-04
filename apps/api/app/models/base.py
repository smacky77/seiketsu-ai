"""
Base model classes for Seiketsu AI API
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class BaseModel(Base):
    """Base model with common attributes"""
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TenantMixin:
    """Mixin for multi-tenant models"""
    organization_id = Column(String, nullable=False, index=True)


class AuditMixin:
    """Mixin for audit trail"""
    created_by = Column(String)
    updated_by = Column(String)  
    version = Column(Integer, default=1)
    metadata = Column(Text)  # JSON field for additional data