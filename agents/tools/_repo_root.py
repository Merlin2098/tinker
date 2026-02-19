#!/usr/bin/env python3
"""
Shared project-root discovery helper for standalone agent_tools scripts.
"""

from __future__ import annotations

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__).resolve().parent).resolve()
    while current != current.parent:
        if (current / "agents").exists() and (current / "agent_framework_config.yaml").exists():
            return current
        if (current / "agent").exists():
            return current
        current = current.parent
    return (start or Path(__file__).resolve().parent).resolve()
