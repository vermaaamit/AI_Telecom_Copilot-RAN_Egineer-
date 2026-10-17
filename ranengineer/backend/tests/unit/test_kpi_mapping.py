from app.config.kpi_config import find_identifier_column, get_kpi_definitions, map_columns, normalise_column_name, IDENTIFIER_ALIASES, SITE_IDENTIFIER_ALIASES


def test_kpi_definitions_structure() -> None:
    definitions = get_kpi_definitions()
    assert "rsrp" in definitions
    assert "sinr" in definitions
    assert "dl_throughput" in definitions
    assert "prb_utilization" in definitions
    assert definitions["rsrp"]["direction"] == "higher_is_better"
    assert definitions["prb_utilization"]["direction"] == "lower_is_better"
    assert "weight" in definitions["rsrp"]


def test_map_columns_with_aliases() -> None:
    columns = [
        "Cell_Name", "Site_ID", "Technology",
        "avg_rsrp", "SINR_dB", "DL_Throughput_Mbps",
        "prb_utilization_percent", "Cell_Availability",
        "Random_Custom_Column"
    ]
    mapped, unsupported = map_columns(columns)
    assert mapped["rsrp"] == "avg_rsrp"
    assert mapped["sinr"] == "SINR_dB"
    assert mapped["dl_throughput"] == "DL_Throughput_Mbps"
    assert mapped["prb_utilization"] == "prb_utilization_percent"
    assert mapped["availability"] == "Cell_Availability"
    assert "Random_Custom_Column" in unsupported


def test_find_identifier_column() -> None:
    assert find_identifier_column(["cell_id", "rsrp"], IDENTIFIER_ALIASES) == "cell_id"
    assert find_identifier_column(["Cell_Name", "rsrp"], IDENTIFIER_ALIASES) == "Cell_Name"
    assert find_identifier_column(["ECI", "rsrp"], IDENTIFIER_ALIASES) == "ECI"
    assert find_identifier_column(["foo", "bar"], IDENTIFIER_ALIASES) is None

