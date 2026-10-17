import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "kpi" / "definitions.json"
IDENTIFIER_ALIASES = {"cell_id", "cell", "cell_name", "cellid", "eci"}
SITE_IDENTIFIER_ALIASES = {"site_id", "site", "site_name"}


def normalise_column_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


@lru_cache
def get_kpi_definitions() -> dict[str, dict[str, Any]]:
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        return json.load(config_file)


def map_columns(columns: list[str]) -> tuple[dict[str, str], list[str]]:
    definitions = get_kpi_definitions()
    normalised = {normalise_column_name(column): column for column in columns}
    mapped: dict[str, str] = {}
    recognised: set[str] = set()
    for kpi, definition in definitions.items():
        for alias in [kpi, *definition["aliases"]]:
            source = normalised.get(normalise_column_name(alias))
            if source:
                mapped[kpi] = source
                recognised.add(source)
                break
    for alias in IDENTIFIER_ALIASES | SITE_IDENTIFIER_ALIASES | {"technology", "timestamp", "date", "region"}:
        source = normalised.get(alias)
        if source:
            recognised.add(source)
    return mapped, [column for column in columns if column not in recognised]


def find_identifier_column(columns: list[str], aliases: set[str]) -> str | None:
    for column in columns:
        if normalise_column_name(column) in aliases:
            return column
    return None
