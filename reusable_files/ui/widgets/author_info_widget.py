"""
Author Info Widget for the PySide6 UI.

Displays author information and date in the header.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class AuthorInfoWidget(QLabel):
    """
    Label with author information and date.

    Displays: "@Febrero 2026 | Autor: Ricardo Fabian Uculmana Quispe"
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setText("@Febrero 2026 | Autor: Ricardo Fabian Uculmana Quispe")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self._is_dark = True

    def update_theme(self, is_dark: bool) -> None:
        self._is_dark = is_dark

        if is_dark:
            color = "#38BDF8"
        else:
            color = "rgba(30, 41, 59, 0.6)"

        self.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 13px;
                font-weight: normal;
                padding: 5px 10px;
                background-color: transparent;
            }}
            """
        )


__all__ = ["AuthorInfoWidget"]
