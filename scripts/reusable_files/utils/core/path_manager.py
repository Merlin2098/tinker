from __future__ import annotations

from pathlib import Path


class PathManager:
    """Project-aware path resolver."""

    def __init__(self, anchor_file: str | Path | None = None) -> None:
        self.anchor_file = Path(anchor_file).resolve() if anchor_file else None
        self.project_root = self._detect_project_root()

    def _detect_project_root(self) -> Path:
        markers = {".gitignore", "main.py", "requirements.txt", "pyproject.toml"}

        if self.anchor_file:
            current = self.anchor_file.parent
            for _ in range(12):
                if any((current / marker).exists() for marker in markers):
                    return current
                if current.parent == current:
                    break
                current = current.parent

        return Path.cwd().resolve()

    def project_path(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.project_root / path

    def resolve_config_path(
        self,
        config_ref: str | Path,
        *,
        yaml_path: str | Path | None = None,
        default_dir: str | Path | None = None,
    ) -> Path:
        raw = Path(config_ref)
        if raw.is_absolute():
            return raw

        candidates: list[Path] = [self.project_path(raw)]
        if yaml_path is not None:
            candidates.append(Path(yaml_path).resolve().parent / raw)
        if default_dir is not None:
            candidates.append(self.project_path(default_dir) / raw.name)

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def ensure_dir(self, value: str | Path) -> Path:
        path = self.project_path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path
