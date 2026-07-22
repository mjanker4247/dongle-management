from __future__ import annotations

import csv
import io
from typing import Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, Dongle, PC, TestModule
from app.schemas.import_schema import ImportResult, ImportRowError
from app.services.naming import normalize_name


def parse_lines(text: str) -> list[str]:
    """Parse paste/CSV text into non-empty trimmed lines (first column if CSV)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if not row:
            continue
        value = normalize_name(row[0])
        # Skip header-like first row for common column names
        if not lines and value.casefold() in {
            "name",
            "pc",
            "pc_name",
            "pc name",
            "dongle_id",
            "dongle id",
            "dongle",
            "category",
            "category_name",
            "module",
            "module_name",
            "test_module",
            "test module",
        }:
            continue
        if value:
            lines.append(value)
    return lines


def parse_csv_upload(content: bytes) -> list[str]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    return parse_lines(text)


class ImportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _upsert_by_name(
        self,
        values: list[str],
        *,
        find_existing: Callable[[str], object | None],
        create: Callable[[str], None],
        update: Callable[[object, str], bool],
        preview_only: bool = False,
    ) -> ImportResult:
        result = ImportResult()
        seen_in_batch: set[str] = set()

        for idx, raw in enumerate(values, start=1):
            name = normalize_name(raw)
            if not name:
                result.errors.append(
                    ImportRowError(row=idx, field="name", message="Empty name", value=raw)
                )
                continue

            key = name.casefold()
            if key in seen_in_batch:
                result.skipped += 1
                result.details.append({"row": idx, "name": name, "action": "skipped_duplicate_in_batch"})
                continue
            seen_in_batch.add(key)

            existing = find_existing(name)
            if existing is None:
                if not preview_only:
                    create(name)
                result.created += 1
                result.details.append({"row": idx, "name": name, "action": "created"})
            else:
                changed = update(existing, name)
                if changed:
                    if not preview_only:
                        pass  # already mutated
                    result.updated += 1
                    result.details.append({"row": idx, "name": name, "action": "updated"})
                else:
                    result.skipped += 1
                    result.details.append({"row": idx, "name": name, "action": "skipped_unchanged"})

        if not preview_only:
            self.db.commit()
        else:
            self.db.rollback()
        return result

    def import_pcs(self, values: list[str], preview_only: bool = False) -> ImportResult:
        def find(name: str) -> PC | None:
            return self.db.scalars(
                select(PC).where(func.lower(PC.name) == name.casefold())
            ).first()

        def create(name: str) -> None:
            self.db.add(PC(name=name))

        def update(existing: PC, name: str) -> bool:
            # Preserve casing updates if different
            if existing.name != name:
                existing.name = name
                return True
            return False

        return self._upsert_by_name(
            values, find_existing=find, create=create, update=update, preview_only=preview_only
        )

    def import_dongles(self, values: list[str], preview_only: bool = False) -> ImportResult:
        def find(name: str) -> Dongle | None:
            return self.db.scalars(
                select(Dongle).where(func.lower(Dongle.dongle_id) == name.casefold())
            ).first()

        def create(name: str) -> None:
            self.db.add(Dongle(dongle_id=name))

        def update(existing: Dongle, name: str) -> bool:
            if existing.dongle_id != name:
                existing.dongle_id = name
                return True
            return False

        return self._upsert_by_name(
            values, find_existing=find, create=create, update=update, preview_only=preview_only
        )

    def import_categories(self, values: list[str], preview_only: bool = False) -> ImportResult:
        def find(name: str) -> Category | None:
            return self.db.scalars(
                select(Category).where(func.lower(Category.name) == name.casefold())
            ).first()

        def create(name: str) -> None:
            self.db.add(Category(name=name))

        def update(existing: Category, name: str) -> bool:
            if existing.name != name:
                existing.name = name
                return True
            return False

        return self._upsert_by_name(
            values, find_existing=find, create=create, update=update, preview_only=preview_only
        )

    def import_test_modules(self, values: list[str], preview_only: bool = False) -> ImportResult:
        max_sort = self.db.scalar(select(func.max(TestModule.sort_index))) or 0
        next_sort = max_sort + 1

        def find(name: str) -> TestModule | None:
            return self.db.scalars(
                select(TestModule).where(func.lower(TestModule.name) == name.casefold())
            ).first()

        def create(name: str) -> None:
            nonlocal next_sort
            self.db.add(TestModule(name=name, sort_index=next_sort, is_active=True))
            next_sort += 1

        def update(existing: TestModule, name: str) -> bool:
            if existing.name != name:
                existing.name = name
                return True
            return False

        return self._upsert_by_name(
            values, find_existing=find, create=create, update=update, preview_only=preview_only
        )
