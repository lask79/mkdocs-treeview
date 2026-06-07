"""
Integration tests for the Markdown extension.

These tests exercise the full pipeline: Markdown source → preprocessor
→ parse → render → HTML, using the real python-markdown machinery.
"""

import markdown

from mkdocs_treeview.extension import TreeviewExtension
from mkdocs_treeview.renderer import IconRegistry


def make_md(registry=None):
    if registry is None:
        registry = IconRegistry()
    ext = TreeviewExtension(registry=registry)
    return markdown.Markdown(extensions=[ext]), registry


# ── Basic rendering ───────────────────────────────────────────────────────────


def test_treeview_block_produces_div():
    md, _ = make_md()
    src = "```treeview\n├── src/\n└── main.py\n```"
    html = md.convert(src)
    assert '<div class="treeview">' in html


def test_treeview_block_contains_filenames():
    md, _ = make_md()
    src = "```treeview\n├── src/\n└── README.md\n```"
    html = md.convert(src)
    assert "src/" in html
    assert "README.md" in html


def test_regular_code_block_untouched():
    md, _ = make_md()
    src = "```python\nprint('hello')\n```"
    html = md.convert(src)
    assert "treeview" not in html
    assert "print" in html


def test_mixed_markdown_and_treeview():
    md, _ = make_md()
    src = "# Heading\n\nSome text.\n\n```treeview\n└── main.py\n```\n\nMore text."
    html = md.convert(src)
    assert "<h1>" in html
    assert "treeview" in html
    assert "main.py" in html
    assert "More text" in html


def test_multiple_treeview_blocks():
    md, _ = make_md()
    src = "```treeview\n└── src/\n```\n\n```treeview\n└── tests/\n```"
    html = md.convert(src)
    assert html.count('class="treeview"') == 2
    assert "src/" in html
    assert "tests/" in html


# ── Icon registry population ──────────────────────────────────────────────────


def test_registry_populated_after_convert():
    md, registry = make_md()
    src = "```treeview\n└── src/\n    └── main.py\n```"
    md.convert(src)
    css_classes = {cls for cls, _, _ in registry.items()}
    assert len(css_classes) >= 1


def test_registry_accumulates_across_blocks():
    md, registry = make_md()
    src = "```treeview\n└── main.py\n```\n\n```treeview\n└── Dockerfile\n```"
    md.convert(src)
    assert len(registry.items()) >= 1


# ── Format support ────────────────────────────────────────────────────────────


def test_symbol_format_renders():
    md, _ = make_md()
    src = "```treeview\n* src/\n** main.py\n* README.md\n```"
    html = md.convert(src)
    assert "src/" in html
    assert "main.py" in html
    assert "README.md" in html


def test_nested_html_structure():
    md, _ = make_md()
    src = "```treeview\n└── src/\n    └── main.py\n```"
    html = md.convert(src)
    # Flat tv-line spans with prefix connectors
    assert html.count('class="tv-line"') >= 2
    assert "└──" in html


# ── Error handling ────────────────────────────────────────────────────────────


def test_mixed_format_emits_error_div():
    md, _ = make_md()
    src = "```treeview\n├── src/\n* main.py\n```"
    html = md.convert(src)
    assert "treeview-error" in html


def test_empty_block_renders_empty_treeview():
    md, _ = make_md()
    src = "```treeview\n\n```"
    html = md.convert(src)
    assert "treeview" in html
