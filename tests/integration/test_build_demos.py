"""
Full-build integration tests for MkDocs, Material for MkDocs, and Zensical.

Each test builds a realistic demo project into tests/demos/<framework>/ so the
output is inspectable in VSCode. Every assertion is automated — no manual steps
required. Running the tests twice is safe: the output directory is wiped and
rebuilt on each run.
"""

from __future__ import annotations

import os
import shutil
import textwrap
from pathlib import Path

import pytest

# Resolved once: tests/demos/ lives inside the project tree.
DEMOS_DIR = Path(__file__).parent.parent / "demos"

# Shared source content used by both demo builds.
TREEVIEW_MD = textwrap.dedent("""\
    # Treeview Demo

    ASCII tree (material icons by file extension / folder type):

    ```treeview
    ├── src/
    │   ├── main.py
    │   └── utils.py
    ├── tests/
    │   └── test_main.py
    ├── Dockerfile
    ├── tsconfig.json
    └── README.md
    ```
""")

EXPECTED_ICONS = {
    "tv-icon-folder-src-open",
    "tv-icon-python",
    "tv-icon-folder-test-open",
    "tv-icon-docker",
    "tv-icon-tsconfig",
    "tv-icon-readme",
}


# ---------------------------------------------------------------------------
# MkDocs demo build
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mkdocs_demo() -> Path:
    """Build the MkDocs demo into tests/demos/mkdocs/ and return its root."""
    import mkdocs.commands.build
    import mkdocs.config

    root = DEMOS_DIR / "mkdocs"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    docs = root / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(TREEVIEW_MD, encoding="utf-8")

    (root / "mkdocs.yml").write_text(
        textwrap.dedent("""\
            site_name: Treeview Demo
            docs_dir: docs
            plugins:
              - treeview:
                  icon_mode: embedded
        """),
        encoding="utf-8",
    )

    cfg = mkdocs.config.load_config(
        config_file=str(root / "mkdocs.yml"),
        site_dir=str(root / "site"),
    )
    mkdocs.commands.build.build(cfg)
    return root


def test_mkdocs_demo_html_contains_treeview(mkdocs_demo: Path):
    """Built HTML has the treeview div and correct file/folder names."""
    html = (mkdocs_demo / "site" / "index.html").read_text(encoding="utf-8")
    assert '<div class="treeview">' in html
    assert "src/" in html
    assert "main.py" in html
    assert "Dockerfile" in html
    assert "README.md" in html


def test_mkdocs_demo_css_linked_in_html(mkdocs_demo: Path):
    """The plugin registers treeview.css with MkDocs so it appears in <head>."""
    html = (mkdocs_demo / "site" / "index.html").read_text(encoding="utf-8")
    assert "assets/treeview/treeview.css" in html, (
        "CSS <link> not found in HTML <head> — plugin did not register extra_css"
    )


def test_mkdocs_demo_css_is_lean(mkdocs_demo: Path):
    """Generated CSS contains only the icons actually used (dynamic, not 1.3 MB)."""
    css_path = mkdocs_demo / "site" / "assets" / "treeview" / "treeview.css"
    assert css_path.exists(), "treeview.css not written to site/assets/treeview/"

    css = css_path.read_text(encoding="utf-8")

    # Embedded mode: base64 data URIs
    assert "data:image/svg+xml;base64," in css

    # All expected icon classes are present
    for cls in EXPECTED_ICONS:
        assert cls in css, f"expected icon class '{cls}' missing from CSS"

    # Sanity: file is small — only 6 icons, not 1120
    size = css_path.stat().st_size
    assert size < 50_000, (
        f"CSS is {size} bytes — looks like all icons were embedded instead of only used ones"
    )


def test_mkdocs_demo_icon_classes_in_html(mkdocs_demo: Path):
    """Every rendered list item has a tv-icon-* CSS class."""
    html = (mkdocs_demo / "site" / "index.html").read_text(encoding="utf-8")
    for cls in EXPECTED_ICONS:
        assert cls in html, f"icon class '{cls}' missing from rendered HTML"


# ---------------------------------------------------------------------------
# Zensical demo build
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def zensical_demo() -> Path:
    """Build the Zensical demo into tests/demos/zensical/ and return its root."""
    from zensical import build as zensical_build

    root = DEMOS_DIR / "zensical"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    docs = root / "docs"
    docs.mkdir()
    (docs / "treeview.md").write_text(TREEVIEW_MD, encoding="utf-8")
    # Second page with a distinct icon (Rust) not present on treeview.md.
    # Proves the CSS accumulates icons across pages instead of only keeping
    # the last page's icons.
    (docs / "extra.md").write_text(
        "# Extra\n\n```treeview\n└── main.rs\n```\n", encoding="utf-8"
    )
    (docs / "index.md").write_text(
        "# Home\n\nSee [Treeview](treeview.md) and [Extra](extra.md).\n", encoding="utf-8"
    )

    (root / "zensical.toml").write_text(
        textwrap.dedent("""\
            [project]
            site_name = "Treeview Demo"
            extra_css = ["stylesheets/treeview.css"]

            [[project.theme.palette]]
            scheme = "default"

            [project.markdown_extensions."mkdocs_treeview.extension"]
            css_output_path = "docs/stylesheets/treeview.css"
            icon_mode = "embedded"
        """),
        encoding="utf-8",
    )

    # zensical.build() requires an absolute config path and cwd = project root
    orig_cwd = os.getcwd()
    try:
        os.chdir(root)
        zensical_build(str(root / "zensical.toml"), {"clean": False, "strict": False})
    finally:
        os.chdir(orig_cwd)

    return root


def test_zensical_demo_html_contains_treeview(zensical_demo: Path):
    """Built HTML has the treeview div and correct file/folder names."""
    html = (zensical_demo / "site" / "treeview" / "index.html").read_text(encoding="utf-8")
    assert '<div class="treeview">' in html
    assert "src/" in html
    assert "main.py" in html
    assert "Dockerfile" in html
    assert "README.md" in html


def test_zensical_demo_css_linked_in_html(zensical_demo: Path):
    """extra_css in zensical.toml causes a <link> tag to appear in the HTML."""
    html = (zensical_demo / "site" / "treeview" / "index.html").read_text(encoding="utf-8")
    assert "treeview.css" in html, (
        "CSS <link> not found in Zensical HTML — extra_css not wired up correctly"
    )


def test_zensical_demo_css_is_lean(zensical_demo: Path):
    """Generated CSS contains only the icons actually used (dynamic, not 1.3 MB).

    The manifest lives in .cache/ (a build artifact, not part of the served site).
    The CSS itself stays in docs/stylesheets/ where extra_css points to it.
    """
    css_path = zensical_demo / "docs" / "stylesheets" / "treeview.css"
    assert css_path.exists(), "treeview.css not written — TreeviewCSSPostprocessor did not run"

    manifest_path = zensical_demo / ".cache" / "treeview.manifest.json"
    assert manifest_path.exists(), (
        ".cache/treeview.manifest.json not written — manifest should be in .cache/, not docs/"
    )
    assert not (zensical_demo / "docs" / "stylesheets" / "treeview.css.manifest.json").exists(), (
        "manifest must not appear in docs/ — it should be in .cache/"
    )

    css = css_path.read_text(encoding="utf-8")

    # Embedded mode: base64 data URIs
    assert "data:image/svg+xml;base64," in css

    # All expected icon classes are present
    for cls in EXPECTED_ICONS:
        assert cls in css, f"expected icon class '{cls}' missing from CSS"

    # Icon from extra.md (second page) must also be present — proves the
    # registry accumulates icons across all pages, not just the last one.
    assert "tv-icon-rust" in css, (
        "Rust icon (from extra.md) missing — CSS only contains last page's icons"
    )

    # Sanity: file is small — only ~7 icons, not 1120
    size = css_path.stat().st_size
    assert size < 50_000, (
        f"CSS is {size} bytes — looks like all icons were embedded instead of only used ones"
    )


def test_zensical_demo_icon_classes_in_html(zensical_demo: Path):
    """Every rendered list item has a tv-icon-* CSS class."""
    html = (zensical_demo / "site" / "treeview" / "index.html").read_text(encoding="utf-8")
    for cls in EXPECTED_ICONS:
        assert cls in html, f"icon class '{cls}' missing from rendered HTML"


# ---------------------------------------------------------------------------
# Material for MkDocs demo build
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def material_demo() -> Path:
    """Build the Material for MkDocs demo into tests/demos/material/ and return its root."""
    import mkdocs.commands.build
    import mkdocs.config

    root = DEMOS_DIR / "material"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    docs = root / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(TREEVIEW_MD, encoding="utf-8")

    (root / "mkdocs.yml").write_text(
        textwrap.dedent("""\
            site_name: Treeview Demo (Material)
            docs_dir: docs
            theme:
              name: material
            plugins:
              - treeview:
                  icon_mode: embedded
        """),
        encoding="utf-8",
    )

    cfg = mkdocs.config.load_config(
        config_file=str(root / "mkdocs.yml"),
        site_dir=str(root / "site"),
    )
    mkdocs.commands.build.build(cfg)
    return root


def test_material_demo_html_contains_treeview(material_demo: Path):
    """Built HTML has the treeview div and correct file/folder names."""
    html = (material_demo / "site" / "index.html").read_text(encoding="utf-8")
    assert '<div class="treeview">' in html
    assert "src/" in html
    assert "main.py" in html
    assert "Dockerfile" in html
    assert "README.md" in html


def test_material_demo_css_linked_in_html(material_demo: Path):
    """The plugin registers treeview.css with Material so it appears in the page."""
    html = (material_demo / "site" / "index.html").read_text(encoding="utf-8")
    assert "assets/treeview/treeview.css" in html, (
        "CSS <link> not found in Material HTML — plugin did not register extra_css"
    )


def test_material_demo_css_is_lean(material_demo: Path):
    """Generated CSS contains only the icons actually used (dynamic, not 1.3 MB)."""
    css_path = material_demo / "site" / "assets" / "treeview" / "treeview.css"
    assert css_path.exists(), "treeview.css not written to site/assets/treeview/"

    css = css_path.read_text(encoding="utf-8")

    # Embedded mode: base64 data URIs
    assert "data:image/svg+xml;base64," in css

    # All expected icon classes are present
    for cls in EXPECTED_ICONS:
        assert cls in css, f"expected icon class '{cls}' missing from CSS"

    # Sanity: file is small — only 6 icons, not 1120
    size = css_path.stat().st_size
    assert size < 50_000, (
        f"CSS is {size} bytes — looks like all icons were embedded instead of only used ones"
    )


def test_material_demo_icon_classes_in_html(material_demo: Path):
    """Every rendered list item has a tv-icon-* CSS class."""
    html = (material_demo / "site" / "index.html").read_text(encoding="utf-8")
    for cls in EXPECTED_ICONS:
        assert cls in html, f"icon class '{cls}' missing from rendered HTML"
