from app.tests.helpers import create_dongle, create_module, create_pc


def test_import_dongles_upserts_and_skips_batch_duplicates(client):
    create_dongle(client, "DNG-100")
    result = client.post(
        "/api/import/dongles/text",
        json={"text": "DNG-100\nDNG-200\nDNG-200\ndng-100\n", "preview_only": False},
    ).json()
    assert result["created"] == 1
    assert result["skipped"] >= 1
    dongles = client.get("/api/dongles").json()
    ids = sorted(d["dongle_id"].casefold() for d in dongles)
    assert ids == ["dng-100", "dng-200"]


def test_import_test_modules_assigns_increasing_sort_index(client):
    create_module(client, "Existing", sort_index=50)
    result = client.post(
        "/api/import/test-modules/text",
        json={"text": "New A\nNew B\n", "preview_only": False},
    ).json()
    assert result["created"] == 2
    modules = {
        m["name"]: m
        for m in client.get("/api/test-modules", params={"order": "manual"}).json()
    }
    assert modules["New A"]["sort_index"] > 50
    assert modules["New B"]["sort_index"] > modules["New A"]["sort_index"]


def test_import_updates_casing_of_existing_name(client):
    create_pc(client, "pc-old")
    result = client.post(
        "/api/import/pcs/text",
        json={"text": "PC-OLD\n", "preview_only": False},
    ).json()
    assert result["updated"] == 1
    pcs = client.get("/api/pcs").json()
    assert len(pcs) == 1
    assert pcs[0]["name"] == "PC-OLD"


def test_import_csv_file_upload(client):
    content = b"name\nFILE-PC-1\nFILE-PC-2\n"
    result = client.post(
        "/api/import/pcs",
        files={"file": ("pcs.csv", content, "text/csv")},
        data={"preview_only": "false"},
    ).json()
    assert result["created"] == 2
    names = sorted(p["name"] for p in client.get("/api/pcs").json())
    assert names == ["FILE-PC-1", "FILE-PC-2"]


def test_import_without_payload_returns_error(client):
    result = client.post("/api/import/pcs", data={"preview_only": "false"}).json()
    assert result["created"] == 0
    assert result["errors"]
    assert "Provide a CSV file" in result["errors"][0]["message"]
