from app.services.naming import names_equal, normalize_name


def test_normalize_name_trims_whitespace():
    assert normalize_name("  Lab A  ") == "Lab A"
    assert normalize_name("\tPC-1\n") == "PC-1"


def test_normalize_name_none_and_empty():
    assert normalize_name(None) == ""
    assert normalize_name("") == ""
    assert normalize_name("   ") == ""


def test_normalize_name_preserves_inner_spacing_and_case():
    assert normalize_name("  Full  Inspection ") == "Full  Inspection"
    assert normalize_name("MiXeD") == "MiXeD"


def test_names_equal_case_insensitive_and_trimmed():
    assert names_equal(" Lab ", "lab") is True
    assert names_equal("PC-1", "pc-1") is True
    assert names_equal("Alpha", "Beta") is False
    assert names_equal("A", "A ") is True
