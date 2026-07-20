from __future__ import annotations

from html import escape

from anki.decks import DeckTreeNode
from aqt.deckbrowser import DeckBrowser
from aqt.overview import Overview

from .style import build_incognito_style_tag


def _deck_list_item(node: DeckTreeNode) -> str:
    deck_id = int(node.deck_id)
    children = ""
    if node.children:
        children = "<ul>" + "".join(
            _deck_list_item(child) for child in node.children
        ) + "</ul>"

    return (
        "<li>"
        '<a href="#" '
        f'onclick="return pycmd(\'open:{deck_id}\')">'
        f"{escape(node.name)}</a>"
        f" (N: {node.new_count}, L: {node.learn_count}, "
        f"R:{node.review_count})"
        f"{children}"
        "</li>"
    )


def build_incognito_deck_browser(
    deck_browser: DeckBrowser,
    incognito_css: str,
) -> str:
    render_data = deck_browser._render_data
    deck_list = "".join(
        _deck_list_item(node) for node in render_data.tree.children
    )
    if deck_list:
        deck_list = f"<ul>{deck_list}</ul>"
    else:
        deck_list = '<div class="epic-anki-screen-line">No decks.</div>'

    return (
        f"{build_incognito_style_tag(incognito_css)}"
        '<div class="extra">'
        '<div class="extra-header">Problem List</div>'
        '<div class="extra-content">'
        f"{deck_list}"
        "</div>"
        "</div>"
    )


def build_incognito_overview(
    overview: Overview,
    incognito_css: str,
) -> str:
    deck_name = escape(overview.mw.col.decks.current()["name"])
    new_count, learning_count, review_count = overview.mw.col.sched.counts()
    return f"""
{build_incognito_style_tag(incognito_css)}
<div class="extra">
  <div class="extra-header">Assessment/Plan</div>
  <div class="extra-content">
    <ul>
      <li>{deck_name}
        <ul>
          <li>New: {new_count}</li>
          <li>Learning: {learning_count}</li>
          <li>Review: {review_count}</li>
        </ul>
      </li>
    </ul>
  </div>
</div>
<div class="epic-anki-screen-actions">
  <a href="#"
     onclick="return pycmd('decks')">[Back]</a>
  ·
  <a href="#"
     onclick="return pycmd('study')">[Study Now]</a>
</div>
""".strip("\r\n")
