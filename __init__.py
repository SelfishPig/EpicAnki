from copy import deepcopy

from aqt import mw, gui_hooks
from anki.hooks import wrap
from anki.cards import Card
from anki.consts import MODEL_CLOZE
from anki.template import TemplateRenderContext
from aqt.overview import Overview
from aqt.utils import restoreGeom, saveGeom

from aqt.qt import (
    QAction,
    Qt,
    qconnect,
    QShortcut,
    QKeySequence,
    QEvent,
    QFrame,
    QLabel,
    QObject,
    QApplication,
    QTimer,
)

from .card import (
    build_incognito_answer_template,
    build_incognito_question_template,
)
from .configuration import (
    INCOGNITO_POSITION_SLOT_COUNT,
    configured_fields_for_notetype,
    get_active_incognito_position_slot,
    get_dark_mode_enabled,
    get_incognito_styles,
    get_incognito_zoom_factor,
    get_unconfigured_template_warnings_hidden,
    open_configuration_dialog,
    save_active_incognito_position_slot,
    save_dark_mode_enabled,
    save_incognito_zoom_factor,
    setup_configuration_dialog,
)
from .screens import (
    build_incognito_deck_browser,
    build_incognito_overview,
)
from .style import build_incognito_css
from .usage_guide import open_usage_guide, setup_usage_guide_dialog

incognito_mode = False
toggle_action: QAction | None = None
dark_mode_action: QAction | None = None
normal_web_zoom_factor: float | None = None

original_window_flags = mw.windowFlags()
original_window_minimumWidth = mw.minimumWidth()
original_web_minimumWidth = mw.web.minimumWidth()

NORMAL_WINDOW_GEOMETRY_KEY = "epicAnkiNormalMainWindow"
INCOGNITO_WINDOW_GEOMETRY_KEY = "epicAnkiIncognitoMainWindow"

UNCONFIGURED_TEMPLATE_WARNING_HTML = (
    '<div role="alert" style="box-sizing: border-box; margin: 0 0 12px; '
    "padding: 10px 12px; border: 1px solid #b7791f; border-radius: 4px; "
    "background: #fff3cd; color: #4a2c00; font-family: sans-serif; "
    'font-size: 14px; text-align: left;">'
    "<strong>Epic Anki:</strong> This cloze note type has not been configured "
    "for Incognito Mode. Open Epic Anki’s configuration to configure it."
    "</div>"
)


def incognito_window_geometry_key(slot: int | None = None) -> str:
    active_slot = (
        get_active_incognito_position_slot() if slot is None else slot
    )
    if active_slot == 1:
        return INCOGNITO_WINDOW_GEOMETRY_KEY
    return f"{INCOGNITO_WINDOW_GEOMETRY_KEY}Slot{active_slot}"


def apply_incognito(enabled: bool) -> None:
    global incognito_mode, normal_web_zoom_factor

    if enabled == incognito_mode:
        return

    saveGeom(
        mw,
        NORMAL_WINDOW_GEOMETRY_KEY
        if enabled
        else incognito_window_geometry_key(),
    )
    incognito_mode = enabled

    toolbar = mw.toolbarWeb
    bottombar = mw.bottomWeb
    menubar = mw.menuBar()
    
    if enabled:
        normal_web_zoom_factor = mw.web.zoomFactor()
        mw.web.setZoomFactor(get_incognito_zoom_factor())
        set_zoom_shortcuts_enabled(True)
        set_position_slot_shortcuts_enabled(True)
        toolbar.setVisible(False)
        bottombar.setVisible(False)
        menubar.hide()
        mw.setMinimumWidth(0)
        mw.web.setMinimumWidth(0)
        mw.setWindowFlags(
            original_window_flags
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
    else:
        set_zoom_shortcuts_enabled(False)
        set_position_slot_shortcuts_enabled(False)
        if normal_web_zoom_factor is not None:
            mw.web.setZoomFactor(normal_web_zoom_factor)
            normal_web_zoom_factor = None
        toolbar.setVisible(True)
        bottombar.setVisible(True)
        menubar.show()
        mw.setMinimumWidth(original_window_minimumWidth)
        mw.web.setMinimumWidth(original_web_minimumWidth)
        mw.setWindowFlags(original_window_flags)

    mw.show()
    restoreGeom(
        mw,
        incognito_window_geometry_key()
        if enabled
        else NORMAL_WINDOW_GEOMETRY_KEY,
    )
    modifier_border_filter = getattr(mw, "epic_anki_modifier_border_filter", None)
    if modifier_border_filter is not None:
        modifier_border_filter.sync_visibility()
    redraw_current_screen()


def toggle_incognito() -> None:
    if toggle_action is not None:
        toggle_action.setChecked(not toggle_action.isChecked())


def adjust_incognito_zoom(amount: float) -> None:
    if not incognito_mode:
        return

    zoom_factor = round(mw.web.zoomFactor() + amount, 2)
    zoom_factor = save_incognito_zoom_factor(zoom_factor)
    mw.web.setZoomFactor(zoom_factor)


def set_zoom_shortcuts_enabled(enabled: bool) -> None:
    zoom_in_shortcut = getattr(mw, "epic_anki_zoom_in_shortcut", None)
    zoom_out_shortcut = getattr(mw, "epic_anki_zoom_out_shortcut", None)
    if zoom_in_shortcut is not None:
        zoom_in_shortcut.setEnabled(enabled)
    if zoom_out_shortcut is not None:
        zoom_out_shortcut.setEnabled(enabled)


def set_position_slot_shortcuts_enabled(enabled: bool) -> None:
    shortcuts = getattr(mw, "epic_anki_position_slot_shortcuts", [])
    for shortcut in shortcuts:
        shortcut.setEnabled(enabled)


def switch_incognito_position_slot(offset: int) -> None:
    if not incognito_mode or offset == 0:
        return

    current_slot = get_active_incognito_position_slot()
    saveGeom(mw, incognito_window_geometry_key(current_slot))
    target_slot = (
        (current_slot - 1 + offset) % INCOGNITO_POSITION_SLOT_COUNT
    ) + 1
    save_active_incognito_position_slot(target_slot)
    restoreGeom(mw, incognito_window_geometry_key(target_slot))

    modifier_border_filter = getattr(
        mw, "epic_anki_modifier_border_filter", None
    )
    if modifier_border_filter is not None:
        modifier_border_filter.sync_visibility()


def leave_incognito_before_profile_close() -> None:
    if toggle_action is not None and toggle_action.isChecked():
        toggle_action.setChecked(False)


class IncognitoWindowDragFilter(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not incognito_mode:
            return False

        if event.type() != QEvent.Type.MouseButtonPress:
            return False

        if event.button() != Qt.MouseButton.LeftButton:
            return False
        
        if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            return False
        
        if hasattr(watched, "window") and watched.window() is not mw:
            return False

        window = mw.windowHandle()
        if window is None:
            return False

        if window.startSystemMove():
            event.accept()
            return True

        return False


class IncognitoWindowResizeFilter(QObject):
    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self._manual_resize_edges = None
        self._manual_resize_start_pos = None
        self._manual_resize_start_geometry = None

    def _clear_manual_resize(self) -> None:
        self._manual_resize_edges = None
        self._manual_resize_start_pos = None
        self._manual_resize_start_geometry = None

    def _resize_manually(self, event: QEvent) -> None:
        edges = self._manual_resize_edges
        start_pos = self._manual_resize_start_pos
        geometry = self._manual_resize_start_geometry
        if edges is None or start_pos is None or geometry is None:
            return

        current_pos = event.globalPosition().toPoint()
        delta_x = current_pos.x() - start_pos.x()
        delta_y = current_pos.y() - start_pos.y()

        left = geometry.x()
        top = geometry.y()
        right = left + geometry.width()
        bottom = top + geometry.height()
        minimum_width = max(1, mw.minimumWidth())
        minimum_height = max(1, mw.minimumHeight())
        maximum_width = mw.maximumWidth()
        maximum_height = mw.maximumHeight()

        if edges & Qt.Edge.LeftEdge:
            left = min(left + delta_x, right - minimum_width)
            left = max(left, right - maximum_width)
        elif edges & Qt.Edge.RightEdge:
            right = max(right + delta_x, left + minimum_width)
            right = min(right, left + maximum_width)

        if edges & Qt.Edge.TopEdge:
            top = min(top + delta_y, bottom - minimum_height)
            top = max(top, bottom - maximum_height)
        elif edges & Qt.Edge.BottomEdge:
            bottom = max(bottom + delta_y, top + minimum_height)
            bottom = min(bottom, top + maximum_height)

        mw.setGeometry(left, top, right - left, bottom - top)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not incognito_mode:
            self._clear_manual_resize()
            return False

        if self._manual_resize_edges is not None:
            if event.type() == QEvent.Type.MouseMove:
                if not event.buttons() & Qt.MouseButton.LeftButton:
                    self._clear_manual_resize()
                    return False
                self._resize_manually(event)
                event.accept()
                return True

            if (
                event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._resize_manually(event)
                self._clear_manual_resize()
                event.accept()
                return True

        if event.type() != QEvent.Type.MouseButtonPress:
            return False

        if event.button() != Qt.MouseButton.LeftButton:
            return False

        if not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            return False

        if hasattr(watched, "window") and watched.window() is not mw:
            return False

        local_pos = mw.mapFromGlobal(event.globalPosition().toPoint())

        left_half = local_pos.x() < mw.width() / 2
        top_half = local_pos.y() < mw.height() / 2

        if left_half and top_half:
            edges = Qt.Edge.LeftEdge | Qt.Edge.TopEdge
        elif not left_half and top_half:
            edges = Qt.Edge.RightEdge | Qt.Edge.TopEdge
        elif left_half and not top_half:
            edges = Qt.Edge.LeftEdge | Qt.Edge.BottomEdge
        else:
            edges = Qt.Edge.RightEdge | Qt.Edge.BottomEdge

        window = mw.windowHandle()
        if window is not None and window.startSystemResize(edges):
            event.accept()
            return True

        # startSystemResize() is unavailable on some platforms, including macOS.
        # Consume the press so the webview does not select text while dragging.
        self._manual_resize_edges = edges
        self._manual_resize_start_pos = event.globalPosition().toPoint()
        self._manual_resize_start_geometry = mw.geometry()
        event.accept()
        return True


class IncognitoModifierBorderFilter(QObject):
    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self._central_widget = mw.form.centralwidget
        self._border = QFrame(self._central_widget)
        self._border.setObjectName("epicAnkiIncognitoModifierBorder")
        self._border.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._border.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._slot_label = QLabel(self._border)
        self._slot_label.setObjectName("epicAnkiIncognitoPositionSlot")
        self._slot_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._slot_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self._border.setStyleSheet(
            "QFrame#epicAnkiIncognitoModifierBorder {"
            " background: transparent;"
            " border: 2px solid #667788;"
            "}"
            "QLabel#epicAnkiIncognitoPositionSlot {"
            " background: #202630;"
            " color: white;"
            " border: 1px solid #667788;"
            " border-radius: 6px;"
            " padding: 8px 12px;"
            " font-size: 18px;"
            " font-weight: bold;"
            "}"
        )
        self._border.hide()

        self._modifier_poll_timer = QTimer(self)
        self._modifier_poll_timer.setInterval(30)
        qconnect(self._modifier_poll_timer.timeout, self.sync_visibility)

    def _sync_geometry(self) -> None:
        self._border.setGeometry(self._central_widget.rect())
        self._slot_label.setText(
            f"SLOT {get_active_incognito_position_slot()}"
        )
        self._slot_label.adjustSize()
        self._slot_label.move(
            (self._border.width() - self._slot_label.width()) // 2,
            (self._border.height() - self._slot_label.height()) // 2,
        )

    def _event_is_in_main_window(self, watched: QObject) -> bool:
        if watched is mw:
            return True

        window = getattr(watched, "window", None)
        return callable(window) and window() is mw

    def sync_visibility(self) -> None:
        modifiers = QApplication.queryKeyboardModifiers()
        visible = incognito_mode and bool(
            modifiers
            & (
                Qt.KeyboardModifier.ShiftModifier
                | Qt.KeyboardModifier.ControlModifier
            )
        )

        if visible:
            self._sync_geometry()
            self._border.show()
            self._border.raise_()
            self._slot_label.show()
            if not self._modifier_poll_timer.isActive():
                self._modifier_poll_timer.start()
        else:
            self._border.hide()
            self._modifier_poll_timer.stop()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._central_widget and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
        ):
            if self._border.isVisible():
                self._sync_geometry()
                self._border.raise_()

        if (
            event.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease)
            and event.key() in (Qt.Key.Key_Shift, Qt.Key.Key_Control)
            and self._event_is_in_main_window(watched)
        ):
            self.sync_visibility()

        return False


def render_with_incognito_template(card: Card):
    source_notetype = card.note_type()
    configured_fields = configured_fields_for_notetype(source_notetype)
    if configured_fields is None:
        return None

    main_field, extra_fields = configured_fields
    template = deepcopy(card.template())
    # This is a temporary template, so it must not identify itself as the
    # notetype's saved template at ordinal 0. Otherwise Anki fetches the c1
    # card for cloze notes instead of using the current card's ordinal.
    template.pop("ord", None)
    notetype = deepcopy(source_notetype)

    template["qfmt"] = build_incognito_question_template(main_field)
    template["afmt"] = build_incognito_answer_template(main_field, extra_fields)
    light_theme_css, dark_theme_css, incognito_css = get_incognito_styles()
    notetype["css"] = build_incognito_css(
        get_dark_mode_enabled(),
        light_theme_css,
        dark_theme_css,
        incognito_css,
    )

    context = TemplateRenderContext(
        col=mw.col,
        card=card,
        note=card.note(),
        notetype=notetype,
        template=template,
    )

    return context.render()


def redraw_current_card() -> None:
    if mw.state != "review":
        return
    reviewer = getattr(mw, "reviewer", None)
    if reviewer is None or reviewer.card is None:
        return
    reviewer._redraw_current_card()


def redraw_current_screen() -> None:
    if mw.state == "review":
        redraw_current_card()
    elif mw.state == "deckBrowser":
        deck_browser = getattr(mw, "deckBrowser", None)
        if deck_browser is not None:
            deck_browser.refresh()
    elif mw.state == "overview":
        overview = getattr(mw, "overview", None)
        if overview is not None:
            overview.refresh()


def current_incognito_css() -> str:
    light_theme_css, dark_theme_css, incognito_css = get_incognito_styles()
    return build_incognito_css(
        get_dark_mode_enabled(),
        light_theme_css,
        dark_theme_css,
        incognito_css,
    )


def apply_incognito_deck_browser(web_content, context) -> None:
    if (
        not incognito_mode
        or context is not getattr(mw, "deckBrowser", None)
    ):
        return

    web_content.body = build_incognito_deck_browser(
        context,
        current_incognito_css(),
    )


def apply_incognito_overview(web_content, context) -> None:
    if (
        not incognito_mode
        or context is not getattr(mw, "overview", None)
    ):
        return

    web_content.body = build_incognito_overview(
        context,
        current_incognito_css(),
    )


def show_incognito_finished_overview(overview, _old) -> None:
    if not incognito_mode:
        _old(overview)
        return

    overview.web.stdHtml(
        build_incognito_overview(
            overview,
            current_incognito_css(),
        ),
        context=overview,
    )


def apply_incognito_card_template(
    original_html: str,
    card: Card,
    context: str,
) -> str:
    if not incognito_mode:
        return original_html

    if context not in ("reviewQuestion", "reviewAnswer"):
        return original_html

    try:
        source_notetype = card.note_type()
        if (
            source_notetype["type"] == MODEL_CLOZE
            and configured_fields_for_notetype(source_notetype) is None
        ):
            if get_unconfigured_template_warnings_hidden():
                return original_html
            return UNCONFIGURED_TEMPLATE_WARNING_HTML + original_html

        rendered = render_with_incognito_template(card)
    except Exception:
        return original_html

    if rendered is None:
        return original_html

    if context == "reviewQuestion":
        return rendered.question_and_style()

    return rendered.answer_and_style()


def apply_dark_mode(enabled: bool) -> None:
    save_dark_mode_enabled(enabled)
    redraw_current_screen()


def add_incognito_context_menu_action(webview, menu) -> None:
    if not incognito_mode or webview is not mw.web:
        return

    menu.addSeparator()
    exit_action = QAction("Exit Incognito Mode", menu)
    qconnect(exit_action.triggered, leave_incognito_before_profile_close)
    menu.addAction(exit_action)


def setup_menu() -> None:
    global toggle_action, dark_mode_action
    menu = mw.form.menubar.addMenu("Epic Anki")
    toggle_action = QAction("Incognito Mode (F6)", mw)
    toggle_action.setCheckable(True)
    qconnect(toggle_action.toggled, apply_incognito)
    menu.addAction(toggle_action)

    menu.addSeparator()

    dark_mode_action = QAction("Dark Mode", mw)
    dark_mode_action.setCheckable(True)
    dark_mode_action.setChecked(get_dark_mode_enabled())
    qconnect(dark_mode_action.toggled, apply_dark_mode)
    menu.addAction(dark_mode_action)

    menu.addSeparator()

    configuration_action = QAction("Configure Note Types...", mw)
    configuration_action.setMenuRole(QAction.MenuRole.NoRole)
    qconnect(configuration_action.triggered, open_configuration_dialog)
    menu.addAction(configuration_action)

    usage_guide_action = QAction("Usage Guide", mw)
    usage_guide_action.setMenuRole(QAction.MenuRole.NoRole)
    qconnect(usage_guide_action.triggered, open_usage_guide)
    menu.addAction(usage_guide_action)


def setup_hotkey() -> None:
    shortcut = QShortcut(QKeySequence("F6"), mw)
    qconnect(shortcut.activated, toggle_incognito)
    mw.epic_anki_shortcut = shortcut


def setup_zoom_shortcuts() -> None:
    zoom_in_shortcut = QShortcut(QKeySequence("Ctrl+="), mw)
    zoom_in_shortcut.setEnabled(False)
    qconnect(zoom_in_shortcut.activated, lambda: adjust_incognito_zoom(0.1))
    mw.epic_anki_zoom_in_shortcut = zoom_in_shortcut

    zoom_out_shortcut = QShortcut(mw)
    zoom_out_shortcut.setKeys(QKeySequence.StandardKey.ZoomOut)
    zoom_out_shortcut.setEnabled(False)
    qconnect(zoom_out_shortcut.activated, lambda: adjust_incognito_zoom(-0.1))
    mw.epic_anki_zoom_out_shortcut = zoom_out_shortcut


def setup_position_slot_shortcuts() -> None:
    shortcuts = []
    for key_sequence, offset in (
        ("Ctrl+Left", -1),
        ("Ctrl+Right", 1),
        ("Shift+Left", -1),
        ("Shift+Right", 1),
    ):
        shortcut = QShortcut(QKeySequence(key_sequence), mw)
        shortcut.setEnabled(False)
        qconnect(
            shortcut.activated,
            lambda offset=offset: switch_incognito_position_slot(offset),
        )
        shortcuts.append(shortcut)
    mw.epic_anki_position_slot_shortcuts = shortcuts


def setup_window_drag() -> None:
    drag_filter = IncognitoWindowDragFilter(mw)
    QApplication.instance().installEventFilter(drag_filter)
    mw.epic_anki_drag_filter = drag_filter


def setup_window_resize() -> None:
    resize_filter = IncognitoWindowResizeFilter(mw)
    QApplication.instance().installEventFilter(resize_filter)
    mw.epic_anki_resize_filter = resize_filter


def setup_modifier_border() -> None:
    modifier_border_filter = IncognitoModifierBorderFilter(mw)
    QApplication.instance().installEventFilter(modifier_border_filter)
    mw.epic_anki_modifier_border_filter = modifier_border_filter


def setup_hooks() -> None:
    gui_hooks.card_will_show.append(apply_incognito_card_template)
    gui_hooks.profile_will_close.append(leave_incognito_before_profile_close)
    gui_hooks.webview_will_set_content.append(apply_incognito_deck_browser)
    gui_hooks.webview_will_set_content.append(apply_incognito_overview)
    gui_hooks.webview_will_show_context_menu.append(
        add_incognito_context_menu_action
    )


def setup_finished_overview() -> None:
    Overview._show_finished_screen = wrap(
        Overview._show_finished_screen,
        show_incognito_finished_overview,
        "around",
    )


setup_configuration_dialog(redraw_current_screen)
setup_usage_guide_dialog()
setup_menu()
setup_hotkey()
setup_zoom_shortcuts()
setup_position_slot_shortcuts()
setup_window_drag()
setup_window_resize()
setup_modifier_border()
setup_hooks()
setup_finished_overview()
