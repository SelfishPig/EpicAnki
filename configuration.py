from __future__ import annotations

from collections.abc import Callable
from math import isfinite
from typing import Any

import aqt
from anki.consts import MODEL_CLOZE
from anki.models import NotetypeDict, NotetypeId
from aqt.qt import (
    QAbstractItemView,
    QBrush,
    QCheckBox,
    QCloseEvent,
    QColor,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    Qt,
    QVBoxLayout,
    QWidget,
    qconnect,
)
from aqt.utils import restoreGeom, saveGeom, showWarning

from .style import (
    INCOGNITO_CSS,
    INCOGNITO_DARK_THEME_CSS,
    INCOGNITO_LIGHT_THEME_CSS,
)

CONFIG_DIALOG_NAME = "EpicAnkiConfig"
CONFIG_DIALOG_GEOMETRY_KEY = "epicAnkiConfigDialog"
CONFIGURED_BACKGROUND = QColor(72, 170, 95, 80)
DEFAULT_INCOGNITO_ZOOM_FACTOR = 1.0
MINIMUM_INCOGNITO_ZOOM_FACTOR = 0.25
MAXIMUM_INCOGNITO_ZOOM_FACTOR = 5.0
DEFAULT_DARK_MODE_ENABLED = False
DEFAULT_HIDE_UNCONFIGURED_TEMPLATE_WARNINGS = False
DEFAULT_INCOGNITO_POSITION_SLOT = 1
INCOGNITO_POSITION_SLOT_COUNT = 4

_config_cache: dict[str, Any] | None = None
_configuration_changed: Callable[[], None] | None = None


def reload_configuration() -> None:
    global _config_cache
    config = aqt.mw.addonManager.getConfig(__name__)
    _config_cache = config if isinstance(config, dict) else {"notetypes": {}}


def _configuration_data() -> dict[str, Any]:
    if _config_cache is None:
        reload_configuration()

    assert _config_cache is not None
    if not isinstance(_config_cache.get("notetypes"), dict):
        _config_cache["notetypes"] = {}
    return _config_cache


def _validated_incognito_zoom_factor(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return DEFAULT_INCOGNITO_ZOOM_FACTOR

    factor = float(value)
    if not isfinite(factor):
        return DEFAULT_INCOGNITO_ZOOM_FACTOR

    return max(
        MINIMUM_INCOGNITO_ZOOM_FACTOR,
        min(MAXIMUM_INCOGNITO_ZOOM_FACTOR, factor),
    )


def get_incognito_zoom_factor() -> float:
    return _validated_incognito_zoom_factor(
        _configuration_data().get("incognito_zoom_factor")
    )


def save_incognito_zoom_factor(value: float) -> float:
    factor = _validated_incognito_zoom_factor(value)
    _configuration_data()["incognito_zoom_factor"] = factor
    aqt.mw.addonManager.writeConfig(__name__, _configuration_data())
    return factor


def get_active_incognito_position_slot() -> int:
    value = _configuration_data().get("active_incognito_position_slot")
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= INCOGNITO_POSITION_SLOT_COUNT
    ):
        return DEFAULT_INCOGNITO_POSITION_SLOT
    return value


def save_active_incognito_position_slot(slot: int) -> int:
    if (
        isinstance(slot, bool)
        or not isinstance(slot, int)
        or not 1 <= slot <= INCOGNITO_POSITION_SLOT_COUNT
    ):
        slot = DEFAULT_INCOGNITO_POSITION_SLOT
    _configuration_data()["active_incognito_position_slot"] = slot
    aqt.mw.addonManager.writeConfig(__name__, _configuration_data())
    return slot


def get_dark_mode_enabled() -> bool:
    value = _configuration_data().get("dark_mode")
    return value if isinstance(value, bool) else DEFAULT_DARK_MODE_ENABLED


def save_dark_mode_enabled(enabled: bool) -> None:
    _configuration_data()["dark_mode"] = bool(enabled)
    aqt.mw.addonManager.writeConfig(__name__, _configuration_data())


def get_unconfigured_template_warnings_hidden() -> bool:
    value = _configuration_data().get("hide_unconfigured_template_warnings")
    return (
        value
        if isinstance(value, bool)
        else DEFAULT_HIDE_UNCONFIGURED_TEMPLATE_WARNINGS
    )


def save_unconfigured_template_warnings_hidden(hidden: bool) -> None:
    _configuration_data()["hide_unconfigured_template_warnings"] = bool(hidden)
    aqt.mw.addonManager.writeConfig(__name__, _configuration_data())


def get_incognito_styles() -> tuple[str, str, str]:
    configuration = _configuration_data()
    light_theme_css = configuration.get("incognito_light_theme_css")
    dark_theme_css = configuration.get("incognito_dark_theme_css")
    incognito_css = configuration.get("incognito_css")

    return (
        light_theme_css.strip("\r\n")
        if isinstance(light_theme_css, str)
        else INCOGNITO_LIGHT_THEME_CSS,
        dark_theme_css.strip("\r\n")
        if isinstance(dark_theme_css, str)
        else INCOGNITO_DARK_THEME_CSS,
        incognito_css.strip("\r\n")
        if isinstance(incognito_css, str)
        else INCOGNITO_CSS,
    )


def save_incognito_styles(
    light_theme_css: str,
    dark_theme_css: str,
    incognito_css: str,
) -> None:
    _configuration_data().update(
        {
            "incognito_light_theme_css": light_theme_css.strip("\r\n"),
            "incognito_dark_theme_css": dark_theme_css.strip("\r\n"),
            "incognito_css": incognito_css.strip("\r\n"),
        }
    )
    aqt.mw.addonManager.writeConfig(__name__, _configuration_data())


def get_notetype_configuration(notetype_id: int) -> dict[str, Any] | None:
    entry = _configuration_data()["notetypes"].get(str(notetype_id))
    return entry if isinstance(entry, dict) else None


def configured_fields_for_notetype(
    notetype: NotetypeDict,
) -> tuple[str, list[str]] | None:
    if notetype["type"] != MODEL_CLOZE:
        return None

    entry = get_notetype_configuration(notetype["id"])
    if entry is None:
        return None

    field_names = [field["name"] for field in notetype["flds"]]
    main_field = entry.get("main_field")
    extra_fields = entry.get("extra_fields")

    if not isinstance(main_field, str) or main_field not in field_names:
        return None
    if not isinstance(extra_fields, list):
        return None
    if any(not isinstance(field, str) for field in extra_fields):
        return None
    if len(extra_fields) != len(set(extra_fields)):
        return None
    if main_field in extra_fields:
        return None
    if any(field not in field_names for field in extra_fields):
        return None

    return main_field, list(extra_fields)


def save_notetype_configuration(
    notetype: NotetypeDict,
    main_field: str,
    selected_extra_fields: list[str],
) -> None:
    field_names = {field["name"] for field in notetype["flds"]}
    extra_fields = []
    for field_name in selected_extra_fields:
        if (
            field_name in field_names
            and field_name != main_field
            and field_name not in extra_fields
        ):
            extra_fields.append(field_name)
    _configuration_data()["notetypes"][str(notetype["id"])] = {
        "name": notetype["name"],
        "main_field": main_field,
        "extra_fields": extra_fields,
    }
    aqt.mw.addonManager.writeConfig(__name__, _configuration_data())


def remove_notetype_configuration(notetype_id: int) -> None:
    _configuration_data()["notetypes"].pop(str(notetype_id), None)
    aqt.mw.addonManager.writeConfig(__name__, _configuration_data())


def _notify_configuration_changed() -> None:
    if _configuration_changed is not None:
        _configuration_changed()


class EpicAnkiConfigDialog(QDialog):
    silentlyClose = True

    def __init__(self, mw: aqt.AnkiQt) -> None:
        super().__init__(mw, Qt.WindowType.Window)
        self.mw = mw
        self._current_notetype_id: NotetypeId | None = None

        self.setWindowTitle("Epic Anki Configuration")
        self.setMinimumSize(520, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        reload_configuration()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        self._pages = QStackedWidget(self)
        root_layout.addWidget(self._pages)

        self._list_page = self._build_list_page()
        self._editor_page = self._build_editor_page()
        self._style_editor_page = self._build_style_editor_page()
        self._pages.addWidget(self._list_page)
        self._pages.addWidget(self._editor_page)
        self._pages.addWidget(self._style_editor_page)

        self._populate_notetype_list()
        restoreGeom(self, CONFIG_DIALOG_GEOMETRY_KEY)
        self.show()

    def _build_list_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.addWidget(
            QLabel(
                "Select a cloze note type to configure its incognito card layout.",
                page,
            )
        )

        self._notetype_list = QListWidget(page)
        qconnect(self._notetype_list.itemClicked, self._open_notetype_editor)
        layout.addWidget(self._notetype_list)

        button_layout = QHBoxLayout()
        style_editor_button = QPushButton("Style Editor...", page)
        qconnect(style_editor_button.clicked, self._open_style_editor)
        button_layout.addWidget(style_editor_button)

        self._hide_unconfigured_template_warnings = QCheckBox(
            "Hide unconfigured template warnings", page
        )
        self._hide_unconfigured_template_warnings.setChecked(
            get_unconfigured_template_warnings_hidden()
        )
        qconnect(
            self._hide_unconfigured_template_warnings.toggled,
            self._set_unconfigured_template_warnings_hidden,
        )
        button_layout.addWidget(self._hide_unconfigured_template_warnings)
        button_layout.addStretch()

        close_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close, page
        )
        qconnect(close_buttons.rejected, self.close)
        button_layout.addWidget(close_buttons)
        layout.addLayout(button_layout)
        return page

    def _build_editor_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)

        self._editor_heading = QLabel(page)
        self._editor_heading.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self._editor_heading)

        layout.addWidget(QLabel("Main cloze field", page))
        self._main_field = QComboBox(page)
        qconnect(self._main_field.currentTextChanged, self._sync_extra_field_states)
        layout.addWidget(self._main_field)

        layout.addWidget(
            QLabel("Additional fields shown on the back (drag to reorder)", page)
        )
        self._extra_fields = QListWidget(page)
        self._extra_fields.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove
        )
        self._extra_fields.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._extra_fields.setDropIndicatorShown(True)
        layout.addWidget(self._extra_fields)

        button_layout = QHBoxLayout()
        self._back_button = QPushButton("Back", page)
        self._remove_button = QPushButton("Remove Configuration", page)
        self._save_button = QPushButton("Save", page)
        qconnect(self._back_button.clicked, self._show_notetype_list)
        qconnect(self._remove_button.clicked, self._remove_current_configuration)
        qconnect(self._save_button.clicked, self._save_current_configuration)
        button_layout.addWidget(self._back_button)
        button_layout.addWidget(self._remove_button)
        button_layout.addStretch()
        button_layout.addWidget(self._save_button)
        layout.addLayout(button_layout)
        return page

    def _build_style_editor_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Incognito Card Styles", page))

        layout.addWidget(QLabel("Light Theme CSS", page))
        self._light_theme_css = QPlainTextEdit(page)
        layout.addWidget(self._light_theme_css)

        layout.addWidget(QLabel("Dark Theme CSS", page))
        self._dark_theme_css = QPlainTextEdit(page)
        layout.addWidget(self._dark_theme_css)

        layout.addWidget(QLabel("Shared Incognito CSS", page))
        self._incognito_css = QPlainTextEdit(page)
        layout.addWidget(self._incognito_css)

        button_layout = QHBoxLayout()
        back_button = QPushButton("Back", page)
        restore_button = QPushButton("Restore Defaults", page)
        save_button = QPushButton("Save", page)
        qconnect(back_button.clicked, self._show_notetype_list)
        qconnect(restore_button.clicked, self._restore_default_styles)
        qconnect(save_button.clicked, self._save_styles)
        button_layout.addWidget(back_button)
        button_layout.addWidget(restore_button)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
        return page

    def _populate_notetype_list(self) -> None:
        self._notetype_list.clear()
        notetypes = sorted(
            self.mw.col.models.all(),
            key=lambda notetype: notetype["name"].casefold(),
        )

        for notetype in notetypes:
            is_cloze = notetype["type"] == MODEL_CLOZE
            label = notetype["name"]
            if not is_cloze:
                label += " (cloze only)"

            item = QListWidgetItem(label, self._notetype_list)
            item.setData(Qt.ItemDataRole.UserRole, notetype["id"])

            if not is_cloze:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                item.setToolTip("Epic Anki currently supports cloze note types only.")
            elif configured_fields_for_notetype(notetype) is not None:
                item.setBackground(QBrush(CONFIGURED_BACKGROUND))
                item.setToolTip("This note type is configured.")
            elif get_notetype_configuration(notetype["id"]) is not None:
                item.setToolTip(
                    "This saved configuration is no longer valid and needs updating."
                )

    def _open_notetype_editor(self, item: QListWidgetItem) -> None:
        notetype_id = NotetypeId(item.data(Qt.ItemDataRole.UserRole))
        notetype = self.mw.col.models.get(notetype_id)
        if notetype is None or notetype["type"] != MODEL_CLOZE:
            return

        self._current_notetype_id = notetype_id
        self._editor_heading.setText(f"Configure: {notetype['name']}")

        field_names = [field["name"] for field in notetype["flds"]]
        saved_configuration = get_notetype_configuration(notetype_id)
        saved = saved_configuration or {}
        saved_main = saved.get("main_field")
        saved_extras = saved.get("extra_fields")

        self._main_field.clear()
        self._main_field.addItems(field_names)
        if isinstance(saved_main, str) and saved_main in field_names:
            self._main_field.setCurrentText(saved_main)

        ordered_saved_extras = []
        if isinstance(saved_extras, list):
            for field in saved_extras:
                if (
                    isinstance(field, str)
                    and field in field_names
                    and field not in ordered_saved_extras
                ):
                    ordered_saved_extras.append(field)

        selected_extras = set(ordered_saved_extras)
        displayed_fields = ordered_saved_extras + [
            field for field in field_names if field not in selected_extras
        ]

        self._extra_fields.clear()
        for field_name in displayed_fields:
            field_item = QListWidgetItem(field_name, self._extra_fields)
            field_item.setFlags(field_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            field_item.setCheckState(
                Qt.CheckState.Checked
                if field_name in selected_extras
                else Qt.CheckState.Unchecked
            )

        self._remove_button.setEnabled(saved_configuration is not None)
        self._save_button.setEnabled(bool(field_names))
        self._sync_extra_field_states()
        self._pages.setCurrentWidget(self._editor_page)

    def _sync_extra_field_states(self, _current_text: str = "") -> None:
        main_field = self._main_field.currentText()
        for row in range(self._extra_fields.count()):
            item = self._extra_fields.item(row)
            if item.text() == main_field:
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)

    def _checked_extra_fields(self) -> list[str]:
        return [
            self._extra_fields.item(row).text()
            for row in range(self._extra_fields.count())
            if self._extra_fields.item(row).checkState() == Qt.CheckState.Checked
        ]

    def _open_style_editor(self) -> None:
        light_theme_css, dark_theme_css, incognito_css = get_incognito_styles()
        self._light_theme_css.setPlainText(light_theme_css)
        self._dark_theme_css.setPlainText(dark_theme_css)
        self._incognito_css.setPlainText(incognito_css)
        self._pages.setCurrentWidget(self._style_editor_page)

    def _set_unconfigured_template_warnings_hidden(self, hidden: bool) -> None:
        save_unconfigured_template_warnings_hidden(hidden)
        _notify_configuration_changed()

    def _restore_default_styles(self) -> None:
        self._light_theme_css.setPlainText(INCOGNITO_LIGHT_THEME_CSS)
        self._dark_theme_css.setPlainText(INCOGNITO_DARK_THEME_CSS)
        self._incognito_css.setPlainText(INCOGNITO_CSS)

    def _save_styles(self) -> None:
        save_incognito_styles(
            self._light_theme_css.toPlainText(),
            self._dark_theme_css.toPlainText(),
            self._incognito_css.toPlainText(),
        )
        _notify_configuration_changed()
        self._show_notetype_list()

    def _save_current_configuration(self) -> None:
        if self._current_notetype_id is None:
            return

        notetype = self.mw.col.models.get(self._current_notetype_id)
        if notetype is None or notetype["type"] != MODEL_CLOZE:
            showWarning("The selected note type is no longer available.", parent=self)
            self._show_notetype_list()
            return

        field_names = [field["name"] for field in notetype["flds"]]
        main_field = self._main_field.currentText()
        extra_fields = self._checked_extra_fields()
        if main_field not in field_names or any(
            field not in field_names for field in extra_fields
        ):
            showWarning(
                "The note type's fields changed while this window was open. "
                "Please select it again.",
                parent=self,
            )
            self._show_notetype_list()
            return

        save_notetype_configuration(notetype, main_field, extra_fields)
        _notify_configuration_changed()
        self._show_notetype_list()

    def _remove_current_configuration(self) -> None:
        if self._current_notetype_id is None:
            return

        remove_notetype_configuration(self._current_notetype_id)
        _notify_configuration_changed()
        self._show_notetype_list()

    def _show_notetype_list(self) -> None:
        self._current_notetype_id = None
        self._populate_notetype_list()
        self._pages.setCurrentWidget(self._list_page)

    def reopen(self, mw: aqt.AnkiQt) -> None:
        self.mw = mw
        reload_configuration()
        self._show_notetype_list()

    def closeEvent(self, event: QCloseEvent) -> None:
        saveGeom(self, CONFIG_DIALOG_GEOMETRY_KEY)
        aqt.dialogs.markClosed(CONFIG_DIALOG_NAME)
        super().closeEvent(event)


def setup_configuration_dialog(on_configuration_changed: Callable[[], None]) -> None:
    global _configuration_changed
    _configuration_changed = on_configuration_changed
    aqt.dialogs.register_dialog(CONFIG_DIALOG_NAME, EpicAnkiConfigDialog)


def open_configuration_dialog() -> None:
    if aqt.mw.col is not None:
        aqt.dialogs.open(CONFIG_DIALOG_NAME, aqt.mw)
