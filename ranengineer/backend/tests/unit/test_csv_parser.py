from pathlib import Path

import pytest

from app.analytics.ingestion.csv_parser import InvalidKPIFileError, parse_kpi_csv, parse_numeric


def test_parser_maps_aliases_and_preserves_original_data() -> None:
    content = (Path(__file__).parents[1] / "fixtures" / "kpi_sample.csv").read_bytes()
    parsed = parse_kpi_csv(content)
    assert parsed.mapped_columns["rsrp"] == "RSRP"
    assert parsed.rows[0]["cell_id"] == "CELL102"
    assert parsed.rows[0]["original"]["RSRP"] == "-116"


def test_parser_requires_cell_identifier() -> None:
    with pytest.raises(InvalidKPIFileError, match="cell identifier"):
        parse_kpi_csv(b"rsrp,sinr\n-100,5\n")


def test_parser_rejects_empty_csv() -> None:
    with pytest.raises(InvalidKPIFileError, match="empty"):
        parse_kpi_csv(b"")


def test_parse_numeric_normalizes_units_and_nulls() -> None:
    assert parse_numeric("-105 dBm") == -105.0
    assert parse_numeric("15.5 dB") == 15.5
    assert parse_numeric("45 Mbps") == 45.0
    assert parse_numeric("85%") == 85.0
    assert parse_numeric("85 %") == 85.0
    assert parse_numeric("20ms") == 20.0
    assert parse_numeric("1,250.5") == 1250.5
    assert parse_numeric("N/A") is None
    assert parse_numeric("NaN") is None
    assert parse_numeric("null") is None
    assert parse_numeric("-") is None
    assert parse_numeric("") is None
    assert parse_numeric(None) is None


def test_parser_flags_duplicate_cells() -> None:
    csv_data = b"cell_id,RSRP\nCELL01,-85\nCELL01,-95\n"
    parsed = parse_kpi_csv(csv_data)
    assert len(parsed.rows) == 2
    assert any("Duplicate cell identifier" in inv["reason"] for inv in parsed.invalid_values)

