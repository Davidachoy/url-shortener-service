from sqlalchemy import Column, Index, Integer, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from app.db.base_class import Base

class Click(Base):
    __tablename__ = "clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=False)

    __table_args__ = (
        Index("ix_clicks_url_id_created_at", "url_id", "created_at"),
    )
    
