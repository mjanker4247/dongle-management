from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Category, CategoryTestModule, TestModule
from app.schemas.category import CategoryCreate, CategoryModuleAssignment, CategoryUpdate
from app.services.naming import normalize_name


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Category]:
        return list(
            self.db.scalars(
                select(Category)
                .options(selectinload(Category.module_links))
                .order_by(Category.name)
            ).all()
        )

    def get(self, category_id: int) -> Category:
        category = self.db.scalars(
            select(Category)
            .options(
                selectinload(Category.module_links).selectinload(CategoryTestModule.test_module)
            )
            .where(Category.id == category_id)
        ).first()
        if not category:
            raise NotFoundError(f"Category {category_id} not found")
        return category

    def _ensure_unique_name(self, name: str, exclude_id: int | None = None) -> str:
        name = normalize_name(name)
        if not name:
            raise ConflictError("Category name cannot be empty")
        stmt = select(Category).where(func.lower(Category.name) == name.casefold())
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        if self.db.scalars(stmt).first():
            raise ConflictError(f"Category name '{name}' already exists")
        return name

    def create(self, data: CategoryCreate) -> Category:
        name = self._ensure_unique_name(data.name)
        category = Category(name=name, description=data.description)
        self.db.add(category)
        self.db.commit()
        return self.get(category.id)

    def update(self, category_id: int, data: CategoryUpdate) -> Category:
        category = self.get(category_id)
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload and payload["name"] is not None:
            category.name = self._ensure_unique_name(payload["name"], exclude_id=category_id)
        if "description" in payload:
            category.description = payload["description"]
        self.db.commit()
        return self.get(category_id)

    def delete(self, category_id: int) -> None:
        category = self.get(category_id)
        self.db.delete(category)
        self.db.commit()

    def set_modules(self, category_id: int, data: CategoryModuleAssignment) -> Category:
        category = self.get(category_id)
        existing = {link.test_module_id: link for link in category.module_links}
        seen: set[int] = set()
        for module_id in data.test_module_ids:
            module = self.db.get(TestModule, module_id)
            if not module:
                raise NotFoundError(f"Test module {module_id} not found")
            seen.add(module_id)
            if module_id not in existing:
                self.db.add(
                    CategoryTestModule(category_id=category.id, test_module_id=module_id)
                )
        for module_id, link in list(existing.items()):
            if module_id not in seen:
                self.db.delete(link)
        self.db.commit()
        return self.get(category_id)

    def get_modules_sorted(
        self, category: Category, alphabetical: bool = False
    ) -> list[TestModule]:
        modules = [
            link.test_module
            for link in category.module_links
            if link.test_module is not None
        ]
        if alphabetical:
            modules.sort(key=lambda m: m.name.casefold())
        else:
            modules.sort(key=lambda m: (m.sort_index, m.name.casefold()))
        return modules
