# Phase 1: KPI CSV Analyzer

```text
CSV upload → parser/validator → alias mapping → numeric normalization
    → threshold classification → weighted health score → rule-based probable causes
    → REST response / dashboard
```

The parser retains original CSV rows and only treats recognized KPI aliases as scoring inputs. Missing KPIs are allowed; the health score is normalized over the configured weights that are actually present. The score is an application-defined prioritization aid, not a standardized telecom metric.

The FastAPI application is a modular monolith by design. It creates extraction boundaries without the operational overhead of microservices during the MVP.
