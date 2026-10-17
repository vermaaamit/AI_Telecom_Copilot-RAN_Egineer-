import re
from typing import Any


def extract_cell_ids_from_text(text: str) -> set[str]:
    matches = re.findall(r"\b(?!(?:cell|cells)\b)(?:cell|gnb|enb)[-_]?[a-zA-Z0-9]+\b", text, re.IGNORECASE)
    return {m.upper() for m in matches}




def get_known_cells_from_evidence(evidence: dict[str, Any]) -> set[str]:
    known = set()
    if "cell" in evidence and evidence["cell"]:
        known.add(evidence["cell"].get("cell_id", "").upper())
    if "items" in evidence:
        for item in evidence["items"]:
            if isinstance(item, dict) and "cell_id" in item:
                known.add(item["cell_id"].upper())
    return known


def verify_grounding(response_text: str, evidence: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    violations: list[str] = []

    # 1. Check for ungrounded cell references
    mentioned_cells = extract_cell_ids_from_text(response_text)
    known_cells = get_known_cells_from_evidence(evidence)
    if known_cells:
        unknown_cells = mentioned_cells - known_cells
        if unknown_cells:
            violations.append(f"Response mentioned cell IDs not found in evidence: {', '.join(sorted(unknown_cells))}")

    # 2. Check for absolute root cause assertions without 'probable' qualification
    lower_text = response_text.lower()
    definitive_patterns = [
        r"\bdefinitely caused by\b",
        r"\bthe root cause is\b",
        r"\bproven root cause\b",
        r"\bconclusively caused\b",
    ]
    for pattern in definitive_patterns:
        if re.search(pattern, lower_text):
            violations.append("Response claimed definitive root cause instead of using 'Probable cause'.")

    # 3. Check that Limitations or Confidence statement is present
    if "limitation" not in lower_text and "confidence" not in lower_text:
        warnings.append("Response lacks explicit Limitations or Confidence section.")

    # 4. Check for 'Probable cause' usage when making inferences
    if "cause" in lower_text and "probable" not in lower_text and "rule" not in lower_text:
        warnings.append("Inferences about causes should use 'Probable cause' phrasing.")

    is_grounded = len(violations) == 0
    return {
        "is_grounded": is_grounded,
        "violations": violations,
        "warnings": warnings,
    }


def apply_guardrails(response_text: str, evidence: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    report = verify_grounding(response_text, evidence)
    sanitized_text = response_text

    # Automatically soften definitive claims if detected
    sanitized_text = re.sub(r"(?i)\bthe root cause is\b", "The probable root cause is", sanitized_text)
    sanitized_text = re.sub(r"(?i)\bdefinitely caused by\b", "probably caused by", sanitized_text)

    # Append standard limitation disclaimer if omitted
    if "limitation" not in sanitized_text.lower():
        sanitized_text += "\n\nLimitations: This analysis is based strictly on the uploaded KPI dataset and rule-based engineering inferences."

    return sanitized_text, report
