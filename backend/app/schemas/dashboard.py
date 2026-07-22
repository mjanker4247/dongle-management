from pydantic import BaseModel

from app.schemas.dongle import DongleRead


class DashboardStats(BaseModel):
    dongle_count: int
    pc_count: int
    location_count: int
    category_count: int
    test_module_count: int
    unassigned_dongles: list[DongleRead]
    recently_changed_dongles: list[DongleRead]
