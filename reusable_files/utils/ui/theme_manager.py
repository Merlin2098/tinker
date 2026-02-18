"""
Theme Manager for the PySide6 UI.

Loads and applies visual themes from src/config/ui/themes JSON files.
Provides QSS stylesheet access, color lookup, and theme switching with persistence.

Adapted from reference implementation for PySide6.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):
    """
    Manages loading and application of visual themes.

    Features:
    - Loads themes from theme_light.json and theme_dark.json
    - Generates complete QSS stylesheets
    - Persists theme selection via PathCacheManager
    - Provides color and component style lookup
    - Emits signal on theme change
    - Fallback to minimal hardcoded theme if files missing

    Default theme: 'dark'
    """

    # Signal emitted when theme changes
    theme_changed = Signal(str)  # theme_name

    def __init__(self, config_dir: Optional[Path] = None, parent: Optional[QObject] = None):
        """
        Initialize the theme manager.

        Args:
            config_dir: Directory containing theme files (default: ./config/themes)
            parent: Parent QObject for Qt memory management
        """
        super().__init__(parent)

        # Determine config directory
        if config_dir is None:
            # Default to src/config/ui/themes relative to project root (src/)
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config" / "ui" / "themes"

        self.config_dir = Path(config_dir)
        self.themes_cache: Dict[str, Dict[str, Any]] = {}

        # Current theme (will be set by set_theme or loaded from cache)
        self._current_theme_name = "dark"
        self._current_theme_data: Dict[str, Any] = {}

    def initialize(self, saved_theme: Optional[str] = None):
        """
        Initialize the theme manager with a saved theme preference.

        This should be called after construction, typically with the theme
        loaded from PathCacheManager.

        Args:
            saved_theme: Theme name from cache ('light' or 'dark'), or None for default
        """
        theme_name = saved_theme if saved_theme in ['light', 'dark'] else 'dark'
        self._current_theme_name = theme_name
        self._current_theme_data = self._load_theme_file(theme_name)

    def _load_theme_file(self, theme_name: str) -> Dict[str, Any]:
        """
        Load a specific theme file.

        Args:
            theme_name: 'light' or 'dark'

        Returns:
            Dict with theme configuration
        """
        # Use cache if available
        if theme_name in self.themes_cache:
            return self.themes_cache[theme_name]

        theme_file = self.config_dir / f"theme_{theme_name}.json"

        if not theme_file.exists():
            print(f"⚠️  Theme file not found: {theme_file}")
            print(f"   Using fallback theme")
            return self._get_fallback_theme()

        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)

            # Cache the theme
            self.themes_cache[theme_name] = theme_data

            print(f"✅ Theme loaded: {theme_name}")
            return theme_data

        except Exception as e:
            print(f"❌ Error loading theme: {e}")
            return self._get_fallback_theme()

    def _get_fallback_theme(self) -> Dict[str, Any]:
        """
        Returns a minimal fallback theme (DARK).

        Returns:
            Dict with minimal configuration
        """
        return {
            "name": "fallback_dark",
            "colors": {
                "primary": "#EB2814",
                "background": "#121212",
                "surface": "#1E1E1E",
                "text": {
                    "primary": "#FFFFFF",
                    "secondary": "#A1A1AA"
                },
                "success": "#51D645",
                "warning": "#DEEC29",
                "error": "#E5097C",
                "info": "#00E2B2"
            },
            "pyqt5": {
                "stylesheet": """
                    QWidget {
                        background-color: #121212;
                        color: #FFFFFF;
                        font-family: 'Segoe UI', sans-serif;
                        font-size: 13px;
                    }
                    QPushButton {
                        background-color: #EB2814;
                        color: #FFFFFF;
                        border-radius: 4px;
                        padding: 8px 20px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #C11E0F;
                    }
                    QLineEdit {
                        background-color: #2D2D2D;
                        border: 2px solid #3F3F46;
                        border-radius: 4px;
                        padding: 8px 12px;
                        color: #FFFFFF;
                    }
                    QLineEdit:focus {
                        border-color: #EB2814;
                    }
                    QProgressBar {
                        background-color: #2D2D2D;
                        border: 1px solid #3F3F46;
                        border-radius: 4px;
                        text-align: center;
                        color: #FFFFFF;
                    }
                    QProgressBar::chunk {
                        background-color: #EB2814;
                    }
                """
            }
        }

    def get_stylesheet(self) -> str:
        """
        Get the complete QSS stylesheet for the current theme.

        Returns:
            str: QSS stylesheet ready to apply
        """
        try:
            stylesheet = self._current_theme_data.get("pyqt5", {}).get("stylesheet", "")
            return stylesheet
        except Exception as e:
            print(f"❌ Error getting stylesheet: {e}")
            return self._get_fallback_theme()["pyqt5"]["stylesheet"]

    def get_color(self, color_key: str) -> str:
        """
        Get a specific color value from the current theme.

        Supports nested keys using dot notation (e.g., 'text.primary').

        Args:
            color_key: Color key (e.g., 'primary', 'text.primary', 'success')

        Returns:
            str: Hex color code (e.g., '#EB2814')
        """
        try:
            colors = self._current_theme_data.get("colors", {})

            # Handle nested keys (e.g., 'text.primary')
            if '.' in color_key:
                keys = color_key.split('.')
                value = colors
                for key in keys:
                    value = value.get(key, {})
                return str(value) if value else "#FFFFFF"

            # Direct key
            color = colors.get(color_key, "#FFFFFF")

            # If color is a dict (nested structure), return the value itself or first key
            if isinstance(color, dict):
                return color.get('primary', "#FFFFFF")

            return color

        except Exception as e:
            print(f"❌ Error getting color '{color_key}': {e}")
            return "#FFFFFF"

    def get_component_style(self, component: str, property_name: str) -> str:
        """
        Get a specific style property for a component.

        Args:
            component: Component name (e.g., 'button', 'input', 'card')
            property_name: Property name (e.g., 'background', 'text', 'hover')

        Returns:
            str: Property value (color code or other value)
        """
        try:
            components = self._current_theme_data.get("components", {})
            component_data = components.get(component, {})
            return component_data.get(property_name, "#FFFFFF")
        except Exception as e:
            print(f"❌ Error getting component style '{component}.{property_name}': {e}")
            return "#FFFFFF"

    def get_current_theme(self) -> str:
        """
        Get the name of the current theme.

        Returns:
            str: 'light' or 'dark'
        """
        return self._current_theme_name

    def set_theme(self, theme_name: str) -> bool:
        """
        Set the current theme and emit theme_changed signal.

        The caller should save the theme preference using PathCacheManager.

        Args:
            theme_name: 'light' or 'dark'

        Returns:
            bool: True if theme was successfully loaded, False otherwise
        """
        if theme_name not in ['light', 'dark']:
            print(f"⚠️  Invalid theme name: {theme_name}. Must be 'light' or 'dark'.")
            return False

        # Load the new theme
        new_theme_data = self._load_theme_file(theme_name)

        # Update current theme
        self._current_theme_name = theme_name
        self._current_theme_data = new_theme_data

        # Emit signal for live switching
        self.theme_changed.emit(theme_name)

        print(f"🎨 Theme switched to: {theme_name}")
        return True

    def get_theme_data(self) -> Dict[str, Any]:
        """
        Get the complete current theme data dictionary.

        Returns:
            Dict with full theme configuration
        """
        return self._current_theme_data.copy()
