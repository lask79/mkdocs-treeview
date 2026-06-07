"""
MkDocs plugin for treeview.

Hooks:
- on_config: inject the Markdown extension, configure icon mode
- on_page_content: (via extension) render treeview blocks, collect used icons
- on_post_build: copy used SVGs to site assets, write generated CSS
"""

from __future__ import annotations

import shutil
from pathlib import Path

from mkdocs.config import config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin

from mkdocs_treeview.css_generator import generate_css
from mkdocs_treeview.extension import TreeviewExtension
from mkdocs_treeview.renderer import IconRegistry

ICONS_PKG_DIR = Path(__file__).parent / "icons"


class TreeviewPlugin(BasePlugin):
    config_scheme = (("icon_mode", config_options.Type(str, default="files")),)

    def __init__(self) -> None:
        super().__init__()
        self._registry = IconRegistry()
        self._extension: TreeviewExtension | None = None

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        icon_mode = self.config["icon_mode"]
        if icon_mode not in ("files", "embedded", "cdn"):
            raise ValueError(
                f"treeview: icon_mode must be 'files', 'embedded', or 'cdn', got '{icon_mode}'"
            )

        self._registry.clear()
        self._extension = TreeviewExtension(registry=self._registry)

        # Remove any previously registered instance (guard against hot-reload double-registration)
        config["markdown_extensions"] = [
            e for e in config["markdown_extensions"] if not isinstance(e, TreeviewExtension)
        ]
        config["markdown_extensions"].append(self._extension)

        # Register the generated CSS so MkDocs injects a <link> tag into every page.
        css_ref = "assets/treeview/treeview.css"
        if css_ref not in config["extra_css"]:
            config["extra_css"].append(css_ref)

        return config

    def on_post_build(self, config: MkDocsConfig) -> None:
        icon_mode = self.config["icon_mode"]
        site_dir = Path(config["site_dir"])
        icons_used = self._registry.items()

        if not icons_used:
            return

        assets_dir = site_dir / "assets" / "treeview" / "icons"
        css_path = site_dir / "assets" / "treeview" / "treeview.css"
        css_path.parent.mkdir(parents=True, exist_ok=True)

        if icon_mode == "files":
            assets_dir.mkdir(parents=True, exist_ok=True)
            _copy_icons(icons_used, ICONS_PKG_DIR, assets_dir)

        css = generate_css(
            icons=icons_used,
            icon_mode=icon_mode,
            icons_dir=ICONS_PKG_DIR if icon_mode == "embedded" else None,
            # CSS is at assets/treeview/treeview.css; icons are at assets/treeview/icons/
            assets_path="icons",
        )
        css_path.write_text(css, encoding="utf-8")


def _copy_icons(
    icons: list[tuple[str, str, str]],
    src_dir: Path,
    dest_dir: Path,
) -> None:
    seen: set[str] = set()
    for _, dark_svg, light_svg in icons:
        for svg_name in (dark_svg, light_svg):
            if svg_name in seen:
                continue
            seen.add(svg_name)
            src = src_dir / svg_name
            if src.exists():
                shutil.copy2(src, dest_dir / svg_name)
