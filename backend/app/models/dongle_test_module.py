from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.dongle import Dongle
    from app.models.test_module import TestModule


class DongleTestModule(Base, TimestampMixin):
    __tablename__ = "dongle_test_modules"
    __table_args__ = (
        UniqueConstraint("dongle_id", "test_module_id", name="uq_dongle_test_module"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dongle_id: Mapped[int] = mapped_column(
        ForeignKey("dongles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_module_id: Mapped[int] = mapped_column(
        ForeignKey("test_modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    dongle: Mapped[Dongle] = relationship("Dongle", back_populates="module_links")
    test_module: Mapped[TestModule] = relationship("TestModule", back_populates="dongle_links")
