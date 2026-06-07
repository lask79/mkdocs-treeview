"""
End-to-end Zensical integration test.

Calls Zensical's Python Markdown pipeline directly (zensical.markdown.render.render)
with a real config parsed by parse_mkdocs_config(), injects our TreeviewExtension,
and asserts that the resulting HTML contains treeview output.

Zensical stores config in a global _CONFIG dict (zensical.config._CONFIG).
parse_mkdocs_config() populates it; get_config() returns it.
render() then builds a fresh Markdown() instance from that config on every call.
"""

import textwrap
from pathlib import Path

import pytest


@pytest.fixture()
def zensical_config(tmp_path: Path):
    """Initialise a minimal Zensical/MkDocs config for the render pipeline."""
    import zensical.config as zc

    from mkdocs_treeview.extension import TreeviewExtension
    from mkdocs_treeview.renderer import IconRegistry

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# placeholder", encoding="utf-8")
    (tmp_path / "mkdocs.yml").write_text("site_name: Test\n", encoding="utf-8")

    config = zc.parse_mkdocs_config(str(tmp_path / "mkdocs.yml"))

    registry = IconRegistry()
    ext = TreeviewExtension(registry=registry)
    # Guard against double-registration (mirrors plugin.on_config logic)
    config["markdown_extensions"] = [
        e for e in config["markdown_extensions"] if not isinstance(e, TreeviewExtension)
    ]
    config["markdown_extensions"].append(ext)

    return config, registry


def test_zensical_renders_ascii_treeview(zensical_config):
    """ASCII tree in a treeview fence is converted to treeview HTML by Zensical."""
    from zensical.markdown.render import render

    content = textwrap.dedent("""\
        # Project layout

        ```treeview
        ├── src/
        │   └── main.py
        └── README.md
        ```
    """)

    result = render(content, "index.md", "/")
    html = result["content"]

    assert '<div class="treeview">' in html, "treeview div not found"
    assert "src/" in html
    assert "main.py" in html
    assert "README.md" in html


def test_zensical_renders_symbol_treeview(zensical_config):
    """Symbol-style tree (*, #) in a treeview fence is also rendered."""
    from zensical.markdown.render import render

    content = textwrap.dedent("""\
        ```treeview
        * src/
        ** utils.py
        * tests/
        ** test_main.py
        ```
    """)

    result = render(content, "index.md", "/")
    html = result["content"]

    assert '<div class="treeview">' in html
    assert "src/" in html
    assert "utils.py" in html
    assert "tests/" in html
    assert "test_main.py" in html


def test_zensical_icon_css_classes_present(zensical_config):
    """Rendered HTML contains tv-icon CSS classes for file-type icons."""
    from zensical.markdown.render import render

    content = "```treeview\n└── main.py\n```"
    result = render(content, "index.md", "/")
    html = result["content"]

    assert 'class="tv-icon' in html, "tv-icon CSS class not present"


def test_zensical_used_icons_registered(zensical_config):
    """After render(), the IconRegistry contains entries for the icons used."""
    from zensical.markdown.render import render

    _, registry = zensical_config
    registry.clear()

    content = "```treeview\n└── src/\n    └── main.py\n```"
    render(content, "index.md", "/")

    items = registry.items()
    assert len(items) > 0, "no icons registered after render"
    css_classes = {cls for cls, _, _ in items}
    assert any("folder" in cls for cls in css_classes)


def test_zensical_multiple_trees_in_one_page(zensical_config):
    """Multiple treeview fences on a single page all render correctly."""
    from zensical.markdown.render import render

    content = textwrap.dedent("""\
        First tree:

        ```treeview
        └── alpha.py
        ```

        Second tree:

        ```treeview
        └── beta.py
        ```
    """)

    result = render(content, "index.md", "/")
    html = result["content"]

    count = html.count('<div class="treeview">')
    assert count == 2, f"expected 2 treeview divs, got {count}"
    assert "alpha.py" in html
    assert "beta.py" in html


def test_zensical_plain_markdown_unaffected(zensical_config):
    """Regular Markdown outside treeview fences is unaffected by the extension."""
    from zensical.markdown.render import render

    content = textwrap.dedent("""\
        # Hello

        A paragraph with **bold** and _italic_.

        - item one
        - item two
    """)

    result = render(content, "index.md", "/")
    html = result["content"]

    assert "<h1" in html or "Hello" in html
    assert "<strong>" in html
    assert "<em>" in html
    assert "<li>" in html
    assert "treeview" not in html
