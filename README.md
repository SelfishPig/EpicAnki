# Epic Anki User Guide

Epic Anki adds a focused, frameless review mode for configured cloze note types. It can replace the normal cloze layout, deck browser, and deck overview with compact incognito layouts, remember several window positions, and keep separate light and dark styles.

## Getting Started

1. Open Anki and choose **Epic Anki > Configure Note Types...**.
2. Select a cloze note type. Non-cloze note types are listed but cannot be configured.
3. Choose the field containing the main cloze text.
4. Check any additional fields that should appear on the answer side. Drag checked fields into the order you want.
5. Select **Save**. Configured note types are highlighted in the list.
6. Start reviewing and press **F6** to enter Incognito Mode.

When a configured cloze card is shown in Incognito Mode, the main cloze field is used on the question and answer sides. Checked additional fields are shown below it on the answer side.

## Epic Anki Menu

- **Incognito Mode (F6)** enters or leaves the focused review window.
- **Dark Mode** selects the dark incognito style.
- **Configure Note Types...** opens note-type and style configuration.
- **Usage Guide** opens this guide inside Anki.

The menu bar is hidden while Incognito Mode is active. Press **F6** to return to the normal window and access the menu again.

## Keyboard and Mouse Controls

| Control | Action |
| --- | --- |
| **F6** | Enter or leave Incognito Mode. |
| **Ctrl+=** | Increase incognito card zoom. |
| **Ctrl+-** | Decrease incognito card zoom. Anki may use the platform's standard Zoom Out shortcut. |
| **Shift+Left Arrow** or **Ctrl+Left Arrow** | Switch to the previous position slot. |
| **Shift+Right Arrow** or **Ctrl+Right Arrow** | Switch to the next position slot. |
| **Shift+Left Mouse Drag** | Move the frameless incognito window. |
| **Ctrl+Left Mouse Drag** | Resize the window from the corner corresponding to the pointer's quadrant. |
| **Click an image** | Expand or collapse an image in the incognito card layout. |

Zoom and position-slot shortcuts are active only in Incognito Mode. Incognito zoom is saved independently from normal Anki zoom.

## Position Slots

Incognito Mode has four window-position slots. Hold **Ctrl** or **Shift** to display the window border and the active slot number in the center of the window.

Use **Ctrl/Shift+Left Arrow** or **Ctrl/Shift+Right Arrow** to move between slots. Slot selection wraps between Slot 1 and Slot 4. Switching slots saves the window geometry for the slot you leave and immediately restores the geometry saved for the destination slot. Leaving Incognito Mode also saves the active slot.

To arrange the slots:

1. Switch to a slot.
2. Hold **Shift** and drag to move the window.
3. Hold **Ctrl** and drag to resize it if needed.
4. Switch to another slot or leave Incognito Mode to save that geometry.

Slot 1 uses the original incognito window position from versions without multiple slots. The active slot is remembered between Anki sessions.

## Unconfigured Cloze Cards

An unconfigured cloze card continues to use its normal Anki template in Incognito Mode. A banner at the top warns that its note type has not been configured.

To disable these banners, open **Epic Anki > Configure Note Types...** and check **Hide unconfigured template warnings**. The setting takes effect immediately. A saved configuration that is no longer valid because its fields changed is also treated as unconfigured.

## Managing Note Types

Open **Epic Anki > Configure Note Types...** and select a cloze note type to edit it.

- **Main cloze field** controls the field rendered as the primary card content.
- **Additional fields shown on the back** can be checked, unchecked, and dragged into a custom order.
- **Save** stores the current selections.
- **Remove Configuration** returns that note type to its normal Anki template in Incognito Mode.
- **Back** leaves the editor without saving changes.

If a note type is renamed, Epic Anki continues to identify it by its Anki note-type ID. If configured fields are renamed or removed, update the saved configuration before using its incognito template again.

## Style Editor

Select **Style Editor...** at the bottom of the configuration window. It provides three CSS fields:

- **Light Theme CSS** defines the light color scheme and variables.
- **Dark Theme CSS** defines the dark color scheme and variables.
- **Shared Incognito CSS** contains layout and component styling used by both themes.

Select **Save** to store all three fields and redraw the current Anki screen. **Back** discards unsaved edits. **Restore Defaults** replaces the fields with the factory styles; select **Save** afterward to persist the restored values.

Epic Anki does not validate custom CSS. If a style causes display problems, restore the defaults and save them.

## Incognito Mode Behavior

While Incognito Mode is active, Epic Anki:

- hides Anki's toolbar, bottom bar, and menu bar;
- changes the main window to a frameless focused view;
- applies the saved incognito zoom;
- replaces the deck browser and deck overview with plaintext versions;
- renders configured cloze note types with the incognito template;
- uses the selected light or dark theme plus the shared CSS; and
- preserves normal Anki rendering for other cards.

Leaving Incognito Mode restores the normal window frame, controls, geometry, and zoom.

## Troubleshooting

- **A cloze card shows its normal template:** Configure its note type and ensure the selected fields still exist.
- **The configuration cannot be saved correctly:** Reopen the note type after changing its fields in Anki.
- **The window is difficult to move:** Hold **Shift** while dragging with the left mouse button.
- **The window is difficult to resize:** Hold **Ctrl** and drag with the left mouse button from the quadrant matching the desired corner.
- **Custom styling is broken:** Open the Style Editor, select **Restore Defaults**, and then select **Save**.
- **The menu is missing:** Press **F6** to leave Incognito Mode; the normal Anki menu will return.
