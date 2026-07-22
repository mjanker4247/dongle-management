from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PCBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    location_id: Optional[int] = None
    description: Optional[str] = None


class PCCreate(PCBase):
    pass


class PCUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location_id: Optional[int] = None
    description: Optional[str] = None


class LocationBrief(ORMModel):
    id: int
    name: str


class PCRead(PCBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
    location: Optional[LocationBrief] = None
    dongle_count: int = 0


class DongleBrief(ORMModel):
    id: int
    dongle_id: str


class PCDetail(PCRead):
    dongles: list[DongleBrief] = []
