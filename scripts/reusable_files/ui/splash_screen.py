"""
Splash Screen for the PySide6 UI.

Loading splash screen with app icon, title, and progress bar.
"""

from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap


class SplashScreen(QWidget):
    """
    Loading splash screen shown during application initialization.
    """

    finished = Signal()

    APP_TITLE = "Auditoria BD PeoplePoint"
    APP_SUBTITLE = "Metso MSK"
    APP_VERSION = "v1.0"

    LOADING_MESSAGES = [
        "Iniciando aplicacion...",
        "Cargando temas...",
        "Inicializando interfaz...",
        "Listo!",
    ]

    def __init__(self):
        super().__init__()

        self._progress = 0
        self._message_index = 0

        self.timer: QTimer = None
        self.message_label: QLabel = None
        self.progress_bar: QProgressBar = None

        self._init_ui()
        self._center_on_screen()
        self._setup_timer()

    def _init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(520, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #0D273D;
                border-radius: 8px;
            }
            """
        )

        icon_path = Path(__file__).resolve().parents[1] / "config" / "ui" / "icon" / "app.ico"
        if icon_path.exists():
            icon_label = QLabel()
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    80,
                    80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                icon_label.setPixmap(scaled_pixmap)
            else:
                icon_label.setText("🏭")
                icon_label.setStyleSheet("font-size: 64px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        else:
            icon_label = QLabel("🏭")
            icon_label.setStyleSheet("font-size: 64px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        title_label = QLabel(self.APP_TITLE)
        title_label.setStyleSheet(
            """
            QLabel {
                color: #A6BED1;
                font-size: 22px;
                font-weight: bold;
            }
            """
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel(self.APP_SUBTITLE)
        subtitle_label.setStyleSheet(
            """
            QLabel {
                color: #CDD7DF;
                font-size: 14px;
            }
            """
        )
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        version_label = QLabel(self.APP_VERSION)
        version_label.setStyleSheet(
            """
            QLabel {
                color: #8AA7BC;
                font-size: 12px;
                font-style: italic;
            }
            """
        )
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        layout.addStretch()

        self.message_label = QLabel(self.LOADING_MESSAGES[0])
        self.message_label.setStyleSheet(
            """
            QLabel {
                color: #FFFFFF;
                font-size: 13px;
            }
            """
        )
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                background-color: #16334D;
                border: 1px solid #3E6985;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #A6BED1;
                border-radius: 4px;
            }
            """
        )
        layout.addWidget(self.progress_bar)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_progress)
        self.timer.start(30)

    def _update_progress(self):
        self._progress += 1

        if self._progress > 100:
            self._finish()
            return

        self.progress_bar.setValue(self._progress)

        if self._progress == 25:
            self._message_index = 1
            self.message_label.setText(self.LOADING_MESSAGES[1])
        elif self._progress == 55:
            self._message_index = 2
            self.message_label.setText(self.LOADING_MESSAGES[2])
        elif self._progress == 90:
            self._message_index = 3
            self.message_label.setText(self.LOADING_MESSAGES[3])

    def _finish(self):
        self.timer.stop()
        self.finished.emit()
