"""
Python-Markdown extension for treeview fenced code blocks.
"""

from __future__ import annotations

import json
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
    """Writes a lean CSS file accumulating icons from all rendered pages.

    Registered when css_output_path is set on TreeviewExtension. Zensical's
    Rust core isolates each page render in its own Python sub-interpreter, so
    module-level state cannot be shared across pages. Instead, a JSON manifest
    (css_output_path + ".manifest.json") persists the full icon registry on
    disk. Each page render merges its icons into the manifest, then regenerates
    the CSS. Every write is additive — no previously seen icon is ever lost.
    """

    def __init__(
        self,
        md: Any,
        registry: IconRegistry,
        css_output_path: Path,
        icon_mode: str,
        icons_dir: Path,
        manifest_path: Path | None = None,
    ):
        super().__init__(md)
        self.registry = registry
        self.css_output_path = css_output_path
        self.manifest_path = manifest_path or (
            Path.cwd() / ".cache" / f"{css_output_path.stem}.manifest.json"
        )
        self.icon_mode = icon_mode
        self.icons_dir = icons_dir

    def _load_manifest(self) -> dict[str, tuple[str, str]]:
        """Load the persisted icon registry from disk, or return empty dict."""
        if not self.manifest_path.exists():
            return {}
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return {cls: tuple(pair) for cls, pair in data.items()}  # type: ignore[misc]
        except Exception:
            return {}

    def _save_manifest(self, registry: dict[str, tuple[str, str]]) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(registry, indent=2), encoding="utf-8"
        )

    def run(self, text: str) -> str:
        this_page_icons = self.registry.items()
        if not this_page_icons:
            return text

        # Merge this page's icons into the persisted manifest.
        manifest = self._load_manifest()
        for cls, dark, light in this_page_icons:
            manifest[cls] = (dark, light)

        self.css_output_path.parent.mkdir(parents=True, exist_ok=True)
        self._save_manifest(manifest)

        merged = [(cls, dark, light) for cls, (dark, light) in manifest.items()]
        css = generate_css(
            icons=merged,
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
        self._manifest_path: Path | None = (
            Path(kwargs.pop("manifest_path")) if "manifest_path" in kwargs else None
        )
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
                    manifest_path=self._manifest_path,
                ),
                "treeview_css",
                # Priority 0: run last, after all HTML is finalised.
                0,
            )


def makeExtension(**kwargs: object) -> TreeviewExtension:
    return TreeviewExtension(**kwargs)
