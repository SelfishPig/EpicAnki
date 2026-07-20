INCOGNITO_LIGHT_THEME_CSS = """
:root {
  color-scheme: light;
  --fg-color: #000000;
  --bg-color: #ffffff;
}
""".strip("\r\n")

INCOGNITO_DARK_THEME_CSS = """
:root {
  color-scheme: dark;
  --fg-color: #ffffff;
  --bg-color: #121112;
}
""".strip("\r\n")

INCOGNITO_CSS = """
:root {
  --accent-color: #667788;
}

html,
body {
  background: var(--bg-color) !important;
  color: var(--fg-color) !important;
}

body {
  margin: 5px;
  font-family: Arial, sans-serif;
  font-size: 12px;
  line-height: 1.4;
  text-align: left !important;
}

p {
  margin-top: 0;
}

center {
  display: block;
  text-align: left !important;
}

center > br {
  display: none;
}

h3 {
  color: var(--fg-color) !important;
  font-size: inherit;
  margin: 0 0 12px;
  text-align: left;
}

.card,
.card.night_mode {
  background-color: var(--bg-color);
  color: var(--fg-color);
}

.card::-webkit-scrollbar {
  display: none;
}

.cloze b,
.cloze u,
.cloze i,
.cloze b > i,
.cloze i > b,
.cloze {
  font-weight: bold;
}

.avfElement.screenGlow {
  display: none;
}

.replay-button {
  display: none;
}

.main img {
  cursor: zoom-in;
  border: 2px solid var(--accent-color);
}

.main img:not(.epic-anki-image-expanded) {
  width: auto !important;
  height: auto !important;
  max-width: 120px !important;
  max-height: 120px !important;
  object-fit: contain;
}

.main img.epic-anki-image-expanded {
  max-width: 100% !important;
  max-height: none !important;
  height: auto !important;
  cursor: zoom-out;
}

.divider {
  border-top: 2px solid var(--accent-color);
  margin-top: 15px;
  margin-bottom: 15px;
  height: 0px;
}

.extra {
  margin-left: 10px;
  margin-bottom: 20px;
}

.extra-header {
  font-weight: bold;
  color: var(--accent-color);
}

.extra-content {
  border-left: 5px solid var(--accent-color);
  padding-left: 5px;
  margin: 0px;
}

a,
a:link,
a:visited {
  color: var(--fg-color) !important;
  cursor: pointer;
  text-decoration: underline;
}

ul {
  margin: 0;
  padding-left: 20px;
}

li {
  margin: 0 0 4px;
}

li > ul {
  margin-top: 4px;
}

.epic-anki-screen-line {
  margin: 0 0 6px;
}

.epic-anki-screen-actions {
  margin-top: 12px;
}
""".strip("\r\n")


def build_incognito_css(
    dark_mode_enabled: bool,
    light_theme_css: str = INCOGNITO_LIGHT_THEME_CSS,
    dark_theme_css: str = INCOGNITO_DARK_THEME_CSS,
    incognito_css: str = INCOGNITO_CSS,
) -> str:
    theme_css = dark_theme_css if dark_mode_enabled else light_theme_css
    return theme_css + "\n\n" + incognito_css


def build_incognito_style_tag(incognito_css: str) -> str:
    return f"<style>\n{incognito_css}\n</style>"
