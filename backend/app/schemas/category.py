from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class TestModuleBrief(ORMModel):
    id: int
    name: str
    sort_index: int
    is_active: bool


class CategoryModuleAssignment(BaseModel):
    test_module_ids: list[int]


class CategoryRead(CategoryBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
    module_count: int = 0


class CategoryDetail(CategoryRead):
    modules: list[TestModuleBrief] = []
