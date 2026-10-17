"""Structured logging for AI Telecom Copilot – RAN Engineer.

Uses loguru with separate sinks for:
  - app.log      – general application events
  - error.log    – ERROR and above
  - audit.log    – business / data-access audit trail
  - security.log – security events (file uploads, blocked files, etc.)

Never log passwords, API keys, JWT secrets, database credentials, or cloud credentials.
"""
import os
import sys
from pathlib import Path

from loguru import logger

# ---------------------------------------------------------------------------
# Log directory (writable inside Docker container or local dev)
# ---------------------------------------------------------------------------
LOG_DIR = Path(os.getenv("LOG_DIR", "/tmp/ranengineer/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Remove the default stderr sink so we control all output ourselves.
logger.remove()

# ── stdout sink (development convenience) ──────────────────────────────────
logger.add(
    sys.stdout,
    level="INFO",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "{message}"
    ),
    colorize=True,
)

# ── app.log ────────────────────────────────────────────────────────────────
logger.add(
    LOG_DIR / "app.log",
    level="INFO",
    rotation="50 MB",
    retention="30 days",
    compression="gz",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
)

# ── error.log ──────────────────────────────────────────────────────────────
logger.add(
    LOG_DIR / "error.log",
    level="ERROR",
    rotation="20 MB",
    retention="60 days",
    compression="gz",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
)

# ── audit.log ──────────────────────────────────────────────────────────────
_audit_logger = logger.bind(sink="audit")
logger.add(
    LOG_DIR / "audit.log",
    level="INFO",
    rotation="50 MB",
    retention="90 days",
    compression="gz",
    format="{time:YYYY-MM-DD HH:mm:ss} | AUDIT | {message}",
    filter=lambda record: record["extra"].get("sink") == "audit",
)

# ── security.log ───────────────────────────────────────────────────────────
_security_logger = logger.bind(sink="security")
logger.add(
    LOG_DIR / "security.log",
    level="INFO",
    rotation="20 MB",
    retention="90 days",
    compression="gz",
    format="{time:YYYY-MM-DD HH:mm:ss} | SECURITY | {message}",
    filter=lambda record: record["extra"].get("sink") == "security",
)

app_logger = logger


def audit(event: str, **context: object) -> None:
    """Write a structured entry to audit.log."""
    _audit_logger.info("event={event} {ctx}", event=event, ctx=" ".join(f"{k}={v}" for k, v in context.items()))


def security(event: str, **context: object) -> None:
    """Write a structured entry to security.log."""
    _security_logger.warning("event={event} {ctx}", event=event, ctx=" ".join(f"{k}={v}" for k, v in context.items()))


__all__ = ["app_logger", "audit", "security"]

