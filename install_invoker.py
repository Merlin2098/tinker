#!/usr/bin/env python3
"""
Backward-compatible installer entrypoint.
Use install_tinker.py as the canonical command.
"""

from __future__ import annotations

from install_tinker import main


if __name__ == "__main__":
    raise SystemExit(main())
