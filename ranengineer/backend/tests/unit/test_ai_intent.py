from app.ai.intent import parse_intent


def test_intent_find_bad_cells() -> None:
    i1 = parse_intent("Which cells are performing badly?")
    assert i1.name == "find_bad_cells"
    assert i1.limit == 10

    i2 = parse_intent("Show me the worst 5 cells.")
    assert i2.name == "find_bad_cells"
    assert i2.limit == 5

    i3 = parse_intent("What should a RAN engineer check first?")
    assert i3.name == "find_bad_cells"


def test_intent_cell_analysis() -> None:
    i1 = parse_intent("Why is CELL102 performing badly?")
    assert i1.name == "cell_analysis"
    assert i1.target_id == "CELL102"

    i2 = parse_intent("Analyze GNB-013 performance")
    assert i2.name == "cell_analysis"
    assert i2.target_id == "GNB-013"


def test_intent_compare_cells() -> None:
    i = parse_intent("Compare CELL102 and CELL105.")
    assert i.name == "compare_cells"
    assert i.target_id == "CELL102"
    assert i.target_id_2 == "CELL105"


def test_intent_filter_kpi() -> None:
    i1 = parse_intent("Which cells have poor RSRP?")
    assert i1.name == "filter_cells_by_kpi"
    assert i1.kpi == "rsrp"

    i2 = parse_intent("Which cells have SINR below 5?")
    assert i2.name == "filter_cells_by_kpi"
    assert i2.kpi == "sinr"
    assert i2.threshold == 5.0
    assert i2.direction == "lower"

    i3 = parse_intent("Which cells have high PRB utilization?")
    assert i3.name == "filter_cells_by_kpi"
    assert i3.kpi == "prb_utilization"


def test_intent_site_questions() -> None:
    i1 = parse_intent("Which site has the worst performance?")
    assert i1.name == "compare_sites"

    i2 = parse_intent("Which sites are congested?")
    assert i2.name == "compare_sites"


def test_intent_dataset_summary() -> None:
    i1 = parse_intent("Give me a KPI summary.")
    assert i1.name == "dataset_summary"

    i2 = parse_intent("What are the major issues in this dataset?")
    assert i2.name == "dataset_summary"


def test_intent_anomalies() -> None:
    i1 = parse_intent("Show me anomalous cells.")
    assert i1.name == "get_anomalies"

    i2 = parse_intent("Detect outliers in the network")
    assert i2.name == "get_anomalies"

