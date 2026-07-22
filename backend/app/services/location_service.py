from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Location, PC
from app.schemas.location import LocationCreate, LocationUpdate
from app.services.naming import normalize_name


class LocationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Location]:
        return list(self.db.scalars(select(Location).order_by(Location.name)).all())

    def get(self, location_id: int) -> Location:
        location = self.db.get(Location, location_id)
        if not location:
            raise NotFoundError(f"Location {location_id} not found")
        return location

    def get_detail_counts(self, location: Location) -> tuple[int, int]:
        pcs = list(
            self.db.scalars(
                select(PC).options(selectinload(PC.dongles)).where(PC.location_id == location.id)
            ).all()
        )
        pc_count = len(pcs)
        dongle_count = sum(len(pc.dongles) for pc in pcs)
        return pc_count, dongle_count

    def _ensure_unique_name(self, name: str, exclude_id: int | None = None) -> str:
        name = normalize_name(name)
        if not name:
            raise ConflictError("Location name cannot be empty")
        stmt = select(Location).where(func.lower(Location.name) == name.casefold())
        if exclude_id is not None:
            stmt = stmt.where(Location.id != exclude_id)
        existing = self.db.scalars(stmt).first()
        if existing:
            raise ConflictError(f"Location name '{name}' already exists")
        return name

    def create(self, data: LocationCreate) -> Location:
        name = self._ensure_unique_name(data.name)
        location = Location(name=name, description=data.description)
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def update(self, location_id: int, data: LocationUpdate) -> Location:
        location = self.get(location_id)
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload and payload["name"] is not None:
            location.name = self._ensure_unique_name(payload["name"], exclude_id=location_id)
        if "description" in payload:
            location.description = payload["description"]
        self.db.commit()
        self.db.refresh(location)
        return location

    def delete(self, location_id: int) -> None:
        location = self.get(location_id)
        # Unassign PCs rather than cascading delete of PCs/dongles
        for pc in list(
            self.db.scalars(select(PC).where(PC.location_id == location_id)).all()
        ):
            pc.location_id = None
        self.db.delete(location)
        self.db.commit()
