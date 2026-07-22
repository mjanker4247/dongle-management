from app.tests.helpers import create_category, create_dongle, create_location, create_module, create_pc


def test_location_name_uniqueness_is_case_insensitive(client):
    create_location(client, "Lab A")
    resp = client.post("/api/locations", json={"name": " lab a "})
    assert resp.status_code == 409


def test_location_empty_name_rejected(client):
    resp = client.post("/api/locations", json={"name": "   "})
    assert resp.status_code in (409, 422)


def test_location_update_to_own_name_allowed(client):
    loc = create_location(client, "Lab")
    resp = client.put(f"/api/locations/{loc['id']}", json={"name": "lab"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "lab"


def test_location_update_clash_rejected(client):
    create_location(client, "Lab A")
    loc_b = create_location(client, "Lab B")
    resp = client.put(f"/api/locations/{loc_b['id']}", json={"name": "lab a"})
    assert resp.status_code == 409


def test_pc_name_uniqueness_is_case_insensitive(client):
    create_pc(client, "TEST-PC")
    resp = client.post("/api/pcs", json={"name": "test-pc"})
    assert resp.status_code == 409


def test_category_name_uniqueness_is_case_insensitive(client):
    create_category(client, "Basic Safety")
    resp = client.post("/api/categories", json={"name": "basic safety"})
    assert resp.status_code == 409


def test_test_module_name_uniqueness_is_case_insensitive(client):
    create_module(client, "Brake Test")
    resp = client.post("/api/test-modules", json={"name": "brake test"})
    assert resp.status_code == 409


def test_dongle_id_update_clash_rejected(client):
    create_dongle(client, "DNG-1")
    other = create_dongle(client, "DNG-2")
    resp = client.put(f"/api/dongles/{other['id']}", json={"dongle_id": "dng-1"})
    assert resp.status_code == 409


def test_pc_invalid_location_rejected(client):
    resp = client.post("/api/pcs", json={"name": "PC-X", "location_id": 9999})
    assert resp.status_code == 404


def test_dongle_invalid_pc_rejected(client):
    resp = client.post("/api/dongles", json={"dongle_id": "DNG-X", "pc_id": 9999})
    assert resp.status_code == 404
