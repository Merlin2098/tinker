"""
PeoplePoint pipeline tab for PySide6 UI.
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

from src.core.people_point.orchestrator1 import run as run_peoplepoint
from src.core.people_point.config_validator import validate_configs, ConfigValidationError
from src.ui.widgets.file_picker import FilePickerWidget
from src.ui.workers.pipeline_worker import PipelineWorker
from src.utils.logs import get_ui_logger


class PeoplePointTab(QWidget):
    """
    UI tab to run the PeoplePoint pipeline.
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

        self._logger = get_ui_logger("tab.peoplepoint")
        self._config_valid = True
        self._worker: Optional[PipelineWorker] = None

        self.peoplepoint_picker: Optional[FilePickerWidget] = None
        self.salesbonus_picker: Optional[FilePickerWidget] = None
        self.btn_run: Optional[QPushButton] = None
        self.lbl_status: Optional[QLabel] = None

        self._init_ui()
        self._validate_configs()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        group_box = QGroupBox("")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(10)

        self.peoplepoint_picker = FilePickerWidget(
            label_text="Seleccione el reporte de PeoplePoint:",
            dialog_title="Seleccionar archivo Excel de PeoplePoint",
            file_filter="Excel Files (*.xlsx *.xls);;All Files (*.*)",
            cache_key="peoplepoint",
            path_cache_manager=self.path_cache_manager,
        )
        group_layout.addWidget(self.peoplepoint_picker)

        self.salesbonus_picker = FilePickerWidget(
            label_text="Seleccione el reporte de Sales Bonus:",
            dialog_title="Seleccionar archivo Excel de Sales Bonus",
            file_filter="Excel Files (*.xlsx *.xls);;All Files (*.*)",
            cache_key="salesbonus",
            path_cache_manager=self.path_cache_manager,
        )
        group_layout.addWidget(self.salesbonus_picker)

        layout.addWidget(group_box)

        self.btn_run = QPushButton("PROCESAR PIPELINE ETL")
        self.btn_run.setMinimumHeight(40)
        self.btn_run.clicked.connect(self._on_run_clicked)
        layout.addWidget(self.btn_run)

        self.lbl_status = QLabel("Estado: Listo")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

    def _validate_configs(self) -> None:
        try:
            validate_configs()
            self._config_valid = True
            self._logger.info("Configuracion PeoplePoint validada correctamente.")
            if self.lbl_status:
                self.lbl_status.setText("Estado: Listo (configuración validada)")
                self.lbl_status.setStyleSheet("color: green;")
        except ConfigValidationError as exc:
            self._config_valid = False
            self._logger.error("Error de configuracion PeoplePoint: %s", exc, exc_info=True)
            if self.btn_run:
                self.btn_run.setEnabled(False)
            if self.lbl_status:
                self.lbl_status.setText("Estado: Error de configuración")
                self.lbl_status.setStyleSheet("color: red;")
            QMessageBox.critical(
                self,
                "Error de Configuración",
                f"No se pudo inicializar el pipeline.\n\n{exc}",
            )

    def _on_run_clicked(self) -> None:
        if not self._config_valid:
            self._logger.warning("Intento de ejecucion con configuracion invalida.")
            QMessageBox.critical(
                self,
                "Error",
                "La configuración del pipeline no es válida.\n"
                "Por favor revise los archivos de configuración.",
            )
            return

        peoplepoint_path = self.peoplepoint_picker.path() if self.peoplepoint_picker else ""
        salesbonus_path = self.salesbonus_picker.path() if self.salesbonus_picker else ""

        if not peoplepoint_path:
            self._logger.warning("PeoplePoint: archivo requerido no seleccionado.")
            QMessageBox.warning(self, "Aviso", "Por favor seleccione el archivo de PeoplePoint.")
            return
        if not salesbonus_path:
            self._logger.warning("PeoplePoint: Sales Bonus no seleccionado.")
            QMessageBox.warning(self, "Aviso", "Por favor seleccione el archivo de Sales Bonus.")
            return

        if not Path(peoplepoint_path).exists():
            self._logger.error("PeoplePoint: archivo no existe: %s", peoplepoint_path)
            QMessageBox.warning(self, "Aviso", "El archivo de PeoplePoint no existe.")
            return
        if not Path(salesbonus_path).exists():
            self._logger.error("PeoplePoint: archivo Sales Bonus no existe: %s", salesbonus_path)
            QMessageBox.warning(self, "Aviso", "El archivo de Sales Bonus no existe.")
            return

        self._logger.info(
            "PeoplePoint pipeline iniciado. PeoplePoint=%s SalesBonus=%s",
            peoplepoint_path,
            salesbonus_path,
        )
        self._set_running(True)
        if self.monitoring_panel:
            self.monitoring_panel.reset()
            self.monitoring_panel.start_monitoring(["silver", "gold"])

        self._worker = PipelineWorker(run_peoplepoint, peoplepoint_path, salesbonus_path)
        self._worker.started.connect(self._on_started)
        self._worker.finished.connect(self._on_finished)
        self._worker.error_occurred.connect(self._on_error)
        if self.monitoring_panel:
            self._worker.stage_started.connect(self.monitoring_panel.stage_started)
            self._worker.stage_finished.connect(self.monitoring_panel.stage_finished)
        self._worker.start()

    def _on_started(self) -> None:
        self._logger.info("PeoplePoint pipeline en ejecucion.")
        if self.lbl_status:
            self.lbl_status.setText("Ejecutando pipeline ETL...")
            self.lbl_status.setStyleSheet("color: blue;")

    def _on_finished(self, result) -> None:
        self._set_running(False)
        if self.monitoring_panel:
            self.monitoring_panel.complete_monitoring()
        if getattr(result, "success", False):
            self._logger.info(
                "PeoplePoint pipeline completado. Silver=%s Gold=%s Reporte=%s",
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
                self.lbl_status.setText("Pipeline completado con éxito")
                self.lbl_status.setStyleSheet("color: green;")
        else:
            error_msg = "\n".join(result.errors) if getattr(result, "errors", None) else "Error desconocido"
            self._logger.error("PeoplePoint pipeline fallo: %s", error_msg)
            QMessageBox.critical(self, "Error", f"Pipeline falló:\n\n{error_msg}")
            if self.lbl_status:
                self.lbl_status.setText("Error en la ejecución")
                self.lbl_status.setStyleSheet("color: red;")

        self._worker = None

    def _on_error(self, error_msg: str) -> None:
        self._logger.error("PeoplePoint pipeline error: %s", error_msg)
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
