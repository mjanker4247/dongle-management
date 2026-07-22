from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.serializers import dongle_to_detail, dongle_to_read
from app.db.session import get_db
from app.schemas.dongle import (
    AssignPCRequest,
    CompletenessResult,
    DongleCreate,
    DongleDetail,
    DongleModulesUpdate,
    DongleRead,
    DongleUpdate,
)
from app.services.dongle_service import DongleService

router = APIRouter(prefix="/dongles", tags=["dongles"])


@router.get("", response_model=list[DongleRead])
def list_dongles(
    search: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[DongleRead]:
    return [dongle_to_read(d) for d in DongleService(db).list(search=search)]


@router.post("", response_model=DongleRead, status_code=201)
def create_dongle(data: DongleCreate, db: Session = Depends(get_db)) -> DongleRead:
    return dongle_to_read(DongleService(db).create(data))


@router.get("/{dongle_id}", response_model=DongleDetail)
def get_dongle(dongle_id: int, db: Session = Depends(get_db)) -> DongleDetail:
    return dongle_to_detail(DongleService(db).get(dongle_id))


@router.put("/{dongle_id}", response_model=DongleRead)
def update_dongle(
    dongle_id: int, data: DongleUpdate, db: Session = Depends(get_db)
) -> DongleRead:
    return dongle_to_read(DongleService(db).update(dongle_id, data))


@router.delete("/{dongle_id}", status_code=204)
def delete_dongle(dongle_id: int, db: Session = Depends(get_db)) -> None:
    DongleService(db).delete(dongle_id)


@router.post("/{dongle_id}/assign-pc", response_model=DongleRead)
def assign_pc(
    dongle_id: int, data: AssignPCRequest, db: Session = Depends(get_db)
) -> DongleRead:
    return dongle_to_read(DongleService(db).assign_pc(dongle_id, data))


@router.post("/{dongle_id}/modules", response_model=DongleDetail)
def set_modules(
    dongle_id: int, data: DongleModulesUpdate, db: Session = Depends(get_db)
) -> DongleDetail:
    return dongle_to_detail(DongleService(db).set_modules(dongle_id, data))


@router.put("/{dongle_id}/modules", response_model=DongleDetail)
def update_modules(
    dongle_id: int, data: DongleModulesUpdate, db: Session = Depends(get_db)
) -> DongleDetail:
    return dongle_to_detail(DongleService(db).update_modules(dongle_id, data))


@router.get("/{dongle_id}/completeness", response_model=CompletenessResult)
def check_completeness(
    dongle_id: int,
    category_id: int | None = Query(None),
    category_name: str | None = Query(None),
    db: Session = Depends(get_db),
) -> CompletenessResult:
    return DongleService(db).check_completeness(
        dongle_id, category_id=category_id, category_name=category_name
    )
