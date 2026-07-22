"""Shared helpers for API tests."""


def create_location(client, name: str = "Lab", description: str | None = None) -> dict:
    payload = {"name": name}
    if description is not None:
        payload["description"] = description
    resp = client.post("/api/locations", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_pc(
    client,
    name: str = "PC-1",
    location_id: int | None = None,
    description: str | None = None,
) -> dict:
    payload: dict = {"name": name}
    if location_id is not None:
        payload["location_id"] = location_id
    if description is not None:
        payload["description"] = description
    resp = client.post("/api/pcs", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_module(
    client,
    name: str,
    sort_index: int | None = None,
    is_active: bool = True,
) -> dict:
    payload: dict = {"name": name, "is_active": is_active}
    if sort_index is not None:
        payload["sort_index"] = sort_index
    resp = client.post("/api/test-modules", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_category(client, name: str = "Basic", description: str | None = None) -> dict:
    payload = {"name": name}
    if description is not None:
        payload["description"] = description
    resp = client.post("/api/categories", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_dongle(
    client,
    dongle_id: str = "DNG-1",
    pc_id: int | None = None,
    description: str | None = None,
) -> dict:
    payload: dict = {"dongle_id": dongle_id}
    if pc_id is not None:
        payload["pc_id"] = pc_id
    if description is not None:
        payload["description"] = description
    resp = client.post("/api/dongles", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def setup_basic_inventory(client) -> dict:
    """Create a small related inventory graph used by several tests."""
    loc = create_location(client, "Lab")
    pc = create_pc(client, "PC-1", location_id=loc["id"])
    modules = [
        create_module(client, name, sort_index=i * 10)
        for i, name in enumerate(["Brake", "Safety", "Emissions", "Noise"], start=1)
    ]
    cat = create_category(client, "Basic")
    client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [modules[0]["id"], modules[1]["id"]]},
    )
    dongle = create_dongle(client, "DNG-1", pc_id=pc["id"])
    return {
        "location": loc,
        "pc": pc,
        "modules": modules,
        "category": cat,
        "dongle": dongle,
    }
