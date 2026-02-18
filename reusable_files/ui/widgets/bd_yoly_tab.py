"""
BD Yoly pipeline tab for PySide6 UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QGroupBox,
)

from src.core.bd_yoly.orchestrator2 import run as run_bd_yoly
from src.ui.widgets.file_picker import FilePickerWidget
from src.ui.workers.pipeline_worker import PipelineWorker
from src.utils.logs import get_ui_logger


class BdYolyTab(QWidget):
    """
    UI tab to run the BD Yoly pipeline.
    """

    def __init__(
        self,
        theme_manager,
        path_cache_manager,
        monitoring_panel=None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.path_cache_manager = path_cache_manager
        self.monitoring_panel = monitoring_panel

        self._logger = get_ui_logger("tab.bd_yoly")
        self._worker: Optional[PipelineWorker] = None

        self.bd_yoly_picker: Optional[FilePickerWidget] = None
        self.homologacion_picker: Optional[FilePickerWidget] = None
        self.btn_run: Optional[QPushButton] = None
        self.lbl_status: Optional[QLabel] = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        group_box = QGroupBox("")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(10)

        self.bd_yoly_picker = FilePickerWidget(
            label_text="Seleccione el archivo BD Yoly:",
            dialog_title="Seleccionar archivo BD Yoly",
            file_filter="Excel Files (*.xlsm *.xlsx *.xls);;All Files (*.*)",
            cache_key="bd_yoly",
            path_cache_manager=self.path_cache_manager,
        )
        group_layout.addWidget(self.bd_yoly_picker)

        self.homologacion_picker = FilePickerWidget(
            label_text="Seleccione el archivo Homologación de puestos:",
            dialog_title="Seleccionar archivo Homologación de puestos",
            file_filter="Excel Files (*.xlsx *.xls);;All Files (*.*)",
            cache_key="homologacion",
            path_cache_manager=self.path_cache_manager,
        )
        group_layout.addWidget(self.homologacion_picker)

        layout.addWidget(group_box)

        self.btn_run = QPushButton("PROCESAR BD YOLY")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.clicked.connect(self._on_run_clicked)
        layout.addWidget(self.btn_run)

        self.lbl_status = QLabel("Estado: Listo")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

    def _on_run_clicked(self) -> None:
        bd_yoly_path = self.bd_yoly_picker.path() if self.bd_yoly_picker else ""
        homologacion_path = self.homologacion_picker.path() if self.homologacion_picker else ""

        if not bd_yoly_path:
            self._logger.warning("BD Yoly: archivo requerido no seleccionado.")
            QMessageBox.warning(self, "Aviso", "Por favor seleccione el archivo BD Yoly.")
            return
        if not homologacion_path:
            self._logger.warning("BD Yoly: homologacion no seleccionada.")
            QMessageBox.warning(self, "Aviso", "Por favor seleccione el archivo Homologación de puestos.")
            return

        if not Path(bd_yoly_path).exists():
            self._logger.error("BD Yoly: archivo no existe: %s", bd_yoly_path)
            QMessageBox.warning(self, "Aviso", "El archivo BD Yoly no existe.")
            return
        if not Path(homologacion_path).exists():
            self._logger.error("BD Yoly: homologacion no existe: %s", homologacion_path)
            QMessageBox.warning(self, "Aviso", "El archivo Homologación no existe.")
            return

        self._logger.info(
            "BD Yoly pipeline iniciado. BD=%s Homologacion=%s",
            bd_yoly_path,
            homologacion_path,
        )
        self._set_running(True)
        if self.monitoring_panel:
            self.monitoring_panel.reset()
            self.monitoring_panel.start_monitoring(["silver", "gold"])

        self._worker = PipelineWorker(run_bd_yoly, bd_yoly_path, homologacion_path)
        self._worker.started.connect(self._on_started)
        self._worker.finished.connect(self._on_finished)
        self._worker.error_occurred.connect(self._on_error)
        if self.monitoring_panel:
            self._worker.stage_started.connect(self.monitoring_panel.stage_started)
            self._worker.stage_finished.connect(self.monitoring_panel.stage_finished)
        self._worker.start()

    def _on_started(self) -> None:
        self._logger.info("BD Yoly pipeline en ejecucion.")
        if self.lbl_status:
            self.lbl_status.setText("Ejecutando BD Yoly...")
            self.lbl_status.setStyleSheet("color: blue;")

    def _on_finished(self, result) -> None:
        self._set_running(False)
        if self.monitoring_panel:
            self.monitoring_panel.complete_monitoring()
        if getattr(result, "success", False):
            self._logger.info(
                "BD Yoly completado. Silver=%s Gold=%s Reporte=%s",
                result.silver_dir,
                result.gold_dir,
                result.report_path,
            )
            QMessageBox.information(
                self,
                "Éxito",
                "Pipeline completado exitosamente.\n\n"
                f"Silver: {result.silver_dir}\n"
                f"Gold: {result.gold_dir}\n"
                f"Reporte: {result.report_path}\n\n"
                f"Duración: {result.statistics.get('total_duration_seconds', 0):.2f}s",
            )
            if self.lbl_status:
                self.lbl_status.setText("BD Yoly completado con éxito")
                self.lbl_status.setStyleSheet("color: green;")
        else:
            error_msg = "\n".join(result.errors) if getattr(result, "errors", None) else "Error desconocido"
            self._logger.error("BD Yoly fallo: %s", error_msg)
            QMessageBox.critical(self, "Error", f"Pipeline BD Yoly falló:\n\n{error_msg}")
            if self.lbl_status:
                self.lbl_status.setText("Error en la ejecución")
                self.lbl_status.setStyleSheet("color: red;")

        self._worker = None

    def _on_error(self, error_msg: str) -> None:
        self._logger.error("BD Yoly pipeline error: %s", error_msg)
        self._set_running(False)
        if self.monitoring_panel:
            self.monitoring_panel.complete_monitoring()
        QMessageBox.critical(self, "Error", f"Fallo en el procesamiento:\n{error_msg}")
        if self.lbl_status:
            self.lbl_status.setText("Error en la ejecución")
            self.lbl_status.setStyleSheet("color: red;")
        self._worker = None

    def _set_running(self, running: bool) -> None:
        if self.btn_run:
            self.btn_run.setEnabled(not running)
