from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.test_module import TestModule


class CategoryTestModule(Base):
    __tablename__ = "category_test_modules"
    __table_args__ = (
        UniqueConstraint("category_id", "test_module_id", name="uq_category_test_module"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_module_id: Mapped[int] = mapped_column(
        ForeignKey("test_modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    category: Mapped[Category] = relationship("Category", back_populates="module_links")
    test_module: Mapped[TestModule] = relationship("TestModule", back_populates="category_links")
