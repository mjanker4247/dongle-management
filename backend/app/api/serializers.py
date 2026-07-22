from __future__ import annotations

from app.models import Category, Dongle, Location, PC, TestModule
from app.schemas.category import CategoryDetail, CategoryRead, TestModuleBrief
from app.schemas.dongle import (
    DongleDetail,
    DongleModuleLink,
    DongleRead,
    LocationBrief,
    PCBrief,
    TestModuleBrief as DongleTestModuleBrief,
)
from app.schemas.location import LocationDetail, LocationRead
from app.schemas.pc import DongleBrief, PCDetail, PCRead, LocationBrief as PCLocationBrief
from app.schemas.test_module import CategoryBrief, TestModuleRead
from app.services.dongle_service import DongleService


def location_to_read(location: Location) -> LocationRead:
    return LocationRead.model_validate(location)


def location_to_detail(location: Location, pc_count: int, dongle_count: int) -> LocationDetail:
    base = LocationRead.model_validate(location)
    return LocationDetail(**base.model_dump(), pc_count=pc_count, dongle_count=dongle_count)


def pc_to_read(pc: PC) -> PCRead:
    location = None
    if pc.location:
        location = PCLocationBrief(id=pc.location.id, name=pc.location.name)
    return PCRead(
        id=pc.id,
        name=pc.name,
        location_id=pc.location_id,
        description=pc.description,
        created_at=pc.created_at,
        updated_at=pc.updated_at,
        location=location,
        dongle_count=len(pc.dongles) if pc.dongles is not None else 0,
    )


def pc_to_detail(pc: PC) -> PCDetail:
    base = pc_to_read(pc)
    return PCDetail(
        **base.model_dump(),
        dongles=[DongleBrief(id=d.id, dongle_id=d.dongle_id) for d in pc.dongles],
    )


def dongle_to_read(dongle: Dongle) -> DongleRead:
    pc_brief = None
    if dongle.pc:
        loc = None
        if dongle.pc.location:
            loc = LocationBrief(id=dongle.pc.location.id, name=dongle.pc.location.name)
        pc_brief = PCBrief(id=dongle.pc.id, name=dongle.pc.name, location=loc)
    return DongleRead(
        id=dongle.id,
        dongle_id=dongle.dongle_id,
        pc_id=dongle.pc_id,
        description=dongle.description,
        created_at=dongle.created_at,
        updated_at=dongle.updated_at,
        pc=pc_brief,
        enabled_module_count=DongleService.enabled_count(dongle),
    )


def dongle_to_detail(dongle: Dongle) -> DongleDetail:
    base = dongle_to_read(dongle)
    modules = []
    for link in sorted(
        dongle.module_links,
        key=lambda l: (
            l.test_module.sort_index if l.test_module else 0,
            l.test_module.name.casefold() if l.test_module else "",
        ),
    ):
        tm = None
        if link.test_module:
            tm = DongleTestModuleBrief(
                id=link.test_module.id,
                name=link.test_module.name,
                sort_index=link.test_module.sort_index,
                is_active=link.test_module.is_active,
            )
        modules.append(
            DongleModuleLink(
                test_module_id=link.test_module_id,
                enabled=link.enabled,
                test_module=tm,
            )
        )
    return DongleDetail(**base.model_dump(), modules=modules)


def category_to_read(category: Category) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        name=category.name,
        description=category.description,
        created_at=category.created_at,
        updated_at=category.updated_at,
        module_count=len(category.module_links) if category.module_links is not None else 0,
    )


def category_to_detail(category: Category, alphabetical: bool = False) -> CategoryDetail:
    base = category_to_read(category)
    modules = [
        link.test_module
        for link in category.module_links
        if link.test_module is not None
    ]
    if alphabetical:
        modules.sort(key=lambda m: m.name.casefold())
    else:
        modules.sort(key=lambda m: (m.sort_index, m.name.casefold()))
    return CategoryDetail(
        **base.model_dump(),
        modules=[
            TestModuleBrief(
                id=m.id,
                name=m.name,
                sort_index=m.sort_index,
                is_active=m.is_active,
            )
            for m in modules
        ],
    )


def test_module_to_read(module: TestModule) -> TestModuleRead:
    categories = [
        CategoryBrief(id=link.category.id, name=link.category.name)
        for link in module.category_links
        if link.category is not None
    ]
    categories.sort(key=lambda c: c.name.casefold())
    return TestModuleRead(
        id=module.id,
        name=module.name,
        description=module.description,
        sort_index=module.sort_index,
        is_active=module.is_active,
        created_at=module.created_at,
        updated_at=module.updated_at,
        categories=categories,
    )
