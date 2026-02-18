"""
Path Cache Manager for the PySide6 UI.

Persists and restores file selections and user preferences to/from
src/config/json/path_cache.json.

Provides get/set API with JSON serialization.
"""

import copy
import json
from pathlib import Path
from typing import Dict, Any, Optional


class PathCacheManager:
    """
    Manages persistence and restoration of file selections and preferences.

    Features:
    - Saves last-used file paths for pipeline inputs
    - Stores user preferences (theme)
    - Handles missing or corrupt cache files gracefully
    - Automatic save on updates

    Cache location: src/config/json/path_cache.json
    """

    # Cache schema version
    CACHE_VERSION = "1.0"

    # Default cache structure
    DEFAULT_CACHE = {
        "version": CACHE_VERSION,
        "last_used_files": {
            "peoplepoint": "",
            "salesbonus": "",
            "bd_yoly": "",
            "homologacion": ""
        },
        "preferences": {
            "theme": "dark"
        }
    }

    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize the path cache manager.

        Args:
            cache_path: Path to cache file (default: config/json/path_cache.json)
        """
        if cache_path is None:
            # Default to src/config/json/path_cache.json relative to project root
            project_root = Path(__file__).parent.parent.parent
            cache_path = project_root / "config" / "json" / "path_cache.json"

        self.cache_path = Path(cache_path)
        self._cache_data: Dict[str, Any] = {}

        # Ensure directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        self.loaded_ok = self.load()

    def load(self) -> bool:
        """
        Load cache from disk.

        Returns:
            bool: True if loaded successfully, False if using default
        """
        if not self.cache_path.exists():
            print(f"ℹ️  Path cache not found. Creating new cache at: {self.cache_path}")
            self._cache_data = copy.deepcopy(self.DEFAULT_CACHE)
            self.save()  # Create the file
            return False

        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            # Validate structure and merge with defaults
            self._cache_data = self._merge_with_defaults(loaded_data)

            print(f"✅ Path cache loaded from: {self.cache_path}")
            return True

        except json.JSONDecodeError as e:
            print(f"⚠️  Corrupt cache file: {e}. Using defaults.")
            self._cache_data = copy.deepcopy(self.DEFAULT_CACHE)
            return False

        except Exception as e:
            print(f"❌ Error loading cache: {e}. Using defaults.")
            self._cache_data = copy.deepcopy(self.DEFAULT_CACHE)
            return False

    def save(self) -> bool:
        """
        Save cache to disk.

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"❌ Error saving cache: {e}")
            return False

    def _merge_with_defaults(self, loaded_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded data with default structure to handle schema evolution.

        Args:
            loaded_data: Data loaded from cache file

        Returns:
            Dict with complete structure
        """
        merged = copy.deepcopy(self.DEFAULT_CACHE)

        # Update version
        merged["version"] = loaded_data.get("version", self.CACHE_VERSION)

        # Merge last_used_files
        if "last_used_files" in loaded_data:
            merged["last_used_files"].update(loaded_data["last_used_files"])

        # Merge preferences
        if "preferences" in loaded_data:
            merged["preferences"].update(loaded_data["preferences"])

        return merged

    def get_last_files(self) -> Dict[str, str]:
        """
        Get the dictionary of last-used file paths.

        Returns:
            Dict mapping input keys to file paths (may be empty strings)
        """
        return self._cache_data.get("last_used_files", {}).copy()

    def save_last_files(self, files: Dict[str, str]) -> bool:
        """
        Save last-used file paths.

        Args:
            files: Dict mapping input keys to file paths

        Returns:
            bool: True if saved successfully
        """
        if "last_used_files" not in self._cache_data:
            self._cache_data["last_used_files"] = {}

        self._cache_data["last_used_files"].update(files)
        return self.save()

    def get_last_file(self, key: str) -> str:
        """
        Get a specific last-used file path.

        Args:
            key: Input key (e.g., 'etl_core')

        Returns:
            str: File path or empty string
        """
        return self._cache_data.get("last_used_files", {}).get(key, "")

    def set_last_file(self, key: str, path: str) -> bool:
        """
        Set a specific last-used file path.

        Args:
            key: Input key (e.g., 'etl_core')
            path: File path (absolute path as string)

        Returns:
            bool: True if saved successfully
        """
        if "last_used_files" not in self._cache_data:
            self._cache_data["last_used_files"] = {}

        self._cache_data["last_used_files"][key] = path
        return self.save()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference value.

        Args:
            key: Preference key (e.g., 'theme', 'stop_on_domain_error')
            default: Default value if key not found

        Returns:
            Preference value or default
        """
        return self._cache_data.get("preferences", {}).get(key, default)

    def set_preference(self, key: str, value: Any) -> bool:
        """
        Set a user preference value.

        Args:
            key: Preference key
            value: Preference value (must be JSON-serializable)

        Returns:
            bool: True if saved successfully
        """
        if "preferences" not in self._cache_data:
            self._cache_data["preferences"] = {}

        self._cache_data["preferences"][key] = value
        return self.save()

    def get_all_preferences(self) -> Dict[str, Any]:
        """
        Get all user preferences.

        Returns:
            Dict of all preferences
        """
        return self._cache_data.get("preferences", {}).copy()

    def clear_cache(self) -> bool:
        """
        Reset cache to defaults.

        Returns:
            bool: True if cleared successfully
        """
        self._cache_data = copy.deepcopy(self.DEFAULT_CACHE)
        return self.save()

    def get_cache_path(self) -> Path:
        """
        Get the cache file path.

        Returns:
            Path to cache file
        """
        return self.cache_path
