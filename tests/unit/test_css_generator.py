import base64
import tempfile
from pathlib import Path

from mkdocs_treeview.css_generator import generate_css

SAMPLE_ICONS = [
    ("tv-icon-python", "python.svg", "python.svg"),
    ("tv-icon-typescript", "typescript.svg", "typescript_light.svg"),
]


def test_files_mode_uses_relative_urls():
    css = generate_css(SAMPLE_ICONS, icon_mode="files", assets_path="assets/treeview/icons")
    assert "assets/treeview/icons/python.svg" in css
    assert "assets/treeview/icons/typescript.svg" in css


def test_files_mode_emits_light_override():
    css = generate_css(SAMPLE_ICONS, icon_mode="files")
    assert "typescript_light.svg" in css
    assert ":root:not(" in css


def test_files_mode_no_light_override_when_same():
    icons = [("tv-icon-python", "python.svg", "python.svg")]
    css = generate_css(icons, icon_mode="files")
    assert ":root:not(" not in css


def test_cdn_mode_uses_jsdelivr():
    css = generate_css(SAMPLE_ICONS, icon_mode="cdn", cdn_version="5.35.0")
    assert "cdn.jsdelivr.net" in css
    assert "5.35.0" in css
    assert "python.svg" in css


def test_embedded_mode_inlines_base64():
    with tempfile.TemporaryDirectory() as tmp:
        icons_dir = Path(tmp)
        (icons_dir / "python.svg").write_bytes(b"<svg/>")
        icons = [("tv-icon-python", "python.svg", "python.svg")]
        css = generate_css(icons, icon_mode="embedded", icons_dir=icons_dir)
        assert "data:image/svg+xml;base64," in css
        encoded = base64.b64encode(b"<svg/>").decode()
        assert encoded in css


def test_embedded_mode_skips_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        icons_dir = Path(tmp)
        # No SVG files in tmp
        icons = [("tv-icon-python", "python.svg", "python.svg")]
        css = generate_css(icons, icon_mode="embedded", icons_dir=icons_dir)
        # Rule should be absent since file doesn't exist
        assert "tv-icon-python" not in css


def test_base_css_always_present():
    css = generate_css([], icon_mode="files")
    assert ".treeview" in css
    assert ".tv-icon" in css
