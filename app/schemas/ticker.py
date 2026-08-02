from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TickerBase(BaseModel):
    symbol: str = Field(..., json_schema_extra={"example": "AMD"}, description="Stock ticker symbol")
    company_name: str = Field(..., json_schema_extra={"example": "Advanced Micro Devices, Inc."}, description="Company name")

class TickerCreate(TickerBase):
    """Schema used when adding a new ticker to track"""

class TickerResponse(TickerBase):
    """Schema returned to the client"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool = True
    created_at: datetime