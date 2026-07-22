from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Category, CategoryTestModule, Dongle, DongleTestModule, PC, TestModule
from app.schemas.dongle import (
    AssignPCRequest,
    CompletenessResult,
    DongleCreate,
    DongleModulesUpdate,
    DongleUpdate,
    ModuleNameInfo,
)
from app.services.naming import normalize_name


class DongleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(self):
        return select(Dongle).options(
            selectinload(Dongle.pc).selectinload(PC.location),
            selectinload(Dongle.module_links).selectinload(DongleTestModule.test_module),
        )

    def list(self, search: str | None = None) -> list[Dongle]:
        stmt = self._base_query().order_by(Dongle.dongle_id)
        dongles = list(self.db.scalars(stmt).all())
        if not search:
            return dongles
        q = search.casefold().strip()
        filtered: list[Dongle] = []
        for d in dongles:
            haystacks = [d.dongle_id]
            if d.pc:
                haystacks.append(d.pc.name)
                if d.pc.location:
                    haystacks.append(d.pc.location.name)
            if any(q in h.casefold() for h in haystacks):
                filtered.append(d)
        return filtered

    def get(self, dongle_pk: int) -> Dongle:
        dongle = self.db.scalars(self._base_query().where(Dongle.id == dongle_pk)).first()
        if not dongle:
            raise NotFoundError(f"Dongle {dongle_pk} not found")
        return dongle

    def get_by_dongle_id(self, dongle_id: str) -> Dongle | None:
        dongle_id = normalize_name(dongle_id)
        return self.db.scalars(
            self._base_query().where(func.lower(Dongle.dongle_id) == dongle_id.casefold())
        ).first()

    def _ensure_unique_dongle_id(self, dongle_id: str, exclude_id: int | None = None) -> str:
        dongle_id = normalize_name(dongle_id)
        if not dongle_id:
            raise ConflictError("Dongle ID cannot be empty")
        stmt = select(Dongle).where(func.lower(Dongle.dongle_id) == dongle_id.casefold())
        if exclude_id is not None:
            stmt = stmt.where(Dongle.id != exclude_id)
        if self.db.scalars(stmt).first():
            raise ConflictError(f"Dongle ID '{dongle_id}' already exists")
        return dongle_id

    def _validate_pc(self, pc_id: int | None) -> None:
        if pc_id is None:
            return
        if not self.db.get(PC, pc_id):
            raise NotFoundError(f"PC {pc_id} not found")

    def create(self, data: DongleCreate) -> Dongle:
        dongle_id = self._ensure_unique_dongle_id(data.dongle_id)
        self._validate_pc(data.pc_id)
        dongle = Dongle(
            dongle_id=dongle_id,
            pc_id=data.pc_id,
            description=data.description,
        )
        self.db.add(dongle)
        self.db.commit()
        return self.get(dongle.id)

    def update(self, dongle_pk: int, data: DongleUpdate) -> Dongle:
        dongle = self.get(dongle_pk)
        payload = data.model_dump(exclude_unset=True)
        if "dongle_id" in payload and payload["dongle_id"] is not None:
            dongle.dongle_id = self._ensure_unique_dongle_id(payload["dongle_id"], exclude_id=dongle_pk)
        if "pc_id" in payload:
            self._validate_pc(payload["pc_id"])
            dongle.pc_id = payload["pc_id"]
        if "description" in payload:
            dongle.description = payload["description"]
        self.db.commit()
        return self.get(dongle_pk)

    def delete(self, dongle_pk: int) -> None:
        dongle = self.get(dongle_pk)
        self.db.delete(dongle)
        self.db.commit()

    def assign_pc(self, dongle_pk: int, data: AssignPCRequest) -> Dongle:
        """Assign dongle to a PC (or unassign if pc_id is None).

        A dongle can only be on one PC at a time — enforced by single nullable pc_id FK.
        """
        dongle = self.get(dongle_pk)
        self._validate_pc(data.pc_id)
        dongle.pc_id = data.pc_id
        self.db.commit()
        return self.get(dongle_pk)

    def set_modules(self, dongle_pk: int, data: DongleModulesUpdate) -> Dongle:
        dongle = self.get(dongle_pk)
        existing = {link.test_module_id: link for link in dongle.module_links}
        seen: set[int] = set()
        for item in data.modules:
            module = self.db.get(TestModule, item.test_module_id)
            if not module:
                raise NotFoundError(f"Test module {item.test_module_id} not found")
            seen.add(item.test_module_id)
            if item.test_module_id in existing:
                existing[item.test_module_id].enabled = item.enabled
            else:
                self.db.add(
                    DongleTestModule(
                        dongle_id=dongle.id,
                        test_module_id=item.test_module_id,
                        enabled=item.enabled,
                    )
                )
        # Remove links not present in payload (explicit replace semantics for listed set)
        # Keep only modules mentioned; for partial updates callers should include all intended state.
        for module_id, link in list(existing.items()):
            if module_id not in seen:
                self.db.delete(link)
        self.db.commit()
        return self.get(dongle_pk)

    def update_modules(self, dongle_pk: int, data: DongleModulesUpdate) -> Dongle:
        """Upsert enable/disable without removing unspecified modules."""
        dongle = self.get(dongle_pk)
        existing = {link.test_module_id: link for link in dongle.module_links}
        for item in data.modules:
            module = self.db.get(TestModule, item.test_module_id)
            if not module:
                raise NotFoundError(f"Test module {item.test_module_id} not found")
            if item.test_module_id in existing:
                existing[item.test_module_id].enabled = item.enabled
            else:
                self.db.add(
                    DongleTestModule(
                        dongle_id=dongle.id,
                        test_module_id=item.test_module_id,
                        enabled=item.enabled,
                    )
                )
        self.db.commit()
        return self.get(dongle_pk)

    def check_completeness(
        self,
        dongle_pk: int,
        category_id: int | None = None,
        category_name: str | None = None,
    ) -> CompletenessResult:
        dongle = self.get(dongle_pk)

        if category_id is not None:
            category = self.db.get(Category, category_id)
            if not category:
                raise NotFoundError(f"Category {category_id} not found")
        elif category_name:
            name = normalize_name(category_name)
            category = self.db.scalars(
                select(Category).where(func.lower(Category.name) == name.casefold())
            ).first()
            if not category:
                raise NotFoundError(f"Category '{category_name}' not found")
        else:
            raise ConflictError("category_id or category_name is required")

        required_links = list(
            self.db.scalars(
                select(CategoryTestModule)
                .options(selectinload(CategoryTestModule.test_module))
                .where(CategoryTestModule.category_id == category.id)
            ).all()
        )
        required_modules = [
            link.test_module
            for link in required_links
            if link.test_module is not None and link.test_module.is_active
        ]
        required_modules.sort(key=lambda m: (m.sort_index, m.name.casefold()))

        enabled_ids = {
            link.test_module_id
            for link in dongle.module_links
            if link.enabled
        }
        enabled_modules = [
            link.test_module
            for link in dongle.module_links
            if link.enabled and link.test_module is not None
        ]

        required_ids = {m.id for m in required_modules}
        missing = [m for m in required_modules if m.id not in enabled_ids]
        extra = [m for m in enabled_modules if m.id not in required_ids]
        extra.sort(key=lambda m: (m.sort_index, m.name.casefold()))

        enabled_required = len(required_ids & enabled_ids)

        return CompletenessResult(
            dongle_id=dongle.dongle_id,
            category_id=category.id,
            category=category.name,
            total_required_modules=len(required_modules),
            enabled_required_modules=enabled_required,
            missing_modules=[
                ModuleNameInfo(id=m.id, name=m.name, sort_index=m.sort_index) for m in missing
            ],
            extra_enabled_modules=[
                ModuleNameInfo(id=m.id, name=m.name, sort_index=m.sort_index) for m in extra
            ],
            is_complete=len(missing) == 0,
        )

    @staticmethod
    def enabled_count(dongle: Dongle) -> int:
        return sum(1 for link in dongle.module_links if link.enabled)
