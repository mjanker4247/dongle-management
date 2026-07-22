from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DongleBase(BaseModel):
    dongle_id: str = Field(..., min_length=1, max_length=255)
    pc_id: Optional[int] = None
    description: Optional[str] = None


class DongleCreate(DongleBase):
    pass


class DongleUpdate(BaseModel):
    dongle_id: Optional[str] = Field(None, min_length=1, max_length=255)
    pc_id: Optional[int] = None
    description: Optional[str] = None


class AssignPCRequest(BaseModel):
    pc_id: Optional[int] = None


class LocationBrief(ORMModel):
    id: int
    name: str


class PCBrief(ORMModel):
    id: int
    name: str
    location: Optional[LocationBrief] = None


class TestModuleBrief(ORMModel):
    id: int
    name: str
    sort_index: int
    is_active: bool


class DongleModuleLink(ORMModel):
    test_module_id: int
    enabled: bool
    test_module: Optional[TestModuleBrief] = None


class DongleModulesUpdate(BaseModel):
    modules: list[DongleModuleLink]


class DongleRead(DongleBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
    pc: Optional[PCBrief] = None
    enabled_module_count: int = 0


class DongleDetail(DongleRead):
    modules: list[DongleModuleLink] = []


class ModuleNameInfo(BaseModel):
    id: int
    name: str
    sort_index: int


class CompletenessResult(BaseModel):
    dongle_id: str
    category_id: int
    category: str
    total_required_modules: int
    enabled_required_modules: int
    missing_modules: list[ModuleNameInfo]
    extra_enabled_modules: list[ModuleNameInfo]
    is_complete: bool
