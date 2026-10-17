from pathlib import Path

from app.services.dataset_service import analyse_dataset, find_underperforming_cells


def test_finds_worst_cells_in_score_order() -> None:
    content = (Path(__file__).parents[1] / "fixtures" / "kpi_sample.csv").read_bytes()
    dataset = analyse_dataset(content, "kpi_sample.csv")
    cells = find_underperforming_cells(dataset, limit=2)
    assert [cell["cell_id"] for cell in cells] == ["CELL102", "CELL221"]
    assert cells[0]["probable_causes"]
