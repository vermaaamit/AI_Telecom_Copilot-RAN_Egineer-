"""Job store abstraction for AI Telecom Copilot – RAN Engineer.

Tracks background job state for long-running operations.
Phase 1 uses InMemoryJobStore.
Production will use RedisJobStore.

Job lifecycle: PENDING → RUNNING → COMPLETED | FAILED
"""
from __future__ import annotations

import os
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class Job:
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class JobStore(ABC):
    """Abstract job state store."""

    @abstractmethod
    def create_job(self, metadata: dict | None = None) -> Job:
        """Create and return a new PENDING job."""

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Job]:
        """Return job by ID or None."""

    @abstractmethod
    def update_job(self, job_id: str, status: JobStatus, result: Any = None, error: str | None = None) -> Optional[Job]:
        """Update job status, result, and error."""


class InMemoryJobStore(JobStore):
    """Thread-safe in-memory job store for Phase 1."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, metadata: dict | None = None) -> Job:
        now = datetime.now(UTC)
        job = Job(
            job_id=str(uuid.uuid4()),
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def update_job(self, job_id: str, status: JobStatus, result: Any = None, error: str | None = None) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = status
                job.result = result
                job.error = error
                job.updated_at = datetime.now(UTC)
        return job


class RedisJobStore(JobStore):
    """Redis-backed job store (future production use).

    Stores jobs as JSON with TTL.
    Requires: REDIS_URL environment variable.
    """

    def __init__(self, url: str | None = None, ttl: int = 3600) -> None:
        try:
            import redis  # type: ignore
        except ImportError as exc:
            raise ImportError("redis-py is required for RedisJobStore.") from exc
        redis_url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl

    def _key(self, job_id: str) -> str:
        return f"ranengineer:job:{job_id}"

    def create_job(self, metadata: dict | None = None) -> Job:
        import json

        now = datetime.now(UTC)
        job = Job(
            job_id=str(uuid.uuid4()),
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self._client.set(
            self._key(job.job_id),
            json.dumps({"job_id": job.job_id, "status": job.status, "created_at": job.created_at.isoformat(), "updated_at": job.updated_at.isoformat(), "metadata": job.metadata}),
            ex=self._ttl,
        )
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        import json

        raw = self._client.get(self._key(job_id))
        if not raw:
            return None
        data = json.loads(raw)
        return Job(
            job_id=data["job_id"],
            status=JobStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            result=data.get("result"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )

    def update_job(self, job_id: str, status: JobStatus, result: Any = None, error: str | None = None) -> Optional[Job]:
        import json

        job = self.get_job(job_id)
        if not job:
            return None
        job.status = status
        job.result = result
        job.error = error
        job.updated_at = datetime.now(UTC)
        self._client.set(
            self._key(job_id),
            json.dumps({"job_id": job.job_id, "status": job.status, "created_at": job.created_at.isoformat(), "updated_at": job.updated_at.isoformat(), "result": result, "error": error, "metadata": job.metadata}),
            ex=self._ttl,
        )
        return job


_job_store: JobStore | None = None


def get_job_store() -> JobStore:
    """Return InMemoryJobStore or RedisJobStore based on RANENGINEER_CACHE."""
    global _job_store
    if _job_store is None:
        cache_type = os.getenv("RANENGINEER_CACHE", "memory").lower()
        _job_store = RedisJobStore() if cache_type == "redis" else InMemoryJobStore()
    return _job_store


__all__ = ["Job", "JobStatus", "JobStore", "InMemoryJobStore", "RedisJobStore", "get_job_store"]

