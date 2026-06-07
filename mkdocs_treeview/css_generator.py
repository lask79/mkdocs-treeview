"""
CSS generator for treeview icons.

Supports three icon_mode values:
- files: relative URL to copied SVG assets
- embedded: base64 data URI inline in CSS
- cdn: jsDelivr CDN URL (no local files needed)
"""

from __future__ import annotations

import base64
from pathlib import Path

CDN_BASE = "https://cdn.jsdelivr.net/npm/vscode-material-icon-theme@{version}/icons"
DEFAULT_CDN_VERSION = "5.35.0"

_BASE_CSS = """\
/* mkdocs-treeview — generated, do not edit */
.treeview { font-family: monospace; line-height: 1.1; }
.tv-line { display: flex; align-items: center; }
.tv-line-element { display: contents; }
.tv-item-name { margin-left: 5px; }
.tv-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  background-repeat: no-repeat;
  background-size: contain;
}
"""

_DARK_SELECTOR = '[data-md-color-scheme="slate"]'


def generate_css(
    icons: list[tuple[str, str, str]],
    icon_mode: str,
    icons_dir: Path | None = None,
    assets_path: str = "assets/treeview/icons",
    cdn_version: str = DEFAULT_CDN_VERSION,
) -> str:
    """
    Generate CSS for the given list of (css_class, dark_svg, light_svg) tuples.

    icons_dir: path to the local icons directory (required for 'embedded' mode).
    assets_path: URL path used in 'files' mode CSS rules.
    """
    parts = [_BASE_CSS]

    for css_class, dark_svg, light_svg in icons:
        dark_url = _resolve_url(dark_svg, icon_mode, icons_dir, assets_path, cdn_version)
        if dark_url is None:
            continue

        parts.append(f".{css_class} {{ background-image: url('{dark_url}'); }}")

        # Light mode override: Material uses [data-md-color-scheme="slate"] for dark,
        # so the "default" scheme is light. We emit a light override for the default scheme.
        if light_svg != dark_svg:
            light_url = _resolve_url(light_svg, icon_mode, icons_dir, assets_path, cdn_version)
            if light_url:
                parts.append(
                    f":root:not({_DARK_SELECTOR}) .{css_class} "
                    f"{{ background-image: url('{light_url}'); }}"
                )

    return "\n".join(parts) + "\n"


def _resolve_url(
    svg_name: str,
    icon_mode: str,
    icons_dir: Path | None,
    assets_path: str,
    cdn_version: str,
) -> str | None:
    if icon_mode == "cdn":
        base = CDN_BASE.format(version=cdn_version)
        return f"{base}/{svg_name}"

    if icon_mode == "embedded":
        if icons_dir is None:
            return None
        svg_path = icons_dir / svg_name
        if not svg_path.exists():
            return None
        data = base64.b64encode(svg_path.read_bytes()).decode()
        return f"data:image/svg+xml;base64,{data}"

    # files mode
    return f"{assets_path}/{svg_name}"
