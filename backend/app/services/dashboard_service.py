from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Category, Dongle, DongleTestModule, Location, PC, TestModule
from app.schemas.dashboard import DashboardStats
from app.schemas.dongle import DongleRead, LocationBrief, PCBrief
from app.services.dongle_service import DongleService


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_stats(self) -> DashboardStats:
        dongle_count = self.db.scalar(select(func.count()).select_from(Dongle)) or 0
        pc_count = self.db.scalar(select(func.count()).select_from(PC)) or 0
        location_count = self.db.scalar(select(func.count()).select_from(Location)) or 0
        category_count = self.db.scalar(select(func.count()).select_from(Category)) or 0
        test_module_count = self.db.scalar(select(func.count()).select_from(TestModule)) or 0

        unassigned = list(
            self.db.scalars(
                select(Dongle)
                .options(
                    selectinload(Dongle.pc).selectinload(PC.location),
                    selectinload(Dongle.module_links),
                )
                .where(Dongle.pc_id.is_(None))
                .order_by(Dongle.dongle_id)
                .limit(20)
            ).all()
        )

        recent = list(
            self.db.scalars(
                select(Dongle)
                .options(
                    selectinload(Dongle.pc).selectinload(PC.location),
                    selectinload(Dongle.module_links),
                )
                .order_by(Dongle.updated_at.desc())
                .limit(10)
            ).all()
        )

        return DashboardStats(
            dongle_count=dongle_count,
            pc_count=pc_count,
            location_count=location_count,
            category_count=category_count,
            test_module_count=test_module_count,
            unassigned_dongles=[self._to_dongle_read(d) for d in unassigned],
            recently_changed_dongles=[self._to_dongle_read(d) for d in recent],
        )

    @staticmethod
    def _to_dongle_read(dongle: Dongle) -> DongleRead:
        pc_brief = None
        if dongle.pc:
            loc = None
            if dongle.pc.location:
                loc = LocationBrief(id=dongle.pc.location.id, name=dongle.pc.location.name)
            pc_brief = PCBrief(id=dongle.pc.id, name=dongle.pc.name, location=loc)
        return DongleRead(
            id=dongle.id,
            dongle_id=dongle.dongle_id,
            pc_id=dongle.pc_id,
            description=dongle.description,
            created_at=dongle.created_at,
            updated_at=dongle.updated_at,
            pc=pc_brief,
            enabled_module_count=DongleService.enabled_count(dongle),
        )
