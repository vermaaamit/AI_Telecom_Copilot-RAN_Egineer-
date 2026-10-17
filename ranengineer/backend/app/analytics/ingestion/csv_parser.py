import csv
import io
import re
from dataclasses import dataclass

from app.config.kpi_config import find_identifier_column, map_columns, normalise_column_name, IDENTIFIER_ALIASES, SITE_IDENTIFIER_ALIASES

NULL_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--", "nil"}
UNIT_SUFFIX_REGEX = re.compile(r"(?i)\s*(?:dbm|db|mbps|kbps|gbps|bps|pct|percent|ms|s|%)\b")


class InvalidKPIFileError(ValueError):
    pass


@dataclass
class ParsedCSV:
    rows: list[dict[str, object]]
    mapped_columns: dict[str, str]
    unsupported_columns: list[str]
    invalid_values: list[dict[str, object]]


def parse_numeric(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in NULL_TOKENS:
        return None
    cleaned = UNIT_SUFFIX_REGEX.sub("", cleaned)
    cleaned = cleaned.replace(",", "").replace("%", "").strip()
    return float(cleaned)


def parse_kpi_csv(content: bytes) -> ParsedCSV:
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
    except (UnicodeDecodeError, csv.Error) as error:
        raise InvalidKPIFileError("CSV could not be read.") from error
    if not reader.fieldnames:
        raise InvalidKPIFileError("CSV is empty or has no header row.")
    cell_column = find_identifier_column(reader.fieldnames, IDENTIFIER_ALIASES)
    if not cell_column:
        raise InvalidKPIFileError("Required cell identifier column was not found.")
    site_column = find_identifier_column(reader.fieldnames, SITE_IDENTIFIER_ALIASES)
    mapped_columns, unsupported_columns = map_columns(reader.fieldnames)
    rows: list[dict[str, object]] = []
    invalid_values: list[dict[str, object]] = []
    seen_cells: set[str] = set()

    for row_number, source in enumerate(reader, start=2):
        cell_id = (source.get(cell_column) or "").strip()
        if not cell_id:
            invalid_values.append({"row": row_number, "column": cell_column, "reason": "Missing cell identifier"})
            continue
        if cell_id in seen_cells:
            invalid_values.append({"row": row_number, "column": cell_column, "reason": f"Duplicate cell identifier: {cell_id}"})
        seen_cells.add(cell_id)

        kpis: dict[str, float | None] = {}
        for kpi, column in mapped_columns.items():
            try:
                kpis[kpi] = parse_numeric(source.get(column))
            except ValueError:
                kpis[kpi] = None
                invalid_values.append({"row": row_number, "column": column, "reason": "Invalid numeric value"})
        technology_column = next((column for column in reader.fieldnames if normalise_column_name(column) == "technology"), None)
        rows.append({"cell_id": cell_id, "site_id": (source.get(site_column) or "").strip() if site_column else None, "technology": (source.get(technology_column) or "").strip() if technology_column else None, "kpis": kpis, "original": source})
    if not rows:
        raise InvalidKPIFileError("CSV has no valid rows with a cell identifier.")
    return ParsedCSV(rows=rows, mapped_columns=mapped_columns, unsupported_columns=unsupported_columns, invalid_values=invalid_values)

