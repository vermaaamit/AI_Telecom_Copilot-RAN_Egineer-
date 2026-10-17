-- Migration 002: Add kpi_degradation column to cells table
-- Phase 1 – adds structured KPI degradation output per cell
ALTER TABLE cells ADD COLUMN IF NOT EXISTS kpi_degradation JSONB NOT NULL DEFAULT '[]'::jsonb;

