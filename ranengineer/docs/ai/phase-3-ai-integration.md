# Phase 3 — AI Integration Architecture

## Overview

The AI Telecom Copilot operates on a strict principle:
> **AI interprets and explains. Analytics calculates. Database stores. RAN rules provide engineering context.**

The LLM is strictly forbidden from directly performing numerical calculations, inventing KPI values, or issuing raw database queries.

## Query Flow Architecture

```text
User Question
      ↓
Intent Parser (app.ai.intent)
      ↓
Structured Query & Parameters
      ↓
Controlled Analytics Tool (app.ai.tools.analytics_tools)
      ↓
Deterministic Result / Evidence
      ↓
LLM Provider Abstraction (AzureOpenAIProvider / DeterministicLLMProvider)
      ↓
Grounding Guardrails & Safety Filter (app.ai.guardrails.grounding)
      ↓
Structured Grounded Response
```

## Controlled Analytics Tools (Section 13)

The LLM interacts exclusively with controlled tool functions:
1. `get_dataset_summary(dataset)`: Summarizes health scores, category distributions, and available KPIs.
2. `find_bad_cells(dataset, limit, ...)`: Returns ranked underperforming cells by application-defined health score.
3. `get_cell_analysis(dataset, cell_id)`: Provides in-depth KPI breakdown, status evaluation, and probable root causes for a specific cell.
4. `filter_cells_by_kpi(dataset, kpi, threshold, direction, limit)`: Identifies cells breaching specific KPI thresholds.
5. `compare_cells(dataset, cell_id_1, cell_id_2)`: Conducts a head-to-head comparison of two cells across all KPIs.
6. `compare_sites(dataset, site_id_1, site_id_2)`: Ranks network sites by aggregated cell health score.
7. `get_anomalies(dataset, limit)`: Surfaces critical cells and acute threshold anomalies.
8. `get_kpi_trend(dataset, kpi)`: Computes statistical metrics (min, max, avg) for measured KPIs.

## Structured Response Format (Section 35)

All engineering explanations adhere to the structured response format:
- **Summary**: Concise high-level statement of network performance or cell condition.
- **Affected Cells**: List of relevant cell IDs with site, score, and status.
- **KPI Evidence**: Direct numbers and statuses taken strictly from the dataset.
- **Probable Causes**: Engineering interpretations explicitly phrased as "Probable cause".
- **Recommended Checks**: Prioritized diagnostic checks for field engineers.
- **Limitations**: Explicit statement detailing boundaries and missing data assumptions.

## Safety & Grounding Guardrails (Section 36)

The safety module in `app/ai/guardrails/grounding.py`:
- Detects and flags any hallucinated cell IDs not present in the evidence.
- Softens definitive root-cause assertions into "Probable cause".
- Ensures that limitations and confidence disclaimers are present in every response.

