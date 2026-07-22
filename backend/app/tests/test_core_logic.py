from app.schemas.dongle import DongleModulesUpdate, DongleModuleLink


def _setup_basic_data(client):
    loc = client.post("/api/locations", json={"name": "Lab"}).json()
    pc = client.post("/api/pcs", json={"name": "PC-1", "location_id": loc["id"]}).json()
    modules = []
    for i, name in enumerate(["Brake", "Safety", "Emissions", "Noise"], start=1):
        modules.append(
            client.post(
                "/api/test-modules",
                json={"name": name, "sort_index": i * 10, "is_active": True},
            ).json()
        )
    cat = client.post("/api/categories", json={"name": "Basic"}).json()
    client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [modules[0]["id"], modules[1]["id"]]},
    )
    dongle = client.post(
        "/api/dongles", json={"dongle_id": "DNG-1", "pc_id": pc["id"]}
    ).json()
    return loc, pc, modules, cat, dongle


def test_completeness_complete_and_incomplete(client):
    _, _, modules, cat, dongle = _setup_basic_data(client)

    # Enable only Brake -> incomplete
    client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": modules[0]["id"], "enabled": True},
            ]
        },
    )
    result = client.get(
        f"/api/dongles/{dongle['id']}/completeness",
        params={"category_id": cat["id"]},
    ).json()
    assert result["is_complete"] is False
    assert result["total_required_modules"] == 2
    assert result["enabled_required_modules"] == 1
    assert [m["name"] for m in result["missing_modules"]] == ["Safety"]

    # Enable both required + an extra -> complete with extras
    client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": modules[0]["id"], "enabled": True},
                {"test_module_id": modules[1]["id"], "enabled": True},
                {"test_module_id": modules[2]["id"], "enabled": True},
            ]
        },
    )
    result = client.get(
        f"/api/dongles/{dongle['id']}/completeness",
        params={"category_id": cat["id"]},
    ).json()
    assert result["is_complete"] is True
    assert result["missing_modules"] == []
    assert [m["name"] for m in result["extra_enabled_modules"]] == ["Emissions"]


def test_dongle_assigned_to_only_one_pc(client):
    client.post("/api/locations", json={"name": "Lab"})
    pc1 = client.post("/api/pcs", json={"name": "PC-A"}).json()
    pc2 = client.post("/api/pcs", json={"name": "PC-B"}).json()
    dongle = client.post(
        "/api/dongles", json={"dongle_id": "DNG-X", "pc_id": pc1["id"]}
    ).json()
    assert dongle["pc_id"] == pc1["id"]

    updated = client.post(
        f"/api/dongles/{dongle['id']}/assign-pc",
        json={"pc_id": pc2["id"]},
    ).json()
    assert updated["pc_id"] == pc2["id"]

    # Re-fetch and ensure only one PC assignment exists
    detail = client.get(f"/api/dongles/{dongle['id']}").json()
    assert detail["pc_id"] == pc2["id"]
    assert detail["pc"]["name"] == "PC-B"

    # Unassign
    cleared = client.post(
        f"/api/dongles/{dongle['id']}/assign-pc",
        json={"pc_id": None},
    ).json()
    assert cleared["pc_id"] is None


def test_import_duplicates_do_not_create_duplicates(client):
    first = client.post(
        "/api/import/pcs/text",
        json={"text": "PC-1\nPC-2\nPC-1\n", "preview_only": False},
    ).json()
    assert first["created"] == 2
    assert first["skipped"] == 1

    second = client.post(
        "/api/import/pcs/text",
        json={"text": "pc-1\nPC-3\n", "preview_only": False},
    ).json()
    assert second["created"] == 1
    assert second["skipped"] + second["updated"] >= 1

    pcs = client.get("/api/pcs").json()
    names = sorted(p["name"].casefold() for p in pcs)
    assert names == ["pc-1", "pc-2", "pc-3"]


def test_enable_disable_modules_on_dongle(client):
    _, _, modules, _, dongle = _setup_basic_data(client)
    updated = client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": modules[0]["id"], "enabled": True},
                {"test_module_id": modules[1]["id"], "enabled": False},
            ]
        },
    ).json()
    enabled_map = {m["test_module_id"]: m["enabled"] for m in updated["modules"]}
    assert enabled_map[modules[0]["id"]] is True
    assert enabled_map[modules[1]["id"]] is False

    # Toggle
    updated = client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": modules[0]["id"], "enabled": False},
                {"test_module_id": modules[1]["id"], "enabled": True},
            ]
        },
    ).json()
    enabled_map = {m["test_module_id"]: m["enabled"] for m in updated["modules"]}
    assert enabled_map[modules[0]["id"]] is False
    assert enabled_map[modules[1]["id"]] is True


def test_duplicate_dongle_id_rejected(client):
    client.post("/api/dongles", json={"dongle_id": "DNG-1"})
    resp = client.post("/api/dongles", json={"dongle_id": "dng-1"})
    assert resp.status_code == 409


def test_import_preview_does_not_persist(client):
    result = client.post(
        "/api/import/categories/text",
        json={"text": "CatA\nCatB", "preview_only": True},
    ).json()
    assert result["created"] == 2
    cats = client.get("/api/categories").json()
    assert cats == []
