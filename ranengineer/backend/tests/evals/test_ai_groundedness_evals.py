"""AI Groundedness, Faithfulness, and Hallucination Prevention Evaluations.

Based on project.txt Section 45:
- Relevance
- Faithfulness
- Groundedness
- Hallucination prevention
- RAG standards grounding
- Tool correctness and parameter integrity
- RCA quality and deterministic rule enforcement
"""
import pytest
from app.ai.guardrails.grounding import verify_grounding, apply_guardrails
from app.ai.intent import parse_intent
from app.ai.tools.analytics_tools import find_bad_cells, get_cell_analysis, filter_cells_by_kpi
from app.ai.rag.retriever import RanKnowledgeRetriever
from app.analytics.anomaly.rules import probable_causes


EVIDENCE = {
    "intent": "find_bad_cells",
    "items": [
        {"cell_id": "CELL101", "health_score": 28, "status": "CRITICAL"},
        {"cell_id": "CELL102", "health_score": 39, "status": "CRITICAL"},
        {"cell_id": "CELL103", "health_score": 75, "status": "GOOD"},
    ],
}


class TestAIGroundednessAndHallucination:
    """Verifies that AI components strictly adhere to deterministic boundaries."""

    def test_guardrail_blocks_nonexistent_cell_hallucination(self):
        """Guardrail must reject responses referencing cell IDs not present in evidence."""
        fabricated_text = (
            "Summary: CELL101 and CELL999 are experiencing heavy degradation.\n"
            "Probable cause: hardware outage.\n"
            "Limitations: Based on telemetry."
        )
        report = verify_grounding(fabricated_text, EVIDENCE)
        assert report["is_grounded"] is False
        assert any("CELL999" in v for v in report["violations"])

    def test_guardrail_accepts_verified_cell_references(self):
        """Guardrail must accept responses that reference only verified evidence cells."""
        valid_text = (
            "Summary: CELL101 exhibits critical health score of 28.\n"
            "Probable cause: High PRB utilization and low throughput.\n"
            "Limitations: Based only on provided dataset telemetry."
        )
        report = verify_grounding(valid_text, EVIDENCE)
        assert report["is_grounded"] is True
        assert len(report["violations"]) == 0

    def test_guardrail_softens_definitive_hallucinatory_claims(self):
        """Guardrails must soften assertive claims like 'the root cause is definitely...'."""
        definitive_text = "The root cause is definitely caused by faulty antenna for CELL101."
        sanitized, report = apply_guardrails(definitive_text, EVIDENCE)
        assert "The probable root cause is" in sanitized or "probable" in sanitized.lower()
        assert "Limitations:" in sanitized

    def test_rag_retriever_grounded_in_3gpp_specifications(self):
        """RAG search returns accurate standards documents matching domain queries."""
        retriever = RanKnowledgeRetriever()
        res = retriever.search_ran_knowledge("handover ping-pong hysteresis A3 event", limit=3)
        assert res.total_matched > 0
        top = res.documents[0]
        assert any(term in top.title.lower() or term in top.content.lower() for term in ["handover", "mobility", "38.331", "36.331", "hysteresis"])
        assert top.domain.upper() in ["MOBILITY", "RADIO_RESOURCE_MANAGEMENT", "3GPP", "O-RAN"]

    def test_rag_retriever_power_saving_standards_grounding(self):
        """RAG retriever returns O-RAN / 3GPP energy efficiency specs for sleep mode queries."""
        retriever = RanKnowledgeRetriever()
        res = retriever.search_ran_knowledge("energy saving carrier sleep mode underlay coverage", limit=3)
        assert res.total_matched > 0
        titles_combined = " ".join([r.title.lower() + " " + r.content.lower() for r in res.documents])
        assert any(term in titles_combined for term in ["energy", "saving", "power", "sleep", "o-ran", "coverage", "carrier"])

    def test_tool_deterministic_execution_fidelity(self):
        """Analytics tool must compute exact math matching raw cell input without drift."""
        dataset = {
            "id": "ds-001",
            "cells": [
                {"cell_id": "CELL101", "health_score": 35.0, "status": "CRITICAL"},
                {"cell_id": "CELL102", "health_score": 85.0, "status": "GOOD"},
                {"cell_id": "CELL103", "health_score": 45.0, "status": "CRITICAL"},
            ]
        }
        res = find_bad_cells(dataset, limit=2)
        assert len(res["items"]) == 2
        assert res["items"][0]["cell_id"] == "CELL101"
        assert res["items"][1]["cell_id"] == "CELL103"
        assert res["total_matched"] == 2

    def test_intent_parser_telecom_domain_accuracy(self):
        """Intent parser correctly categorizes queries without hallucinating intent."""
        # Bad cells intent
        res1 = parse_intent("Which cells are performing badly?")
        assert res1.name == "find_bad_cells"

        # Cell analysis intent
        res2 = parse_intent("Why is CELL_045 performing badly? Give me root cause")
        assert res2.name == "cell_analysis"
        assert res2.target_id == "CELL_045"

        # Compare cells intent
        res3 = parse_intent("Compare CELL_001 and CELL_002")
        assert res3.name == "compare_cells"
        assert res3.target_id == "CELL_001"
        assert res3.target_id_2 == "CELL_002"

    def test_deterministic_rca_evidence_groundedness(self):
        """RCA rule engine must output concrete KPI evidence matching triggering thresholds."""
        kpi_statuses = {
            "rsrp": "CRITICAL",
            "sinr": "CRITICAL",
            "prb_utilization": "HEALTHY",
        }
        causes = probable_causes(kpi_statuses)
        assert len(causes) > 0
        assert any("Coverage degradation or interference" in c["probable_cause"] for c in causes)
        for c in causes:
            assert "recommended_checks" in c
            assert len(c["recommended_checks"]) > 0

