"""
Reusable file picker widget for PySide6 UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
)
from PySide6.QtGui import QFont


def _apply_emoji_button_style(button: QPushButton) -> None:
    button.setFixedSize(40, 36)
    button.setFont(QFont("Segoe UI Emoji", 18))
    button.setStyleSheet(
        "QPushButton { background-color: #FFF7ED; color: #111827; "
        "border: 2px solid #FB923C; border-radius: 8px; padding: 0px; }"
        "QPushButton:hover { background-color: #FFEDD5; }"
        "QPushButton:pressed { background-color: #FED7AA; }"
    )


class FilePickerWidget(QWidget):
    """
    Single file selector widget with label, read-only path, and browse button.
    """

    path_changed = Signal(str)

    def __init__(
        self,
        label_text: str,
        dialog_title: str,
        file_filter: str,
        cache_key: str,
        path_cache_manager,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._label_text = label_text
        self._dialog_title = dialog_title
        self._file_filter = file_filter
        self._cache_key = cache_key
        self._path_cache_manager = path_cache_manager

        self._line_edit: Optional[QLineEdit] = None

        self._init_ui()
        self._load_cached_path()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(self._label_text)
        label.setStyleSheet("font-weight: 600;")
        layout.addWidget(label)

        row = QHBoxLayout()
        row.setSpacing(6)

        self._line_edit = QLineEdit()
        self._line_edit.setReadOnly(True)
        self._line_edit.setPlaceholderText("Selecciona un archivo...")
        row.addWidget(self._line_edit, 1)

        browse_btn = QPushButton("📄")
        _apply_emoji_button_style(browse_btn)
        browse_btn.clicked.connect(self._on_browse_clicked)
        row.addWidget(browse_btn)

        clear_btn = QPushButton("🧹")
        _apply_emoji_button_style(clear_btn)
        clear_btn.clicked.connect(self._on_clear_clicked)
        row.addWidget(clear_btn)

        layout.addLayout(row)

    def _load_cached_path(self) -> None:
        cached = self._path_cache_manager.get_last_file(self._cache_key)
        if cached:
            self.set_path(cached, update_cache=False)

    def _on_browse_clicked(self) -> None:
        start_dir = ""
        current_path = self.path()
        if current_path and Path(current_path).exists():
            start_dir = str(Path(current_path).parent)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self._dialog_title,
            start_dir,
            self._file_filter,
        )

        if file_path:
            self.set_path(file_path, update_cache=True)

    def _on_clear_clicked(self) -> None:
        self.set_path("", update_cache=True)

    def set_path(self, path: str, update_cache: bool = True) -> None:
        if not self._line_edit:
            return
        self._line_edit.setText(path)
        if update_cache:
            self._path_cache_manager.set_last_file(self._cache_key, path)
        self.path_changed.emit(path)

    def path(self) -> str:
        if not self._line_edit:
            return ""
        return self._line_edit.text().strip()


class DirectoryPickerWidget(QWidget):
    """
    Directory selector widget with label, read-only path, and browse button.
    """

    path_changed = Signal(str)

    def __init__(
        self,
        label_text: str,
        dialog_title: str,
        cache_key: str,
        path_cache_manager,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._label_text = label_text
        self._dialog_title = dialog_title
        self._cache_key = cache_key
        self._path_cache_manager = path_cache_manager

        self._line_edit: Optional[QLineEdit] = None

        self._init_ui()
        self._load_cached_path()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(self._label_text)
        label.setStyleSheet("font-weight: 600;")
        layout.addWidget(label)

        row = QHBoxLayout()
        row.setSpacing(6)

        self._line_edit = QLineEdit()
        self._line_edit.setReadOnly(True)
        self._line_edit.setPlaceholderText("Selecciona un directorio...")
        row.addWidget(self._line_edit, 1)

        browse_btn = QPushButton("📄")
        _apply_emoji_button_style(browse_btn)
        browse_btn.clicked.connect(self._on_browse_clicked)
        row.addWidget(browse_btn)

        clear_btn = QPushButton("🧹")
        _apply_emoji_button_style(clear_btn)
        clear_btn.clicked.connect(self._on_clear_clicked)
        row.addWidget(clear_btn)

        layout.addLayout(row)

    def _load_cached_path(self) -> None:
        cached = self._path_cache_manager.get_last_file(self._cache_key)
        if cached:
            self.set_path(cached, update_cache=False)

    def _on_browse_clicked(self) -> None:
        start_dir = ""
        current_path = self.path()
        if current_path and Path(current_path).exists():
            start_dir = current_path

        selected_dir = QFileDialog.getExistingDirectory(
            self,
            self._dialog_title,
            start_dir,
        )

        if selected_dir:
            self.set_path(selected_dir, update_cache=True)

    def _on_clear_clicked(self) -> None:
        self.set_path("", update_cache=True)

    def set_path(self, path: str, update_cache: bool = True) -> None:
        if not self._line_edit:
            return
        self._line_edit.setText(path)
        if update_cache:
            self._path_cache_manager.set_last_file(self._cache_key, path)
        self.path_changed.emit(path)

    def path(self) -> str:
        if not self._line_edit:
            return ""
        return self._line_edit.text().strip()
