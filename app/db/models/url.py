from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.sql import func
from app.db.base_class import Base

class URL(Base):
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(10), unique=True, index=True, nullable=False)
    target_url = Column(String(2048), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    