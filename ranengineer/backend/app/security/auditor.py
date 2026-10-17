"""Security Threat Monitoring, Prompt Injection Guardrails & Audit Logging (Section 32)."""
from datetime import datetime, timezone
import re
import threading
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from app.logging import app_logger

# Known prompt injection & jailbreak signature patterns
PROMPT_INJECTION_PATTERNS = [
    (r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)", "INSTRUCTION_OVERRIDE"),
    (r"(reveal|show|display|print)\s+(the\s+)?(system\s+prompt|initial\s+prompt|secret\s+instructions)", "PROMPT_LEAK_ATTEMPT"),
    (r"you\s+are\s+now\s+(DAN|unrestricted|jailbroken|an\s+unfiltered)", "JAILBREAK_ATTEMPT"),
    (r"(drop|delete|truncate)\s+(table|database|from\s+cells|from\s+alarms)", "SQL_INJECTION_ATTEMPT"),
    (r"eval\s*\(|exec\s*\(|__import__|\bshutil\b|\bos\.system\b", "COMMAND_INJECTION_ATTEMPT"),
    (r"bypass\s+.*?(telecom|security|guardrails?|safety|rules?)", "GUARDRAIL_BYPASS_ATTEMPT"),
]


class PromptInspectionResult(BaseModel):
    is_safe: bool = True
    threat_detected: Optional[str] = None
    risk_score: float = 0.0
    matched_pattern: Optional[str] = None
    sanitized_text: str


class SecurityAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"SEC-{uuid.uuid4().hex[:8].upper()}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str
    severity: str  # INFO, WARNING, CRITICAL
    actor: str
    description: str
    details: Dict[str, Any] = Field(default_factory=dict)


class SecurityAuditor:
    """Thread-safe security auditor and threat detector."""

    def __init__(self, max_history: int = 200):
        self.max_history = max_history
        self._lock = threading.Lock()
        self._audit_log: List[SecurityAuditEvent] = []
        self._seed_default_events()

    def _seed_default_events(self):
        """Initial audit trail markers."""
        self.record_event(
            event_type="SYSTEM_INITIALIZATION",
            severity="INFO",
            actor="SYSTEM",
            description="Security auditing engine and Redis counter protection initialized.",
            details={"version": "1.0.0-phase7"},
        )

    def inspect_prompt(self, text: str) -> PromptInspectionResult:
        """Evaluates user input for adversarial prompt injection patterns."""
        if not text:
            return PromptInspectionResult(is_safe=True, risk_score=0.0, sanitized_text="")

        normalized = text.lower()
        for pattern, threat_type in PROMPT_INJECTION_PATTERNS:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                self.record_event(
                    event_type="PROMPT_INJECTION_DETECTED",
                    severity="WARNING",
                    actor="COPILOT_USER",
                    description=f"Potential prompt injection detected: {threat_type}",
                    details={"matched": match.group(0), "threat": threat_type},
                )
                return PromptInspectionResult(
                    is_safe=False,
                    threat_detected=threat_type,
                    risk_score=0.95,
                    matched_pattern=pattern,
                    sanitized_text="[BLOCKED: Adversarial prompt pattern detected.]",
                )

        return PromptInspectionResult(
            is_safe=True,
            threat_detected=None,
            risk_score=0.05,
            matched_pattern=None,
            sanitized_text=text,
        )

    def record_event(
        self,
        event_type: str,
        severity: str,
        actor: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityAuditEvent:
        """Records and logs a structured security event."""
        event = SecurityAuditEvent(
            event_type=event_type,
            severity=severity,
            actor=actor,
            description=description,
            details=details or {},
        )
        with self._lock:
            self._audit_log.append(event)
            if len(self._audit_log) > self.max_history:
                self._audit_log.pop(0)

        app_logger.info(
            "SECURITY_AUDIT id={} type={} severity={} actor={} desc={}",
            event.event_id,
            event.event_type,
            event.severity,
            event.actor,
            event.description,
        )
        return event

    def list_events(self, limit: int = 50, severity: Optional[str] = None) -> List[SecurityAuditEvent]:
        """Lists recent audit events, most recent first."""
        with self._lock:
            items = list(self._audit_log)
        if severity:
            items = [e for e in items if e.severity.upper() == severity.upper()]
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items[:limit]


# Global singleton
_security_auditor: Optional[SecurityAuditor] = None


def get_security_auditor() -> SecurityAuditor:
    global _security_auditor
    if _security_auditor is None:
        _security_auditor = SecurityAuditor()
    return _security_auditor
