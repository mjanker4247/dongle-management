from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.dongle_test_module import DongleTestModule
    from app.models.pc import PC


class Dongle(Base, TimestampMixin):
    __tablename__ = "dongles"

    id: Mapped[int] = mapped_column(primary_key=True)
    dongle_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    pc_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pcs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    pc: Mapped[Optional[PC]] = relationship("PC", back_populates="dongles")
    module_links: Mapped[list[DongleTestModule]] = relationship(
        "DongleTestModule",
        back_populates="dongle",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Dongle id={self.id} dongle_id={self.dongle_id!r}>"
