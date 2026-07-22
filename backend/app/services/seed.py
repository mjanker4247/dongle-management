from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, CategoryTestModule, Dongle, DongleTestModule, Location, PC, TestModule
from app.services.naming import normalize_name


def seed_database(db: Session) -> None:
    """Insert example data for local development if tables are empty."""
    if db.scalars(select(Location).limit(1)).first():
        return

    lab = Location(name="Lab A", description="Main testing laboratory")
    workshop = Location(name="Workshop", description="Secondary workshop floor")
    db.add_all([lab, workshop])
    db.flush()

    pc1 = PC(name="TEST-PC-01", location_id=lab.id, description="Primary test station")
    pc2 = PC(name="TEST-PC-02", location_id=lab.id)
    pc3 = PC(name="WORK-PC-01", location_id=workshop.id)
    db.add_all([pc1, pc2, pc3])
    db.flush()

    modules_data = [
        ("Brake Test", 10),
        ("Emissions Check", 20),
        ("Headlight Alignment", 30),
        ("Noise Measurement", 40),
        ("Safety Inspection", 50),
        ("Speedometer Check", 60),
        ("Suspension Test", 70),
        ("Wheel Alignment", 80),
    ]
    modules: list[TestModule] = []
    for name, sort_index in modules_data:
        modules.append(TestModule(name=name, sort_index=sort_index, is_active=True))
    db.add_all(modules)
    db.flush()

    cat_full = Category(name="Full Inspection", description="Complete inspection package")
    cat_basic = Category(name="Basic Safety", description="Minimum safety checks")
    cat_emissions = Category(name="Emissions", description="Emissions-related modules")
    db.add_all([cat_full, cat_basic, cat_emissions])
    db.flush()

    by_name = {m.name: m for m in modules}
    for m in modules:
        db.add(CategoryTestModule(category_id=cat_full.id, test_module_id=m.id))
    for name in ["Brake Test", "Safety Inspection", "Headlight Alignment"]:
        db.add(CategoryTestModule(category_id=cat_basic.id, test_module_id=by_name[name].id))
    for name in ["Emissions Check", "Noise Measurement"]:
        db.add(CategoryTestModule(category_id=cat_emissions.id, test_module_id=by_name[name].id))

    d1 = Dongle(dongle_id="DNG-1001", pc_id=pc1.id, description="Station 1 main dongle")
    d2 = Dongle(dongle_id="DNG-1002", pc_id=pc1.id)
    d3 = Dongle(dongle_id="DNG-2001", pc_id=pc2.id)
    d4 = Dongle(dongle_id="DNG-9001", pc_id=None, description="Unassigned spare")
    db.add_all([d1, d2, d3, d4])
    db.flush()

    # DNG-1001 has all basic safety modules (complete for Basic Safety)
    for name in ["Brake Test", "Safety Inspection", "Headlight Alignment", "Emissions Check"]:
        db.add(DongleTestModule(dongle_id=d1.id, test_module_id=by_name[name].id, enabled=True))

    # DNG-1002 incomplete for Basic Safety
    db.add(DongleTestModule(dongle_id=d2.id, test_module_id=by_name["Brake Test"].id, enabled=True))

    # DNG-2001 has emissions modules
    for name in ["Emissions Check", "Noise Measurement"]:
        db.add(DongleTestModule(dongle_id=d3.id, test_module_id=by_name[name].id, enabled=True))

    db.commit()


def ensure_trimmed(value: str) -> str:
    return normalize_name(value)
