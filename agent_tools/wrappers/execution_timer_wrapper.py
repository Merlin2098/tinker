#!/usr/bin/env python3
"""
Canonical execution wrapper for the `execution_timer` skill.
"""

from __future__ import annotations

import time
from typing import Any


def _parse_task_type(value: Any) -> str:
    if value is None:
        return "general"
    if not isinstance(value, str) or not value.strip():
        raise ValueError("task_type must be a non-empty string when provided.")
    normalized = value.strip().lower()
    if normalized not in {"general", "sql_query"}:
        raise ValueError("task_type must be one of: general, sql_query.")
    return normalized


def _parse_float(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value.strip())
        except ValueError as exc:
            raise ValueError(f"{field} must be numeric when provided.") from exc
    raise ValueError(f"{field} must be numeric when provided.")


def _format_general(elapsed_seconds: float) -> str:
    total = int(elapsed_seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _resolve_elapsed(args: dict[str, Any]) -> tuple[float, str]:
    elapsed = _parse_float(args.get("elapsed_seconds"), "elapsed_seconds")
    if elapsed is not None:
        if elapsed < 0:
            raise ValueError("elapsed_seconds must be >= 0.")
        return elapsed, "elapsed_seconds"

    started_at = _parse_float(args.get("started_at"), "started_at")
    ended_at = _parse_float(args.get("ended_at"), "ended_at")

    if started_at is None and ended_at is None:
        raise ValueError(
            "Provide either elapsed_seconds, or started_at (optionally ended_at)."
        )
    if started_at is None:
        raise ValueError("started_at is required when ended_at is provided.")
    if ended_at is None:
        ended_at = time.perf_counter()

    elapsed = ended_at - started_at
    if elapsed < 0:
        raise ValueError("ended_at must be >= started_at.")
    return elapsed, "start_end"


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    task_type = _parse_task_type(args.get("task_type"))
    elapsed_seconds, source = _resolve_elapsed(args)
    milliseconds = elapsed_seconds * 1000.0

    if task_type == "general":
        execution_time = _format_general(elapsed_seconds)
    else:
        execution_time = f"{milliseconds:.2f} ms"

    return {
        "status": "ok",
        "skill": "execution_timer",
        "task_type": task_type,
        "source": source,
        "execution_time": execution_time,
        "execution_time_seconds": elapsed_seconds,
        "execution_time_milliseconds": milliseconds,
    }
