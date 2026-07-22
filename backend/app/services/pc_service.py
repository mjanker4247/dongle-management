from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Location, PC
from app.schemas.pc import PCCreate, PCUpdate
from app.services.naming import normalize_name


class PCService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[PC]:
        return list(
            self.db.scalars(
                select(PC)
                .options(selectinload(PC.location), selectinload(PC.dongles))
                .order_by(PC.name)
            ).all()
        )

    def get(self, pc_id: int) -> PC:
        pc = self.db.scalars(
            select(PC)
            .options(selectinload(PC.location), selectinload(PC.dongles))
            .where(PC.id == pc_id)
        ).first()
        if not pc:
            raise NotFoundError(f"PC {pc_id} not found")
        return pc

    def get_by_name(self, name: str) -> PC | None:
        name = normalize_name(name)
        return self.db.scalars(
            select(PC)
            .options(selectinload(PC.location), selectinload(PC.dongles))
            .where(func.lower(PC.name) == name.casefold())
        ).first()

    def _ensure_unique_name(self, name: str, exclude_id: int | None = None) -> str:
        name = normalize_name(name)
        if not name:
            raise ConflictError("PC name cannot be empty")
        stmt = select(PC).where(func.lower(PC.name) == name.casefold())
        if exclude_id is not None:
            stmt = stmt.where(PC.id != exclude_id)
        if self.db.scalars(stmt).first():
            raise ConflictError(f"PC name '{name}' already exists")
        return name

    def _validate_location(self, location_id: int | None) -> None:
        if location_id is None:
            return
        if not self.db.get(Location, location_id):
            raise NotFoundError(f"Location {location_id} not found")

    def create(self, data: PCCreate) -> PC:
        name = self._ensure_unique_name(data.name)
        self._validate_location(data.location_id)
        pc = PC(name=name, location_id=data.location_id, description=data.description)
        self.db.add(pc)
        self.db.commit()
        return self.get(pc.id)

    def update(self, pc_id: int, data: PCUpdate) -> PC:
        pc = self.get(pc_id)
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload and payload["name"] is not None:
            pc.name = self._ensure_unique_name(payload["name"], exclude_id=pc_id)
        if "location_id" in payload:
            self._validate_location(payload["location_id"])
            pc.location_id = payload["location_id"]
        if "description" in payload:
            pc.description = payload["description"]
        self.db.commit()
        return self.get(pc_id)

    def delete(self, pc_id: int) -> None:
        pc = self.get(pc_id)
        for dongle in list(pc.dongles):
            dongle.pc_id = None
        self.db.delete(pc)
        self.db.commit()
