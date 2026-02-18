"""
Monitoring Panel for ETL stage progress (bronze / silver / gold).
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QGroupBox,
    QGridLayout,
)
from PySide6.QtCore import QTimer, Qt


class MonitoringPanel(QWidget):
    """
    Displays ETL stage progress for a pipeline run.
    """

    def __init__(self, theme_manager, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.theme_manager = theme_manager

        self.stages: List[str] = []
        self.stage_statuses: Dict[str, str] = {}
        self.completed_count = 0
        self.start_time: Optional[datetime] = None

        self.progress_bar: Optional[QProgressBar] = None
        self.elapsed_label: Optional[QLabel] = None
        self.current_status_label: Optional[QLabel] = None
        self._stage_layout: Optional[QGridLayout] = None
        self._stage_labels: Dict[str, QLabel] = {}

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_elapsed_time)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group_box = QGroupBox("Progreso ETL")
        group_layout = QVBoxLayout(group_box)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(3)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Esperando inicio...")
        group_layout.addWidget(self.progress_bar)

        stats_layout = QGridLayout()
        stats_layout.addWidget(QLabel("Tiempo Transcurrido:"), 0, 0)
        self.elapsed_label = QLabel("00:00:00")
        stats_layout.addWidget(self.elapsed_label, 0, 1)
        group_layout.addLayout(stats_layout)

        self._stage_layout = QGridLayout()
        group_layout.addLayout(self._stage_layout)

        self.current_status_label = QLabel("Estado: Inactivo")
        self.current_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_status_label.setStyleSheet("font-style: italic;")
        group_layout.addWidget(self.current_status_label)

        layout.addWidget(group_box)
        self.update_theme()

    def start_monitoring(self, stages: List[str]) -> None:
        self.stages = stages[:]
        self.stage_statuses = {stage: "pending" for stage in self.stages}
        self.completed_count = 0
        self.start_time = datetime.now()

        self.progress_bar.setMaximum(max(len(self.stages), 1))
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0%")

        self._build_stage_rows()
        self._update_stage_labels()
        self.current_status_label.setText("Estado: Ejecutando...")

        self.timer.start(1000)

    def stage_started(self, stage: str) -> None:
        if stage not in self.stage_statuses:
            return
        self.stage_statuses[stage] = "running"
        self._update_stage_labels()

    def stage_finished(self, stage: str, success: bool) -> None:
        if stage not in self.stage_statuses:
            return
        self.stage_statuses[stage] = "done" if success else "failed"
        self.completed_count = len([s for s in self.stage_statuses.values() if s in {"done", "failed"}])
        self._update_progress()
        self._update_stage_labels()

    def complete_monitoring(self) -> None:
        self.timer.stop()
        if self.stages:
            self.progress_bar.setValue(self.completed_count)
            percentage = int((self.completed_count / len(self.stages)) * 100) if self.stages else 0
            self.progress_bar.setFormat(f"{percentage}% ({self.completed_count}/{len(self.stages)})")
        self.current_status_label.setText("Estado: Completado")

    def reset(self) -> None:
        self.timer.stop()
        self.stages = []
        self.stage_statuses = {}
        self.completed_count = 0
        self.start_time = None
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Esperando inicio...")
        self.elapsed_label.setText("00:00:00")
        self.current_status_label.setText("Estado: Inactivo")
        self._clear_stage_rows()

    def update_theme(self) -> None:
        if self.elapsed_label:
            self.elapsed_label.setStyleSheet(
                f"color: {self.theme_manager.get_color('info')}; font-weight: bold;"
            )
        self._update_stage_labels()

    def _update_elapsed_time(self) -> None:
        if self.start_time is None:
            return
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.elapsed_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _build_stage_rows(self) -> None:
        self._clear_stage_rows()
        if not self._stage_layout:
            return
        for idx, stage in enumerate(self.stages):
            label = QLabel(stage.capitalize())
            status = QLabel("Pendiente")
            self._stage_layout.addWidget(label, idx, 0)
            self._stage_layout.addWidget(status, idx, 1)
            self._stage_labels[stage] = status

    def _clear_stage_rows(self) -> None:
        if not self._stage_layout:
            return
        while self._stage_layout.count():
            item = self._stage_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._stage_labels = {}

    def _update_progress(self) -> None:
        if not self.stages:
            return
        percentage = int((self.completed_count / len(self.stages)) * 100)
        self.progress_bar.setValue(self.completed_count)
        self.progress_bar.setFormat(f"{percentage}% ({self.completed_count}/{len(self.stages)})")

    def _update_stage_labels(self) -> None:
        status_colors = {
            "pending": self.theme_manager.get_color("text.secondary"),
            "running": self.theme_manager.get_color("info"),
            "done": self.theme_manager.get_color("success"),
            "failed": self.theme_manager.get_color("error"),
        }

        for stage, label in self._stage_labels.items():
            status = self.stage_statuses.get(stage, "pending")
            text_map = {
                "pending": "Pendiente",
                "running": "En progreso",
                "done": "Completado",
                "failed": "Fallido",
            }
            label.setText(text_map.get(status, status))
            color = status_colors.get(status, "#FFFFFF")
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
