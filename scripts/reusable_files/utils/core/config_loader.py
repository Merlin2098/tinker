from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class ConfigLoader:
    """Centralized YAML and JSON loader with simple key-path access."""

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self.config: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        suffix = self.config_path.suffix.lower()
        with self.config_path.open("r", encoding="utf-8") as handle:
            if suffix in {".yaml", ".yml"}:
                data = yaml.safe_load(handle) or {}
            elif suffix == ".json":
                data = json.load(handle)
            else:
                raise ValueError(f"Unsupported config format: {suffix}")

        if not isinstance(data, dict):
            raise ValueError(f"Config content must be an object/mapping: {self.config_path}")
        return data

    def get(self, key_path: str, default: Any = None) -> Any:
        value: Any = self.config
        for key in key_path.split("."):
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    @staticmethod
    def load_yaml(path: str | Path) -> dict[str, Any]:
        return ConfigLoader(path).config

    @staticmethod
    def load_json(path: str | Path) -> dict[str, Any]:
        return ConfigLoader(path).config
