from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.serializers import pc_to_detail, pc_to_read
from app.db.session import get_db
from app.schemas.pc import PCCreate, PCDetail, PCRead, PCUpdate
from app.services.pc_service import PCService

router = APIRouter(prefix="/pcs", tags=["pcs"])


@router.get("", response_model=list[PCRead])
def list_pcs(db: Session = Depends(get_db)) -> list[PCRead]:
    return [pc_to_read(pc) for pc in PCService(db).list()]


@router.post("", response_model=PCRead, status_code=201)
def create_pc(data: PCCreate, db: Session = Depends(get_db)) -> PCRead:
    return pc_to_read(PCService(db).create(data))


@router.get("/{pc_id}", response_model=PCDetail)
def get_pc(pc_id: int, db: Session = Depends(get_db)) -> PCDetail:
    return pc_to_detail(PCService(db).get(pc_id))


@router.put("/{pc_id}", response_model=PCRead)
def update_pc(pc_id: int, data: PCUpdate, db: Session = Depends(get_db)) -> PCRead:
    return pc_to_read(PCService(db).update(pc_id, data))


@router.delete("/{pc_id}", status_code=204)
def delete_pc(pc_id: int, db: Session = Depends(get_db)) -> None:
    PCService(db).delete(pc_id)
