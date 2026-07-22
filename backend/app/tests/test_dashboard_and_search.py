from app.tests.helpers import (
    create_category,
    create_dongle,
    create_location,
    create_module,
    create_pc,
)


def test_dashboard_counts_and_unassigned_dongles(client):
    loc = create_location(client, "Lab")
    pc = create_pc(client, "PC-1", location_id=loc["id"])
    create_dongle(client, "DNG-ASSIGNED", pc_id=pc["id"])
    unassigned = create_dongle(client, "DNG-FREE")
    create_category(client, "Basic")
    create_module(client, "Brake", sort_index=10)

    stats = client.get("/api/dashboard").json()
    assert stats["location_count"] == 1
    assert stats["pc_count"] == 1
    assert stats["dongle_count"] == 2
    assert stats["category_count"] == 1
    assert stats["test_module_count"] == 1
    assert [d["dongle_id"] for d in stats["unassigned_dongles"]] == ["DNG-FREE"]
    assert all(d["pc_id"] is None for d in stats["unassigned_dongles"])
    assert len(stats["recently_changed_dongles"]) == 2
    assert unassigned["dongle_id"] in {
        d["dongle_id"] for d in stats["recently_changed_dongles"]
    }


def test_dongle_search_matches_id_pc_and_location(client):
    loc = create_location(client, "Workshop North")
    pc = create_pc(client, "ALPHA-PC", location_id=loc["id"])
    create_dongle(client, "DNG-AAA", pc_id=pc["id"])
    create_dongle(client, "DNG-BBB")

    by_id = client.get("/api/dongles", params={"search": "bbb"}).json()
    assert [d["dongle_id"] for d in by_id] == ["DNG-BBB"]

    by_pc = client.get("/api/dongles", params={"search": "alpha"}).json()
    assert [d["dongle_id"] for d in by_pc] == ["DNG-AAA"]

    by_location = client.get("/api/dongles", params={"search": "workshop"}).json()
    assert [d["dongle_id"] for d in by_location] == ["DNG-AAA"]


def test_location_detail_counts_include_nested_dongles(client):
    loc = create_location(client, "Lab")
    pc1 = create_pc(client, "PC-1", location_id=loc["id"])
    pc2 = create_pc(client, "PC-2", location_id=loc["id"])
    create_dongle(client, "DNG-1", pc_id=pc1["id"])
    create_dongle(client, "DNG-2", pc_id=pc1["id"])
    create_dongle(client, "DNG-3", pc_id=pc2["id"])

    detail = client.get(f"/api/locations/{loc['id']}").json()
    assert detail["pc_count"] == 2
    assert detail["dongle_count"] == 3
