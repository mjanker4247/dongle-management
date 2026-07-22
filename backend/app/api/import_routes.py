from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.import_schema import ImportResult, ImportRowError, TextImportRequest
from app.services.import_service import ImportService, parse_csv_upload, parse_lines

router = APIRouter(prefix="/import", tags=["import"])


def _run_import(
    service_method_name: str,
    db: Session,
    *,
    file: UploadFile | None,
    text: str | None,
    preview_only: bool,
) -> ImportResult:
    service = ImportService(db)
    method = getattr(service, service_method_name)
    values: list[str] = []
    if file is not None:
        content = file.file.read()
        values = parse_csv_upload(content)
    elif text is not None:
        values = parse_lines(text)
    else:
        return ImportResult(
            errors=[ImportRowError(row=0, message="Provide a CSV file or text payload")]
        )
    return method(values, preview_only=preview_only)


@router.post("/pcs", response_model=ImportResult)
async def import_pcs(
    file: UploadFile | None = File(None),
    preview_only: bool = Form(False),
    db: Session = Depends(get_db),
) -> ImportResult:
    return _run_import("import_pcs", db, file=file, text=None, preview_only=preview_only)


@router.post("/pcs/text", response_model=ImportResult)
def import_pcs_text(data: TextImportRequest, db: Session = Depends(get_db)) -> ImportResult:
    return ImportService(db).import_pcs(parse_lines(data.text), preview_only=data.preview_only)


@router.post("/dongles", response_model=ImportResult)
async def import_dongles(
    file: UploadFile | None = File(None),
    preview_only: bool = Form(False),
    db: Session = Depends(get_db),
) -> ImportResult:
    return _run_import("import_dongles", db, file=file, text=None, preview_only=preview_only)


@router.post("/dongles/text", response_model=ImportResult)
def import_dongles_text(data: TextImportRequest, db: Session = Depends(get_db)) -> ImportResult:
    return ImportService(db).import_dongles(parse_lines(data.text), preview_only=data.preview_only)


@router.post("/categories", response_model=ImportResult)
async def import_categories(
    file: UploadFile | None = File(None),
    preview_only: bool = Form(False),
    db: Session = Depends(get_db),
) -> ImportResult:
    return _run_import("import_categories", db, file=file, text=None, preview_only=preview_only)


@router.post("/categories/text", response_model=ImportResult)
def import_categories_text(
    data: TextImportRequest, db: Session = Depends(get_db)
) -> ImportResult:
    return ImportService(db).import_categories(
        parse_lines(data.text), preview_only=data.preview_only
    )


@router.post("/test-modules", response_model=ImportResult)
async def import_test_modules(
    file: UploadFile | None = File(None),
    preview_only: bool = Form(False),
    db: Session = Depends(get_db),
) -> ImportResult:
    return _run_import("import_test_modules", db, file=file, text=None, preview_only=preview_only)


@router.post("/test-modules/text", response_model=ImportResult)
def import_test_modules_text(
    data: TextImportRequest, db: Session = Depends(get_db)
) -> ImportResult:
    return ImportService(db).import_test_modules(
        parse_lines(data.text), preview_only=data.preview_only
    )
