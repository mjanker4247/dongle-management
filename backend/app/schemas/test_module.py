from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TestModuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sort_index: Optional[int] = None
    is_active: bool = True


class TestModuleCreate(TestModuleBase):
    pass


class TestModuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sort_index: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryBrief(ORMModel):
    id: int
    name: str


class TestModuleRead(TestModuleBase, ORMModel):
    id: int
    sort_index: int
    created_at: datetime
    updated_at: datetime
    categories: list[CategoryBrief] = []


class ReorderItem(BaseModel):
    id: int
    sort_index: int


class ReorderRequest(BaseModel):
    items: list[ReorderItem]
