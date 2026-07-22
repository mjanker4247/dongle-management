from app.tests.helpers import create_category, create_dongle, create_module, setup_basic_inventory


def test_completeness_by_category_name(client):
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
    result = client.get(
        f"/api/dongles/{dongle['id']}/completeness",
        params={"category_name": "basic"},
    ).json()
    assert result["is_complete"] is True
    assert result["category"] == "Basic"


def test_completeness_requires_category(client):
    dongle = create_dongle(client, "DNG-1")
    resp = client.get(f"/api/dongles/{dongle['id']}/completeness")
    assert resp.status_code == 409


def test_completeness_ignores_inactive_required_modules(client):
    active = create_module(client, "Brake", sort_index=10, is_active=True)
    inactive = create_module(client, "Legacy", sort_index=20, is_active=False)
    cat = create_category(client, "Mixed")
    client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [active["id"], inactive["id"]]},
    )
    dongle = create_dongle(client, "DNG-1")
    client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={"modules": [{"test_module_id": active["id"], "enabled": True}]},
    )

    result = client.get(
        f"/api/dongles/{dongle['id']}/completeness",
        params={"category_id": cat["id"]},
    ).json()
    assert result["total_required_modules"] == 1
    assert result["is_complete"] is True
    assert result["missing_modules"] == []


def test_completeness_empty_category_is_complete(client):
    cat = create_category(client, "Empty")
    dongle = create_dongle(client, "DNG-1")
    result = client.get(
        f"/api/dongles/{dongle['id']}/completeness",
        params={"category_id": cat["id"]},
    ).json()
    assert result["total_required_modules"] == 0
    assert result["enabled_required_modules"] == 0
    assert result["is_complete"] is True
    assert result["missing_modules"] == []


def test_disabled_required_module_counts_as_missing(client):
    data = setup_basic_inventory(client)
    modules = data["modules"]
    cat = data["category"]
    dongle = data["dongle"]

    client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": modules[0]["id"], "enabled": True},
                {"test_module_id": modules[1]["id"], "enabled": False},
            ]
        },
    )
    result = client.get(
        f"/api/dongles/{dongle['id']}/completeness",
        params={"category_id": cat["id"]},
    ).json()
    assert result["is_complete"] is False
    assert [m["name"] for m in result["missing_modules"]] == ["Safety"]
    assert result["enabled_required_modules"] == 1
