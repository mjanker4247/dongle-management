from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.category_test_module import CategoryTestModule
    from app.models.dongle_test_module import DongleTestModule


class TestModule(Base, TimestampMixin):
    __tablename__ = "test_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    category_links: Mapped[list[CategoryTestModule]] = relationship(
        "CategoryTestModule",
        back_populates="test_module",
        cascade="all, delete-orphan",
    )
    dongle_links: Mapped[list[DongleTestModule]] = relationship(
        "DongleTestModule",
        back_populates="test_module",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TestModule id={self.id} name={self.name!r}>"
