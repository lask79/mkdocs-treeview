"""
Python-Markdown extension for treeview fenced code blocks.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from markdown import Extension
from markdown.postprocessors import Postprocessor
from markdown.preprocessors import Preprocessor

from mkdocs_treeview.css_generator import generate_css
from mkdocs_treeview.parser import parse
from mkdocs_treeview.renderer import IconRegistry, render

FENCE_RE = re.compile(r"^```treeview\s*$")
FENCE_END_RE = re.compile(r"^```\s*$")

ICONS_PKG_DIR = Path(__file__).parent / "icons"


class TreeviewPreprocessor(Preprocessor):
    """Preprocessor that handles ```treeview fenced code blocks."""

    def __init__(self, md: Any, registry: IconRegistry):
        super().__init__(md)
        self.registry = registry

    def run(self, lines: list[str]) -> list[str]:
        new_lines: list[str] = []
        i = 0
        while i < len(lines):
            if FENCE_RE.match(lines[i]):
                block_lines = []
                i += 1
                while i < len(lines) and not FENCE_END_RE.match(lines[i]):
                    block_lines.append(lines[i])
                    i += 1
                # If loop ended without finding closing fence, treat gathered
                # lines as the block content (unclosed fence is handled gracefully).
                source = "\n".join(block_lines)
                try:
                    root = parse(source)
                    html = render(root, self.registry)
                    placeholder = self.md.htmlStash.store(html)
                    # Blank lines around placeholder prevent <p> wrapping
                    new_lines.extend(["", placeholder, ""])
                except Exception as exc:
                    err = f'<div class="treeview-error">treeview parse error: {exc}</div>'
                    placeholder = self.md.htmlStash.store(err)
                    new_lines.extend(["", placeholder, ""])
            else:
                new_lines.append(lines[i])
            i += 1
        return new_lines


class TreeviewCSSPostprocessor(Postprocessor):
    """Writes a lean CSS file containing only the icons used so far.

    Registered when css_output_path is set on TreeviewExtension. Since
    Zensical (and similar pipelines) create a new Markdown() instance per
    page, this runs after every page. The registry accumulates icons across
    all pages; each write overwrites the previous file. By the last page the
    file contains exactly the icons referenced across the whole site.
    """

    def __init__(
        self,
        md: Any,
        registry: IconRegistry,
        css_output_path: Path,
        icon_mode: str,
        icons_dir: Path,
    ):
        super().__init__(md)
        self.registry = registry
        self.css_output_path = css_output_path
        self.icon_mode = icon_mode
        self.icons_dir = icons_dir

    def run(self, text: str) -> str:
        icons = self.registry.items()
        if icons:
            self.css_output_path.parent.mkdir(parents=True, exist_ok=True)
            css = generate_css(
                icons=icons,
                icon_mode=self.icon_mode,
                icons_dir=self.icons_dir if self.icon_mode == "embedded" else None,
                assets_path="icons",
            )
            self.css_output_path.write_text(css, encoding="utf-8")
        return text


class TreeviewExtension(Extension):
    """Markdown extension for treeview code blocks.

    Optional kwargs (used when the extension is loaded without the MkDocs
    plugin, e.g. directly in Zensical):

    - registry: IconRegistry — shared across pages; created if not provided
    - css_output_path: str|Path — if set, a CSS file is written here after
      each page, containing only the icons used so far (dynamic, lean output)
    - icon_mode: str — "embedded" (default) or "files"; controls CSS format
    """

    def __init__(self, **kwargs: Any) -> None:
        self.registry: IconRegistry = kwargs.pop("registry", None) or IconRegistry()
        self._css_output_path: Path | None = (
            Path(kwargs.pop("css_output_path")) if "css_output_path" in kwargs else None
        )
        self._icon_mode: str = kwargs.pop("icon_mode", "embedded")
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Any) -> None:
        md.preprocessors.register(
            TreeviewPreprocessor(md, self.registry),
            "treeview",
            # Priority 27: runs AFTER normalize_whitespace (30) so STX/ETX
            # stash placeholders are not stripped, and BEFORE html_block (20)
            # so treeview claims its blocks first.
            27,
        )
        if self._css_output_path is not None:
            md.postprocessors.register(
                TreeviewCSSPostprocessor(
                    md,
                    self.registry,
                    self._css_output_path,
                    self._icon_mode,
                    ICONS_PKG_DIR,
                ),
                "treeview_css",
                # Priority 0: run last, after all HTML is finalised.
                0,
            )


def makeExtension(**kwargs: object) -> TreeviewExtension:
    return TreeviewExtension(**kwargs)
