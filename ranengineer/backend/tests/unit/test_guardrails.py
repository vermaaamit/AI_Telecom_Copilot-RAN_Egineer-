from app.ai.guardrails.grounding import apply_guardrails, verify_grounding

EVIDENCE = {
    "intent": "find_bad_cells",
    "items": [
        {"cell_id": "CELL102", "health_score": 28, "status": "CRITICAL"},
        {"cell_id": "CELL221", "health_score": 39, "status": "CRITICAL"},
    ],
}


def test_verify_grounding_passes_valid_response() -> None:
    text = (
        "Summary: CELL102 and CELL221 are degraded.\n"
        "Probable cause: coverage issue.\n"
        "Limitations: Based only on provided dataset."
    )
    report = verify_grounding(text, EVIDENCE)
    assert report["is_grounded"] is True
    assert len(report["violations"]) == 0


def test_verify_grounding_catches_hallucinated_cell_id() -> None:
    text = (
        "Summary: CELL102 and CELL999 are critical.\n"
        "Probable cause: radio degradation.\n"
        "Limitations: dataset only."
    )
    report = verify_grounding(text, EVIDENCE)
    assert report["is_grounded"] is False
    assert any("CELL999" in v for v in report["violations"])


def test_verify_grounding_flags_definitive_root_cause() -> None:
    text = (
        "Summary: CELL102 is critical.\n"
        "The root cause is definitely caused by broken feeder cable.\n"
        "Limitations: dataset only."
    )
    report = verify_grounding(text, EVIDENCE)
    assert report["is_grounded"] is False
    assert any("definitive root cause" in v for v in report["violations"])


def test_apply_guardrails_softens_definitive_claims() -> None:
    text = "The root cause is fiber cut for CELL102."
    sanitized, report = apply_guardrails(text, EVIDENCE)
    assert "The probable root cause is" in sanitized
    assert "Limitations:" in sanitized

