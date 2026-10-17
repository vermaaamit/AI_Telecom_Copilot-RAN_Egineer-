-- Initial development schema. Apply through the deployment migration process in shared environments.
CREATE TABLE IF NOT EXISTS datasets (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  filename VARCHAR(255) NOT NULL,
  technology VARCHAR(32),
  created_at TIMESTAMPTZ NOT NULL,
  row_count INTEGER NOT NULL,
  cell_count INTEGER NOT NULL,
  available_kpis JSONB NOT NULL,
  unsupported_columns JSONB NOT NULL,
  invalid_values JSONB NOT NULL,
  summary JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS cells (
  id SERIAL PRIMARY KEY,
  dataset_id VARCHAR(36) NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
  cell_id VARCHAR(128) NOT NULL,
  site_id VARCHAR(128),
  technology VARCHAR(32),
  health_score INTEGER,
  status VARCHAR(16) NOT NULL,
  kpis JSONB NOT NULL,
  original JSONB NOT NULL,
  issues JSONB NOT NULL,
  kpi_statuses JSONB NOT NULL,
  probable_causes JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_cells_dataset_id ON cells(dataset_id);
CREATE INDEX IF NOT EXISTS ix_cells_cell_id ON cells(cell_id);
CREATE INDEX IF NOT EXISTS ix_cells_health_score ON cells(health_score);
