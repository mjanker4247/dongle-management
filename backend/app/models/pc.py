from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.dongle import Dongle
    from app.models.location import Location


class PC(Base, TimestampMixin):
    __tablename__ = "pcs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    location_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    location: Mapped[Optional[Location]] = relationship("Location", back_populates="pcs")
    dongles: Mapped[list[Dongle]] = relationship("Dongle", back_populates="pc")

    def __repr__(self) -> str:
        return f"<PC id={self.id} name={self.name!r}>"
