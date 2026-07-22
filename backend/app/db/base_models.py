from app.db.base import Base
from app.models import (  # noqa: F401
    Category,
    CategoryTestModule,
    Dongle,
    DongleTestModule,
    Location,
    PC,
    TestModule,
)

__all__ = ["Base"]
