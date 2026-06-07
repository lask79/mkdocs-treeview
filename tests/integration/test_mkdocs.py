"""
End-to-end MkDocs integration test.

Spins up a real MkDocs project in a temp directory, runs a full build using
the mkdocs Python API, and asserts that the generated HTML contains treeview
output from our plugin.
"""

import textwrap
from pathlib import Path

import pytest


@pytest.fixture()
def mkdocs_project(tmp_path: Path):
    """Create a minimal MkDocs project that uses our plugin."""
    docs = tmp_path / "docs"
    docs.mkdir()

    # A page with both ASCII and symbol treeview blocks
    (docs / "index.md").write_text(
        textwrap.dedent("""\
            # Test page

            ASCII tree:

            ```treeview
            ├── src/
            │   ├── main.py
            │   └── utils.py
            ├── tests/
            │   └── test_main.py
            └── README.md
            ```

            Symbol tree:

            ```treeview
            * src/
            ** main.py
            * README.md
            ```
        """),
        encoding="utf-8",
    )

    (tmp_path / "mkdocs.yml").write_text(
        textwrap.dedent("""\
            site_name: Test
            docs_dir: docs
            plugins:
              - treeview:
                  icon_mode: embedded
        """),
        encoding="utf-8",
    )

    return tmp_path


def test_mkdocs_build_produces_treeview_html(mkdocs_project: Path):
    """Full mkdocs build: plugin processes treeview blocks and outputs HTML."""
    import mkdocs.commands.build
    import mkdocs.config

    config = mkdocs.config.load_config(
        config_file=str(mkdocs_project / "mkdocs.yml"),
        site_dir=str(mkdocs_project / "site"),
    )
    mkdocs.commands.build.build(config)

    output = (mkdocs_project / "site" / "index.html").read_text(encoding="utf-8")

    assert '<div class="treeview">' in output, "treeview div not found in MkDocs output"
    assert "src/" in output
    assert "main.py" in output
    assert "README.md" in output
    assert "assets/treeview/treeview.css" in output, "CSS not linked in HTML <head>"


def test_mkdocs_build_generates_css(mkdocs_project: Path):
    """Plugin writes treeview.css to site assets."""
    import mkdocs.commands.build
    import mkdocs.config

    config = mkdocs.config.load_config(
        config_file=str(mkdocs_project / "mkdocs.yml"),
        site_dir=str(mkdocs_project / "site"),
    )
    mkdocs.commands.build.build(config)

    css_path = mkdocs_project / "site" / "assets" / "treeview" / "treeview.css"
    assert css_path.exists(), "treeview.css not written to site assets"

    css = css_path.read_text(encoding="utf-8")
    assert ".treeview" in css
    assert ".tv-icon" in css
    # embedded mode: icons are base64-encoded data URIs
    assert "data:image/svg+xml;base64," in css


def test_mkdocs_build_files_mode(tmp_path: Path):
    """In files mode, SVG files are copied to site assets."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("```treeview\n├── main.py\n└── README.md\n```", encoding="utf-8")
    (tmp_path / "mkdocs.yml").write_text(
        textwrap.dedent("""\
            site_name: Test
            docs_dir: docs
            plugins:
              - treeview:
                  icon_mode: files
        """),
        encoding="utf-8",
    )

    import mkdocs.commands.build
    import mkdocs.config

    config = mkdocs.config.load_config(
        config_file=str(tmp_path / "mkdocs.yml"),
        site_dir=str(tmp_path / "site"),
    )
    mkdocs.commands.build.build(config)

    icons_dir = tmp_path / "site" / "assets" / "treeview" / "icons"
    assert icons_dir.exists(), "icons directory not created in files mode"
    svg_files = list(icons_dir.glob("*.svg"))
    assert len(svg_files) > 0, "no SVG files copied to icons directory"

    css = (tmp_path / "site" / "assets" / "treeview" / "treeview.css").read_text()
    # files mode: CSS must use relative 'icons/...' URLs, not absolute or data URIs
    assert "icons/" in css
    assert "data:" not in css


def test_mkdocs_icon_classes_in_html(mkdocs_project: Path):
    """Rendered HTML elements have tv-icon CSS classes set by renderer."""
    import mkdocs.commands.build
    import mkdocs.config

    config = mkdocs.config.load_config(
        config_file=str(mkdocs_project / "mkdocs.yml"),
        site_dir=str(mkdocs_project / "site"),
    )
    mkdocs.commands.build.build(config)

    output = (mkdocs_project / "site" / "index.html").read_text(encoding="utf-8")
    assert 'class="tv-icon' in output, "tv-icon CSS classes not present in output"
