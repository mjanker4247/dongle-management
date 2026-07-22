from app.tests.helpers import create_category, create_module


def test_set_category_modules_add_remove_and_clear(client):
    m1 = create_module(client, "Brake", sort_index=10)
    m2 = create_module(client, "Safety", sort_index=20)
    m3 = create_module(client, "Noise", sort_index=30)
    cat = create_category(client, "Basic")

    first = client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [m1["id"], m2["id"], m3["id"]]},
    ).json()
    assert sorted(m["id"] for m in first["modules"]) == sorted([m1["id"], m2["id"], m3["id"]])

    second = client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [m2["id"]]},
    ).json()
    assert [m["id"] for m in second["modules"]] == [m2["id"]]

    cleared = client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": []},
    ).json()
    assert cleared["modules"] == []
    assert cleared["module_count"] == 0


def test_set_category_modules_unknown_id_returns_404(client):
    cat = create_category(client, "Basic")
    resp = client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [9999]},
    )
    assert resp.status_code == 404


def test_category_module_order_manual_vs_alphabetical(client):
    zebra = create_module(client, "Zebra", sort_index=10)
    alpha = create_module(client, "Alpha", sort_index=20)
    cat = create_category(client, "Ordered")
    client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [zebra["id"], alpha["id"]]},
    )

    manual = client.get(f"/api/categories/{cat['id']}").json()
    assert [m["name"] for m in manual["modules"]] == ["Zebra", "Alpha"]

    alpha_order = client.get(
        f"/api/categories/{cat['id']}",
        params={"alphabetical": True},
    ).json()
    assert [m["name"] for m in alpha_order["modules"]] == ["Alpha", "Zebra"]
