from __future__ import annotations

import json
from html import escape
from typing import Any

import aqt
from aqt.qt import (
    QCloseEvent,
    QDialog,
    QVBoxLayout,
    Qt,
)
from aqt.utils import restoreGeom, saveGeom
from aqt.webview import AnkiWebView

IMAGE_VIEWER_DIALOG_NAME = "EpicAnkiImageViewer"
IMAGE_VIEWER_GEOMETRY_KEY = "epicAnkiImageViewer"
IMAGE_VIEWER_MESSAGE_PREFIX = "epic-anki-open-image:"


class EpicAnkiImageViewerDialog(QDialog):
    silentlyClose = True

    def __init__(
        self,
        mw: aqt.AnkiQt,
        image_src: str,
        image_alt: str = "",
    ) -> None:
        super().__init__(mw, Qt.WindowType.Window)
        self.mw = mw
        self._cleaned_up = False

        self.setWindowTitle("Epic Anki Image Viewer")
        self.setMinimumSize(320, 240)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.web = AnkiWebView(self, title="Epic Anki Image Viewer")
        layout.addWidget(self.web)

        restoreGeom(self, IMAGE_VIEWER_GEOMETRY_KEY, default_size=(900, 700))
        self._show_image(image_src, image_alt)
        self.show()

    def _show_image(self, image_src: str, image_alt: str) -> None:
        image_src = escape(image_src, quote=True)
        image_alt = escape(image_alt, quote=True)
        self.web.stdHtml(
            f'<img class="epic-anki-viewer-image" src="{image_src}" '
            f'alt="{image_alt}">',
            head="""
<style>
:root {
  color-scheme: light dark;
}
html,
body {
  margin: 0;
  width: 100%;
  height: 100%;
  background: #111;
}
body {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.epic-anki-viewer-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
""",
            context=self,
            default_css=False,
        )

    def reopen(
        self,
        mw: aqt.AnkiQt,
        image_src: str,
        image_alt: str = "",
    ) -> None:
        self.mw = mw
        self._show_image(image_src, image_alt)

    def closeEvent(self, event: QCloseEvent) -> None:
        saveGeom(self, IMAGE_VIEWER_GEOMETRY_KEY)
        if not self._cleaned_up:
            self.web.cleanup()
            self._cleaned_up = True
        aqt.dialogs.markClosed(IMAGE_VIEWER_DIALOG_NAME)
        super().closeEvent(event)


def handle_image_viewer_message(
    handled: tuple[bool, Any],
    message: str,
    _context: Any,
) -> tuple[bool, Any]:
    if handled[0] or not message.startswith(IMAGE_VIEWER_MESSAGE_PREFIX):
        return handled

    try:
        payload = json.loads(message.removeprefix(IMAGE_VIEWER_MESSAGE_PREFIX))
        image_src = payload["src"]
        image_alt = payload.get("alt", "")
        if not isinstance(image_src, str) or not image_src:
            raise ValueError("missing image source")
        if not isinstance(image_alt, str):
            image_alt = ""
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return (True, None)

    aqt.dialogs.open(
        IMAGE_VIEWER_DIALOG_NAME,
        aqt.mw,
        image_src,
        image_alt,
    )
    return (True, None)


def setup_image_viewer_dialog() -> None:
    aqt.dialogs.register_dialog(
        IMAGE_VIEWER_DIALOG_NAME,
        EpicAnkiImageViewerDialog,
    )
