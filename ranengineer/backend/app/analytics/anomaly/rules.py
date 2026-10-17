from app.analytics.rules.engine import get_rule_engine


def probable_causes(kpi_statuses: dict[str, str]) -> list[dict[str, object]]:
    """Evaluates probable root causes using the dedicated configuration-driven RAN rule engine."""
    engine = get_rule_engine()
    return engine.get_probable_causes(kpi_statuses=kpi_statuses)
