from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.serializers import category_to_detail, category_to_read
from app.db.session import get_db
from app.schemas.category import (
    CategoryCreate,
    CategoryDetail,
    CategoryModuleAssignment,
    CategoryRead,
    CategoryUpdate,
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryRead]:
    return [category_to_read(c) for c in CategoryService(db).list()]


@router.post("", response_model=CategoryRead, status_code=201)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)) -> CategoryRead:
    return category_to_read(CategoryService(db).create(data))


@router.get("/{category_id}", response_model=CategoryDetail)
def get_category(
    category_id: int,
    alphabetical: bool = Query(False),
    db: Session = Depends(get_db),
) -> CategoryDetail:
    return category_to_detail(CategoryService(db).get(category_id), alphabetical=alphabetical)


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)
) -> CategoryRead:
    return category_to_read(CategoryService(db).update(category_id, data))


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    CategoryService(db).delete(category_id)


@router.put("/{category_id}/modules", response_model=CategoryDetail)
def set_category_modules(
    category_id: int,
    data: CategoryModuleAssignment,
    db: Session = Depends(get_db),
) -> CategoryDetail:
    return category_to_detail(CategoryService(db).set_modules(category_id, data))
