"""
Main Window for the PySide6 UI.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

try:
    from src.ui.widgets.peoplepoint_tab import PeoplePointTab
    from src.ui.widgets.bd_yoly_tab import BdYolyTab
    from src.ui.widgets.contrast_tab import ContrastTab
    from src.ui.widgets.author_info_widget import AuthorInfoWidget
    from src.ui.widgets.monitoring_panel import MonitoringPanel
    from src.utils.ui import ThemeManager, PathCacheManager
    from src.utils.logs import get_ui_logger
    from src.utils.core import PathManager, ConfigLoader
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    from src.ui.widgets.peoplepoint_tab import PeoplePointTab
    from src.ui.widgets.bd_yoly_tab import BdYolyTab
    from src.ui.widgets.contrast_tab import ContrastTab
    from src.ui.widgets.author_info_widget import AuthorInfoWidget
    from src.ui.widgets.monitoring_panel import MonitoringPanel
    from src.utils.ui import ThemeManager, PathCacheManager
    from src.utils.logs import get_ui_logger
    from src.utils.core import PathManager, ConfigLoader


class MainWindow(QMainWindow):
    """
    Main application window for the ETL pipelines.
    """

    def __init__(self):
        super().__init__()
        self._logger = get_ui_logger("main_window")

        self.theme_manager = ThemeManager()
        self.path_cache_manager = PathCacheManager()

        self._logger.info(
            "Path cache initialized at %s (loaded=%s)",
            self.path_cache_manager.get_cache_path(),
            getattr(self.path_cache_manager, "loaded_ok", None),
        )

        saved_theme = self.path_cache_manager.get_preference("theme", "dark")
        self.theme_manager.initialize(saved_theme)
        self._logger.info(
            "Theme initialized: %s (dir=%s)",
            self.theme_manager.get_current_theme(),
            self.theme_manager.config_dir,
        )
        self._log_config_diagnostics()

        self.tabs: Optional[QTabWidget] = None
        self.author_info: Optional[AuthorInfoWidget] = None
        self.monitoring_panel: Optional[MonitoringPanel] = None
        self.theme_button: Optional[QPushButton] = None
        self._tab_names = ["People Point", "BD Yoly", "Contrast"]
        self._tab_factories = {}
        self._tab_loaded = {}
        self._is_loading_tab = False

        self._setup_window()
        self._init_ui()
        self._apply_theme()

    def _setup_window(self) -> None:
        self.setWindowTitle("Auditoria BD PeoplePoint")
        self.setMinimumSize(700, 420)

        icon_path = Path(__file__).resolve().parents[1] / "config" / "ui" / "icon" / "app.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _init_ui(self) -> None:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        scroll_area.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)

        self.author_info = AuthorInfoWidget()
        left_layout.addWidget(self.author_info)

        header_layout.addLayout(left_layout)
        header_layout.addStretch()

        self.theme_button = QPushButton()
        self.theme_button.setMaximumWidth(140)
        self.theme_button.clicked.connect(self._on_toggle_theme)
        header_layout.addWidget(self.theme_button)

        layout.addWidget(header)

        self.tabs = QTabWidget()

        self.monitoring_panel = MonitoringPanel(self.theme_manager)

        self._tab_factories = {
            "People Point": lambda: PeoplePointTab(
                self.theme_manager,
                self.path_cache_manager,
                self.monitoring_panel,
            ),
            "BD Yoly": lambda: BdYolyTab(
                self.theme_manager,
                self.path_cache_manager,
                self.monitoring_panel,
            ),
            "Contrast": lambda: ContrastTab(
                self.theme_manager,
                self.path_cache_manager,
                self.monitoring_panel,
            ),
        }

        for name in self._tab_names:
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            placeholder_layout.addWidget(QLabel("Cargando..."))
            self.tabs.addTab(placeholder, name)

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._load_tab(0)

        layout.addWidget(self.tabs)
        layout.addWidget(self.monitoring_panel)

        layout.addStretch()

        self.setCentralWidget(scroll_area)

        self.statusBar().showMessage("Listo. Selecciona archivos para comenzar.")

    def _apply_theme(self) -> None:
        self.setStyleSheet(self.theme_manager.get_stylesheet())
        if self.author_info:
            self.author_info.update_theme(self.theme_manager.get_current_theme() == "dark")
        if self.monitoring_panel:
            self.monitoring_panel.update_theme()
        self._sync_theme_button()

    def _log_config_diagnostics(self) -> None:
        try:
            path_mgr = PathManager(__file__)
            self._logger.info("Project root resolved: %s", path_mgr.project_root)

            total_dirs = 0
            missing_dirs = 0
            total_files = 0
            missing_files = 0
            load_errors = 0

            dirs = [
                ("config.yamls", path_mgr.project_root / "src" / "config" / "yaml"),
                ("config.json", path_mgr.project_root / "src" / "config" / "json"),
                ("config.sql", path_mgr.project_root / "src" / "config" / "sql"),
                ("config.ui", path_mgr.project_root / "src" / "config" / "ui"),
                ("config.ui.themes", path_mgr.project_root / "src" / "config" / "ui" / "themes"),
            ]
            for label, path in dirs:
                total_dirs += 1
                if path.exists():
                    self._logger.info("Config directory OK: %s -> %s", label, path)
                else:
                    missing_dirs += 1
                    self._logger.warning("Config directory MISSING: %s -> %s", label, path)

            yaml_files = [
                "step1_peoplepoint.yaml",
                "step1_salesbonus.yaml",
                "step2_peoplepoint.yaml",
                "step1_bd.yaml",
                "step1_homologapuestos.yaml",
                "step2_bd.yaml",
                "bronze_peoplepoint.yaml",
                "bronze_bd_yoly.yaml",
                "bronze_homologacion.yaml",
                "bronze_to_silver_peoplepoint.yaml",
                "bronze_to_silver_bd_yoly.yaml",
                "bronze_to_silver_homologacion.yaml",
                "contrast_gold.yaml",
            ]
            json_files = [
                "peoplepoint_mappings.json",
                "bd_yoly_mappings.json",
                "homologacion_mappings.json",
                "contrast_gold.json",
                "path_cache.json",
            ]
            sql_files = [
                "validate_peoplepoint.sql",
                "validate_bd.sql",
                "contrast_gold.sql",
                "peoplepoint_transform.sql",
                "bd_yoly_transform.sql",
                "homologacion_transform.sql",
            ]

            def check_and_load(filename: str, config_type: str, load: bool) -> None:
                nonlocal total_files, missing_files, load_errors
                total_files += 1
                path = path_mgr.resolve_config_path(filename, config_type)
                label = f"{config_type}:{filename}"
                if not path:
                    missing_files += 1
                    self._logger.error("Config missing: %s", label)
                    return
                self._logger.info("Config found: %s -> %s", label, path)
                if not load:
                    return
                try:
                    ConfigLoader(str(path))
                    self._logger.info("Config loaded: %s", label)
                except Exception as exc:
                    load_errors += 1
                    self._logger.error("Config load failed: %s (%s)", label, exc, exc_info=True)

            for filename in yaml_files:
                check_and_load(filename, "yaml", load=True)
            for filename in json_files:
                check_and_load(filename, "json", load=True)
            for filename in sql_files:
                check_and_load(filename, "sql", load=False)

            self._logger.info(
                "Config diagnostics summary: dirs_ok=%s dirs_missing=%s files_ok=%s files_missing=%s load_errors=%s",
                total_dirs - missing_dirs,
                missing_dirs,
                total_files - missing_files,
                missing_files,
                load_errors,
            )
        except Exception as exc:
            self._logger.error("Config diagnostics failed: %s", exc, exc_info=True)

    def _sync_theme_button(self) -> None:
        if not self.theme_button:
            return
        current_theme = self.theme_manager.get_current_theme()
        label = "Tema: Claro" if current_theme == "dark" else "Tema: Oscuro"
        self.theme_button.setText(label)

    def _on_toggle_theme(self) -> None:
        current_theme = self.theme_manager.get_current_theme()
        new_theme = "light" if current_theme == "dark" else "dark"
        if self.theme_manager.set_theme(new_theme):
            self.path_cache_manager.set_preference("theme", new_theme)
            self._apply_theme()
            self._logger.info("Theme switched to %s", new_theme)

    def _on_tab_changed(self, index: int) -> None:
        if self._is_loading_tab:
            return
        self._load_tab(index)

    def _load_tab(self, index: int) -> None:
        if index < 0 or index >= len(self._tab_names):
            return
        name = self._tab_names[index]
        if self._tab_loaded.get(name):
            return

        factory = self._tab_factories.get(name)
        if factory is None:
            return

        self._is_loading_tab = True
        widget = factory()
        self.tabs.removeTab(index)
        self.tabs.insertTab(index, widget, name)
        self.tabs.setCurrentIndex(index)
        self._tab_loaded[name] = True
        self._is_loading_tab = False
        self._logger.info("Tab loaded: %s", name)
