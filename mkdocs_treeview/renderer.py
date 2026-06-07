"""
HTML renderer for treeview blocks.

Walks a parsed TreeNode tree and emits HTML as flat <span class="tv-line"> rows
with ASCII tree prefix connectors (├──, └──, │), matching the asciidoctor-treeview
rendering approach. Collects used (dark_svg, light_svg) pairs into an icon registry.
"""

from __future__ import annotations

import html as _html

from mkdocs_treeview import icon_finder
from mkdocs_treeview.parser import TreeNode


class IconRegistry:
    """Tracks which icons are used across all rendered treeview blocks."""

    def __init__(self) -> None:
        # css_class -> (dark_svg, light_svg)
        self._icons: dict[str, tuple[str, str]] = {}

    def add(self, css_class: str, dark: str, light: str) -> None:
        self._icons[css_class] = (dark, light)

    def items(self) -> list[tuple[str, str, str]]:
        return [(cls, dark, light) for cls, (dark, light) in self._icons.items()]

    def clear(self) -> None:
        self._icons.clear()


def _svg_to_class(svg_name: str) -> str:
    """Convert an SVG filename to a CSS class name. e.g. 'python.svg' -> 'tv-icon-python'"""
    return "tv-icon-" + svg_name.replace(".svg", "").replace("_light", "").replace(".", "-")


def render(root: TreeNode, registry: IconRegistry) -> str:
    """Render a parsed tree to an HTML string, registering used icons."""
    lines: list[str] = []
    lines.append('<div class="treeview">')
    for i, child in enumerate(root.children):
        is_last = i == len(root.children) - 1
        _render_node(child, lines, registry, prefix="", is_last=is_last)
    lines.append("</div>")
    return "\n".join(lines)


def _render_node(
    node: TreeNode,
    lines: list[str],
    registry: IconRegistry,
    prefix: str,
    is_last: bool,
) -> None:
    name = node.name
    bare = name.rstrip("/")
    is_folder = name.endswith("/") or node.has_children()

    if is_folder:
        if node.has_children():
            dark, light = icon_finder.get_icon_for_open_folder(bare)
        else:
            dark, light = icon_finder.get_icon_for_folder(bare)
    else:
        dark, light = icon_finder.get_icon_for_file(name)

    css_class = _svg_to_class(dark)
    registry.add(css_class, dark, light)

    # Build the ASCII connector prefix for this line
    connector = prefix + ("└── " if is_last else "├── ")
    # Replace spaces with nbsp so they don't collapse in HTML
    connector_html = connector.replace(" ", "&nbsp;")

    escaped = _html.escape(bare if is_folder else name)
    display_name = escaped + ("/" if is_folder else "")

    lines.append(
        f'<span class="tv-line">'
        f'<span class="tv-line-prefix">{connector_html}</span>'
        f'<span class="tv-line-element">'
        f'<i class="tv-icon {css_class}"></i>'
        f'<span class="tv-item-name">{display_name}</span>'
        f"</span>"
        f"</span>"
    )

    if node.has_children():
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            child_is_last = i == len(node.children) - 1
            _render_node(child, lines, registry, prefix=child_prefix, is_last=child_is_last)
