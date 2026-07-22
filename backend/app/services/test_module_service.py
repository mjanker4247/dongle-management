from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models import CategoryTestModule, TestModule
from app.schemas.test_module import ReorderRequest, TestModuleCreate, TestModuleUpdate
from app.services.naming import normalize_name


class TestModuleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        search: str | None = None,
        category_id: int | None = None,
        is_active: bool | None = None,
        order: str = "manual",
    ) -> list[TestModule]:
        stmt = select(TestModule).options(
            selectinload(TestModule.category_links).selectinload(CategoryTestModule.category)
        )
        if is_active is not None:
            stmt = stmt.where(TestModule.is_active.is_(is_active))
        if order == "alpha":
            stmt = stmt.order_by(func.lower(TestModule.name))
        else:
            stmt = stmt.order_by(TestModule.sort_index, func.lower(TestModule.name))

        modules = list(self.db.scalars(stmt).all())

        if category_id is not None:
            modules = [
                m
                for m in modules
                if any(link.category_id == category_id for link in m.category_links)
            ]
        if search:
            q = search.casefold().strip()
            modules = [
                m
                for m in modules
                if q in m.name.casefold()
                or any(q in link.category.name.casefold() for link in m.category_links if link.category)
            ]
        return modules

    def get(self, module_id: int) -> TestModule:
        module = self.db.scalars(
            select(TestModule)
            .options(
                selectinload(TestModule.category_links).selectinload(CategoryTestModule.category)
            )
            .where(TestModule.id == module_id)
        ).first()
        if not module:
            raise NotFoundError(f"Test module {module_id} not found")
        return module

    def _ensure_unique_name(self, name: str, exclude_id: int | None = None) -> str:
        name = normalize_name(name)
        if not name:
            raise ConflictError("Test module name cannot be empty")
        stmt = select(TestModule).where(func.lower(TestModule.name) == name.casefold())
        if exclude_id is not None:
            stmt = stmt.where(TestModule.id != exclude_id)
        if self.db.scalars(stmt).first():
            raise ConflictError(f"Test module name '{name}' already exists")
        return name

    def _next_sort_index(self) -> int:
        current = self.db.scalar(select(func.max(TestModule.sort_index)))
        return (current or 0) + 1

    def create(self, data: TestModuleCreate) -> TestModule:
        name = self._ensure_unique_name(data.name)
        sort_index = data.sort_index if data.sort_index is not None else self._next_sort_index()
        module = TestModule(
            name=name,
            description=data.description,
            sort_index=sort_index,
            is_active=data.is_active,
        )
        self.db.add(module)
        self.db.commit()
        return self.get(module.id)

    def update(self, module_id: int, data: TestModuleUpdate) -> TestModule:
        module = self.get(module_id)
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload and payload["name"] is not None:
            module.name = self._ensure_unique_name(payload["name"], exclude_id=module_id)
        if "description" in payload:
            module.description = payload["description"]
        if "sort_index" in payload and payload["sort_index"] is not None:
            module.sort_index = payload["sort_index"]
        if "is_active" in payload and payload["is_active"] is not None:
            module.is_active = payload["is_active"]
        self.db.commit()
        return self.get(module_id)

    def delete(self, module_id: int) -> None:
        module = self.get(module_id)
        self.db.delete(module)
        self.db.commit()

    def reorder(self, data: ReorderRequest) -> list[TestModule]:
        ids = [item.id for item in data.items]
        modules = {
            m.id: m
            for m in self.db.scalars(select(TestModule).where(TestModule.id.in_(ids))).all()
        }
        for item in data.items:
            if item.id not in modules:
                raise NotFoundError(f"Test module {item.id} not found")
            modules[item.id].sort_index = item.sort_index
        self.db.commit()
        return self.list(order="manual")
