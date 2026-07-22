from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.serializers import test_module_to_read
from app.db.session import get_db
from app.schemas.test_module import (
    ReorderRequest,
    TestModuleCreate,
    TestModuleRead,
    TestModuleUpdate,
)
from app.services.test_module_service import TestModuleService

router = APIRouter(prefix="/test-modules", tags=["test-modules"])


@router.get("", response_model=list[TestModuleRead])
def list_test_modules(
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    is_active: bool | None = Query(None),
    order: str = Query("manual", pattern="^(manual|alpha)$"),
    db: Session = Depends(get_db),
) -> list[TestModuleRead]:
    modules = TestModuleService(db).list(
        search=search, category_id=category_id, is_active=is_active, order=order
    )
    return [test_module_to_read(m) for m in modules]


@router.put("/reorder", response_model=list[TestModuleRead])
def reorder_test_modules(
    data: ReorderRequest, db: Session = Depends(get_db)
) -> list[TestModuleRead]:
    return [test_module_to_read(m) for m in TestModuleService(db).reorder(data)]


@router.post("", response_model=TestModuleRead, status_code=201)
def create_test_module(
    data: TestModuleCreate, db: Session = Depends(get_db)
) -> TestModuleRead:
    return test_module_to_read(TestModuleService(db).create(data))


@router.get("/{module_id}", response_model=TestModuleRead)
def get_test_module(module_id: int, db: Session = Depends(get_db)) -> TestModuleRead:
    return test_module_to_read(TestModuleService(db).get(module_id))


@router.put("/{module_id}", response_model=TestModuleRead)
def update_test_module(
    module_id: int, data: TestModuleUpdate, db: Session = Depends(get_db)
) -> TestModuleRead:
    return test_module_to_read(TestModuleService(db).update(module_id, data))


@router.delete("/{module_id}", status_code=204)
def delete_test_module(module_id: int, db: Session = Depends(get_db)) -> None:
    TestModuleService(db).delete(module_id)
