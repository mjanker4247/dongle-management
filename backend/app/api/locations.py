from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.serializers import location_to_detail, location_to_read
from app.db.session import get_db
from app.schemas.location import LocationCreate, LocationDetail, LocationRead, LocationUpdate
from app.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationDetail])
def list_locations(db: Session = Depends(get_db)) -> list[LocationDetail]:
    service = LocationService(db)
    results: list[LocationDetail] = []
    for loc in service.list():
        pc_count, dongle_count = service.get_detail_counts(loc)
        results.append(location_to_detail(loc, pc_count, dongle_count))
    return results


@router.post("", response_model=LocationRead, status_code=201)
def create_location(data: LocationCreate, db: Session = Depends(get_db)) -> LocationRead:
    return location_to_read(LocationService(db).create(data))


@router.get("/{location_id}", response_model=LocationDetail)
def get_location(location_id: int, db: Session = Depends(get_db)) -> LocationDetail:
    service = LocationService(db)
    loc = service.get(location_id)
    pc_count, dongle_count = service.get_detail_counts(loc)
    return location_to_detail(loc, pc_count, dongle_count)


@router.put("/{location_id}", response_model=LocationRead)
def update_location(
    location_id: int, data: LocationUpdate, db: Session = Depends(get_db)
) -> LocationRead:
    return location_to_read(LocationService(db).update(location_id, data))


@router.delete("/{location_id}", status_code=204)
def delete_location(location_id: int, db: Session = Depends(get_db)) -> None:
    LocationService(db).delete(location_id)
