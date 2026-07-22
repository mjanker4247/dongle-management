from app.tests.helpers import create_dongle, create_module, setup_basic_inventory


def test_set_modules_replaces_unlisted_links(client):
    data = setup_basic_inventory(client)
    modules = data["modules"]
    dongle = data["dongle"]

    client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": modules[0]["id"], "enabled": True},
                {"test_module_id": modules[1]["id"], "enabled": True},
            ]
        },
    )

    replaced = client.post(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": modules[0]["id"], "enabled": True},
            ]
        },
    ).json()
    ids = [m["test_module_id"] for m in replaced["modules"]]
    assert ids == [modules[0]["id"]]


def test_update_modules_keeps_unlisted_links(client):
    data = setup_basic_inventory(client)
    modules = data["modules"]
    dongle = data["dongle"]

    client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": modules[0]["id"], "enabled": True},
                {"test_module_id": modules[1]["id"], "enabled": True},
            ]
        },
    )

    updated = client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": modules[0]["id"], "enabled": False},
            ]
        },
    ).json()
    enabled_map = {m["test_module_id"]: m["enabled"] for m in updated["modules"]}
    assert enabled_map[modules[0]["id"]] is False
    assert enabled_map[modules[1]["id"]] is True


def test_set_modules_unknown_module_returns_404(client):
    dongle = create_dongle(client, "DNG-1")
    resp = client.post(
        f"/api/dongles/{dongle['id']}/modules",
        json={"modules": [{"test_module_id": 9999, "enabled": True}]},
    )
    assert resp.status_code == 404


def test_update_modules_unknown_module_returns_404(client):
    dongle = create_dongle(client, "DNG-1")
    resp = client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={"modules": [{"test_module_id": 9999, "enabled": True}]},
    )
    assert resp.status_code == 404


def test_enabled_module_count_matches_enabled_links(client):
    module_a = create_module(client, "A", sort_index=10)
    module_b = create_module(client, "B", sort_index=20)
    dongle = create_dongle(client, "DNG-1")
    client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": module_a["id"], "enabled": True},
                {"test_module_id": module_b["id"], "enabled": False},
            ]
        },
    )
    listed = client.get("/api/dongles").json()
    row = next(d for d in listed if d["id"] == dongle["id"])
    assert row["enabled_module_count"] == 1
