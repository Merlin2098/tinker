#!/usr/bin/env python3
"""
Canonical execution wrapper for the `generate_exe_pyinstaller_onedir` skill.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from agents.tools.wrappers._explorer_common import parse_bool, resolve_repo_path
except ImportError:
    from wrappers._explorer_common import parse_bool, resolve_repo_path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_repo_dir(raw_path: Any, *, field_name: str, must_exist: bool) -> tuple[str, Path]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"{field_name} is required and must be a non-empty string.")

    root = _project_root()
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{field_name} must resolve inside project root: {resolved}") from exc

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"{field_name} not found: {resolved}")
    if resolved.exists() and not resolved.is_dir():
        raise ValueError(f"{field_name} must be a directory: {resolved}")
    return str(resolved), resolved


def _parse_string_list(raw: Any, *, field_name: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"{field_name} must be a list when provided.")

    parsed: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} items must be non-empty strings.")
        parsed.append(item.strip())
    return parsed


def _tail(text: str, max_lines: int = 40) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[-max_lines:])


def run(args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ValueError("Wrapper args must be a JSON object.")

    script_path_str, script_path = resolve_repo_path(
        args.get("script_path"),
        field_name="script_path",
        allowed_suffixes={".py"},
    )
    venv_path_str, venv_path = _resolve_repo_dir(
        args.get("venv_path", ".venv"),
        field_name="venv_path",
        must_exist=True,
    )
    output_dir_str, output_dir = _resolve_repo_dir(
        args.get("output_dir", "dist"),
        field_name="output_dir",
        must_exist=False,
    )

    exe_name_raw = args.get("exe_name")
    if exe_name_raw is None:
        exe_name = script_path.stem
    elif isinstance(exe_name_raw, str) and exe_name_raw.strip():
        exe_name = exe_name_raw.strip()
    else:
        raise ValueError("exe_name must be a non-empty string when provided.")

    hidden_imports = _parse_string_list(args.get("hidden_imports"), field_name="hidden_imports")
    excludes = _parse_string_list(args.get("excludes"), field_name="excludes")

    icon_path = None
    icon_arg = args.get("icon_path")
    if icon_arg is not None:
        icon_str, icon_resolved = resolve_repo_path(
            icon_arg,
            field_name="icon_path",
            allowed_suffixes={".ico"},
        )
        icon_path = icon_resolved
    else:
        icon_str = None

    clean = parse_bool(args.get("clean"), field="clean", default=True)
    dry_run = parse_bool(args.get("dry_run"), field="dry_run", default=False)

    if sys.platform == "win32":
        venv_python = venv_path / "Scripts" / "python.exe"
    else:
        venv_python = venv_path / "bin" / "python"
    if not venv_python.exists():
        raise ValueError(f"Invalid virtual environment: Python not found at {venv_python}")

    pyvenv_cfg = venv_path / "pyvenv.cfg"
    if not pyvenv_cfg.exists():
        raise ValueError(f"Invalid virtual environment: pyvenv.cfg not found in {venv_path}")

    cmd: list[str] = [
        str(venv_python),
        "-m",
        "pyinstaller",
        "--onedir",
        "--noconsole",
        "--name",
        exe_name,
        "--distpath",
        str(output_dir),
        "--workpath",
        str(output_dir / "build"),
        "--specpath",
        str(output_dir),
    ]
    if clean:
        cmd.append("--clean")

    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])
    for module in excludes:
        cmd.extend(["--exclude-module", module])
    if icon_path is not None:
        cmd.extend(["--icon", str(icon_path)])

    cmd.append(str(script_path))

    dist_folder = output_dir / exe_name
    if sys.platform == "win32":
        executable_path = dist_folder / f"{exe_name}.exe"
    else:
        executable_path = dist_folder / exe_name

    if dry_run:
        return {
            "status": "ok",
            "skill": "generate_exe_pyinstaller_onedir",
            "dry_run": True,
            "script_path": script_path_str,
            "venv_path": venv_path_str,
            "venv_python_used": str(venv_python),
            "output_dir": output_dir_str,
            "exe_name": exe_name,
            "icon_path": icon_str,
            "hidden_imports": hidden_imports,
            "excludes": excludes,
            "clean": clean,
            "command": cmd,
            "dist_folder": str(dist_folder),
            "executable_path": str(executable_path),
        }

    output_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    if result.returncode != 0:
        stderr_tail = _tail(result.stderr, max_lines=60)
        raise RuntimeError(
            "PyInstaller build failed with exit code "
            f"{result.returncode}. stderr tail:\n{stderr_tail}"
        )

    warnings = [line.strip() for line in result.stderr.splitlines() if "WARNING" in line]

    return {
        "status": "ok",
        "skill": "generate_exe_pyinstaller_onedir",
        "dry_run": False,
        "script_path": script_path_str,
        "venv_path": venv_path_str,
        "venv_python_used": str(venv_python),
        "output_dir": output_dir_str,
        "exe_name": exe_name,
        "icon_path": icon_str,
        "hidden_imports": hidden_imports,
        "excludes": excludes,
        "clean": clean,
        "command": cmd,
        "returncode": result.returncode,
        "build_warnings": warnings,
        "stdout_tail": _tail(result.stdout),
        "stderr_tail": _tail(result.stderr),
        "dist_folder": str(dist_folder),
        "executable_path": str(executable_path),
    }

