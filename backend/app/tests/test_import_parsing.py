from app.services.import_service import parse_csv_upload, parse_lines


def test_parse_lines_skips_common_headers_and_blanks():
    text = "name\n\nPC-1\n\nPC-2\n"
    assert parse_lines(text) == ["PC-1", "PC-2"]


def test_parse_lines_skips_dongle_and_module_headers():
    assert parse_lines("dongle_id\nDNG-1") == ["DNG-1"]
    assert parse_lines("test module\nBrake Test") == ["Brake Test"]
    assert parse_lines("category_name\nBasic") == ["Basic"]


def test_parse_lines_uses_first_csv_column_only():
    text = "name,description\nPC-1,main lab\nPC-2,workshop\n"
    assert parse_lines(text) == ["PC-1", "PC-2"]


def test_parse_lines_handles_windows_and_mac_newlines():
    assert parse_lines("PC-1\r\nPC-2\r\n") == ["PC-1", "PC-2"]
    assert parse_lines("PC-1\rPC-2\r") == ["PC-1", "PC-2"]


def test_parse_lines_trims_values():
    assert parse_lines("  PC-1  \n\tPC-2\t") == ["PC-1", "PC-2"]


def test_parse_csv_upload_strips_utf8_bom():
    content = "\ufeffname\nPC-1\n".encode("utf-8")
    assert parse_csv_upload(content) == ["PC-1"]


def test_parse_csv_upload_latin1_fallback():
    content = "Café-PC\n".encode("latin-1")
    assert parse_csv_upload(content) == ["Café-PC"]
