from app.tests.helpers import (
    create_category,
    create_dongle,
    create_location,
    create_module,
    create_pc,
)


def test_delete_location_unassigns_pcs_but_keeps_them(client):
    loc = create_location(client, "Lab")
    pc = create_pc(client, "PC-1", location_id=loc["id"])
    dongle = create_dongle(client, "DNG-1", pc_id=pc["id"])

    resp = client.delete(f"/api/locations/{loc['id']}")
    assert resp.status_code == 204

    assert client.get(f"/api/locations/{loc['id']}").status_code == 404
    refreshed_pc = client.get(f"/api/pcs/{pc['id']}").json()
    assert refreshed_pc["location_id"] is None
    refreshed_dongle = client.get(f"/api/dongles/{dongle['id']}").json()
    assert refreshed_dongle["pc_id"] == pc["id"]


def test_delete_pc_unassigns_dongles(client):
    pc = create_pc(client, "PC-1")
    dongle = create_dongle(client, "DNG-1", pc_id=pc["id"])

    resp = client.delete(f"/api/pcs/{pc['id']}")
    assert resp.status_code == 204

    assert client.get(f"/api/pcs/{pc['id']}").status_code == 404
    refreshed = client.get(f"/api/dongles/{dongle['id']}").json()
    assert refreshed["pc_id"] is None


def test_delete_category_keeps_test_modules(client):
    module = create_module(client, "Brake")
    cat = create_category(client, "Basic")
    client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [module["id"]]},
    )

    resp = client.delete(f"/api/categories/{cat['id']}")
    assert resp.status_code == 204

    assert client.get(f"/api/categories/{cat['id']}").status_code == 404
    assert client.get(f"/api/test-modules/{module['id']}").status_code == 200


def test_delete_test_module_removes_category_and_dongle_links(client):
    module = create_module(client, "Brake")
    other = create_module(client, "Safety")
    cat = create_category(client, "Basic")
    client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [module["id"], other["id"]]},
    )
    dongle = create_dongle(client, "DNG-1")
    client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={
            "modules": [
                {"test_module_id": module["id"], "enabled": True},
                {"test_module_id": other["id"], "enabled": True},
            ]
        },
    )

    resp = client.delete(f"/api/test-modules/{module['id']}")
    assert resp.status_code == 204

    cat_detail = client.get(f"/api/categories/{cat['id']}").json()
    assert [m["id"] for m in cat_detail["modules"]] == [other["id"]]

    dongle_detail = client.get(f"/api/dongles/{dongle['id']}").json()
    assert [m["test_module_id"] for m in dongle_detail["modules"]] == [other["id"]]


def test_delete_dongle_removes_module_links_only(client):
    module = create_module(client, "Brake")
    dongle = create_dongle(client, "DNG-1")
    client.put(
        f"/api/dongles/{dongle['id']}/modules",
        json={"modules": [{"test_module_id": module["id"], "enabled": True}]},
    )

    resp = client.delete(f"/api/dongles/{dongle['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/dongles/{dongle['id']}").status_code == 404
    assert client.get(f"/api/test-modules/{module['id']}").status_code == 200
