from __future__ import annotations

from pathlib import Path

import aqt
from aqt.qt import (
    QCloseEvent,
    QDialog,
    QDialogButtonBox,
    QPalette,
    QTextBrowser,
    QTextDocument,
    Qt,
    QVBoxLayout,
    qconnect,
)
from aqt.utils import restoreGeom, saveGeom

USAGE_GUIDE_DIALOG_NAME = "EpicAnkiUsageGuide"
USAGE_GUIDE_GEOMETRY_KEY = "epicAnkiUsageGuideDialog"
USAGE_GUIDE_PATH = Path(__file__).with_name("README.md")


class EpicAnkiUsageGuideDialog(QDialog):
    silentlyClose = True

    def __init__(self, mw: aqt.AnkiQt) -> None:
        super().__init__(mw, Qt.WindowType.Window)
        self.mw = mw

        self.setWindowTitle("Epic Anki Usage Guide")
        self.setMinimumSize(640, 520)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        self._guide = QTextBrowser(self)
        self._guide.setOpenExternalLinks(True)
        layout.addWidget(self._guide)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        qconnect(buttons.rejected, self.close)
        layout.addWidget(buttons)

        self._load_guide()
        restoreGeom(self, USAGE_GUIDE_GEOMETRY_KEY)
        self.show()

    def _apply_guide_styles(self) -> None:
        palette = self._guide.palette()
        text_color = palette.color(QPalette.ColorRole.Text).name()
        background_color = palette.color(QPalette.ColorRole.Base).name()
        accent_color = palette.color(QPalette.ColorRole.Link).name()
        muted_color = palette.color(QPalette.ColorRole.Mid).name()
        panel_color = palette.color(QPalette.ColorRole.AlternateBase).name()

        self._guide.document().setDefaultStyleSheet(
            f"""
body {{
  color: {text_color};
  background-color: {background_color};
  font-size: 14px;
  line-height: 1.5;
}}
h1 {{
  color: {accent_color};
  font-size: 28px;
  margin-top: 4px;
  margin-bottom: 16px;
}}
h2 {{
  color: {accent_color};
  font-size: 21px;
  border-bottom: 1px solid {muted_color};
  margin-top: 24px;
  margin-bottom: 10px;
  padding-bottom: 4px;
}}
h3 {{
  color: {accent_color};
  font-size: 17px;
  margin-top: 18px;
  margin-bottom: 8px;
}}
p {{ margin-top: 6px; margin-bottom: 10px; }}
ul, ol {{ margin-top: 6px; margin-bottom: 12px; }}
li {{ margin-bottom: 4px; }}
a {{ color: {accent_color}; text-decoration: none; }}
table {{
  border-collapse: collapse;
  border: 1px solid {muted_color};
  margin-top: 10px;
  margin-bottom: 16px;
}}
th {{
  background-color: {panel_color};
  color: {text_color};
  border: 1px solid {muted_color};
  padding: 7px 9px;
}}
td {{ border: 1px solid {muted_color}; padding: 7px 9px; }}
code {{
  background-color: {panel_color};
  color: {text_color};
  font-family: "Consolas", "Courier New", monospace;
  padding: 2px 4px;
}}
pre {{
  background-color: {panel_color};
  color: {text_color};
  border: 1px solid {muted_color};
  padding: 10px;
}}
blockquote {{
  color: {text_color};
  border-left: 4px solid {accent_color};
  background-color: {panel_color};
  margin: 10px 0;
  padding: 8px 12px;
}}
hr {{
  border: none;
  border-top: 1px solid {muted_color};
  margin: 20px 0;
}}
"""
        )
        self._guide.document().setDocumentMargin(20)

    def _load_guide(self) -> None:
        try:
            guide_text = USAGE_GUIDE_PATH.read_text(encoding="utf-8")
        except OSError as error:
            self._guide.setPlainText(
                f"The Epic Anki usage guide could not be loaded.\n\n{error}"
            )
            return

        markdown_document = QTextDocument()
        markdown_document.setMarkdown(guide_text)

        self._apply_guide_styles()
        self._guide.setHtml(markdown_document.toHtml())

    def reopen(self, mw: aqt.AnkiQt) -> None:
        self.mw = mw
        self._load_guide()

    def closeEvent(self, event: QCloseEvent) -> None:
        saveGeom(self, USAGE_GUIDE_GEOMETRY_KEY)
        aqt.dialogs.markClosed(USAGE_GUIDE_DIALOG_NAME)
        super().closeEvent(event)


def setup_usage_guide_dialog() -> None:
    aqt.dialogs.register_dialog(
        USAGE_GUIDE_DIALOG_NAME, EpicAnkiUsageGuideDialog
    )


def open_usage_guide() -> None:
    aqt.dialogs.open(USAGE_GUIDE_DIALOG_NAME, aqt.mw)
