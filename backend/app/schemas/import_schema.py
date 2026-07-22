from typing import Any, Optional

from pydantic import BaseModel, Field


class ImportRowError(BaseModel):
    row: int
    field: Optional[str] = None
    message: str
    value: Optional[str] = None


class ImportResult(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[ImportRowError] = Field(default_factory=list)
    details: list[dict[str, Any]] = Field(default_factory=list)


class TextImportRequest(BaseModel):
    """Paste import: one value per line, or CSV text."""

    text: str
    preview_only: bool = False


class ImportPreviewRequest(BaseModel):
    preview_only: bool = False
