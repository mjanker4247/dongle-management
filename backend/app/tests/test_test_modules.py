from app.tests.helpers import create_category, create_module


def test_reorder_test_modules_persists_manual_order(client):
    a = create_module(client, "Alpha", sort_index=10)
    b = create_module(client, "Bravo", sort_index=20)
    c = create_module(client, "Charlie", sort_index=30)

    resp = client.put(
        "/api/test-modules/reorder",
        json={
            "items": [
                {"id": c["id"], "sort_index": 10},
                {"id": a["id"], "sort_index": 20},
                {"id": b["id"], "sort_index": 30},
            ]
        },
    )
    assert resp.status_code == 200

    manual = client.get("/api/test-modules", params={"order": "manual"}).json()
    assert [m["name"] for m in manual] == ["Charlie", "Alpha", "Bravo"]

    alpha = client.get("/api/test-modules", params={"order": "alpha"}).json()
    assert [m["name"] for m in alpha] == ["Alpha", "Bravo", "Charlie"]


def test_reorder_unknown_module_returns_404(client):
    a = create_module(client, "Alpha", sort_index=10)
    resp = client.put(
        "/api/test-modules/reorder",
        json={"items": [{"id": a["id"], "sort_index": 10}, {"id": 9999, "sort_index": 20}]},
    )
    assert resp.status_code == 404


def test_create_module_auto_assigns_sort_index(client):
    first = create_module(client, "First")
    second = create_module(client, "Second")
    assert second["sort_index"] > first["sort_index"]


def test_list_modules_filters_by_active_category_and_search(client):
    active = create_module(client, "Brake Test", sort_index=10, is_active=True)
    inactive = create_module(client, "Legacy Check", sort_index=20, is_active=False)
    other = create_module(client, "Noise", sort_index=30, is_active=True)
    cat = create_category(client, "Safety Pack")
    client.put(
        f"/api/categories/{cat['id']}/modules",
        json={"test_module_ids": [active["id"], inactive["id"]]},
    )

    only_active = client.get("/api/test-modules", params={"is_active": True}).json()
    assert {m["id"] for m in only_active} == {active["id"], other["id"]}

    by_category = client.get(
        "/api/test-modules",
        params={"category_id": cat["id"]},
    ).json()
    assert {m["id"] for m in by_category} == {active["id"], inactive["id"]}

    by_search_name = client.get("/api/test-modules", params={"search": "brake"}).json()
    assert [m["id"] for m in by_search_name] == [active["id"]]

    by_search_category = client.get(
        "/api/test-modules",
        params={"search": "safety pack"},
    ).json()
    assert {m["id"] for m in by_search_category} == {active["id"], inactive["id"]}
