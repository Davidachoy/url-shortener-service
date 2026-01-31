from pydantic import BaseModel, HttpUrl, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class URLCreate(BaseModel):
    url: HttpUrl = Field(...,max_length=2048, description="The URL to shorten")
    custom_code: Optional[str] = Field(None, min_length=3, max_length=20, description="Custom code for the URL", pattern=r'^[a-zA-Z0-9\-]+$')   
    expires_at: Optional[datetime] = Field(None, description="Expiration date for the URL")

    @field_validator('expires_at') 
    @classmethod
    def validate_expires_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            now = datetime.now(v.tzinfo) if v.tzinfo else datetime.now()
            if v <= now:
                raise ValueError("Expiration date must be in the future")
        return v

class URLResponse(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    target_url: HttpUrl
    short_url: str = Field(..., description="The short URL")
    created_at: datetime
    clicks: int = Field(0, description="The number of clicks on the URL")

class URLInDB(URLResponse):
    pass
