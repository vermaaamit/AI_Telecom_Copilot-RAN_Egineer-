# AI Telecom Copilot – Design Specifications

## 1. Relational Schema Design (PostgreSQL)

### `datasets`
- `id` (VARCHAR 36, PK): Unique dataset identifier.
- `name` (VARCHAR 255): Dataset label.
- `filename` (VARCHAR 255): Original ingested filename.
- `technology` (VARCHAR 32): 4G / 5G / O-RAN.
- `created_at` (TIMESTAMP WITH TIMEZONE): Upload timestamp.
- `row_count`, `cell_count` (INTEGER): Processed counts.
- `summary`, `available_kpis`, `unsupported_columns`, `invalid_values` (JSONB).

### `cells`
- `id` (SERIAL, PK): Internal integer ID.
- `dataset_id` (FK -> `datasets.id`): Associated dataset.
- `cell_id` (VARCHAR 128, INDEX): External cell identifier (e.g. `CELL_001_A`).
- `site_id` (VARCHAR 128, INDEX): Macro/micro site ID.
- `health_score` (INTEGER): Calculated 0–100 health score.
- `status` (VARCHAR 16): `HEALTHY`, `WARNING`, `CRITICAL`, or `UNKNOWN`.
- `kpis`, `original`, `issues`, `kpi_statuses`, `probable_causes` (JSONB).

### `alarms`
- `id` (VARCHAR 64, PK): Alarm identifier (e.g. `ALM-20261014-ABCDEF12`).
- `cell_id`, `site_id` (VARCHAR 128, INDEX): Spatial location.
- `alarm_type` (VARCHAR 128, INDEX): Enum representing alarm classification.
- `severity` (VARCHAR 32, INDEX): `CRITICAL`, `MAJOR`, `MINOR`, `WARNING`.
- `status` (VARCHAR 32, INDEX): `ACTIVE`, `ACKNOWLEDGED`, `CLEARED`.
- `started_at`, `ended_at`, `created_at`, `updated_at` (TIMESTAMP WITH TIMEZONE).
- `details` (JSONB): Metadata, audit details, and file upload context.

### `incidents`
- `id` (VARCHAR 36, PK): Ticket identifier (e.g. `INC-20261014-XXXXXX`).
- `title`, `description` (VARCHAR): Ticket summary.
- `severity` (VARCHAR 32): Priority level.
- `status` (VARCHAR 32): `OPEN`, `RESOLVED`.
- `created_at`, `updated_at` (TIMESTAMP WITH TIMEZONE).
- `resolution` (VARCHAR 1024): Resolution notes.
- `affected_cells`, `related_alarms` (JSONB): Associated network entities.

---

## 2. API Contract Design
- `POST /api/v1/datasets/upload`: Uploads and scans CSV, returns dataset summary.
- `GET /api/v1/datasets/{id}/worst-cells`: Returns degraded cells ordered by health score.
- `GET /api/v1/datasets/{id}/sites/{site_id}`: Computes site-level aggregations across sectors.
- `GET /api/v1/cells/{cell_id}/rca`: Returns cell probable causes correlated with persistent alarms.
- `GET /api/v1/alarms`: Lists all network and security alarms.
- `PATCH /api/v1/alarms/{id}/acknowledge`: Updates alarm state.
- `PATCH /api/v1/alarms/{id}/clear`: Clears active alarm.
- `GET /api/v1/incidents`: Lists incidents.
- `POST /api/v1/incidents`: Creates a new incident.
- `PATCH /api/v1/incidents/{id}/resolve`: Resolves an incident with an audit explanation.

