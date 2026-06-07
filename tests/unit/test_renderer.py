from unittest.mock import patch

import pytest

from mkdocs_treeview.parser import parse
from mkdocs_treeview.renderer import IconRegistry, _svg_to_class, render


@pytest.fixture(autouse=True)
def patch_icon_finder():
    def mock_file(name):
        return ("file.svg", "file.svg")

    def mock_folder(name):
        return ("folder.svg", "folder.svg")

    def mock_open_folder(name):
        return ("folder-open.svg", "folder-open.svg")

    with patch.multiple(
        "mkdocs_treeview.renderer.icon_finder",
        get_icon_for_file=mock_file,
        get_icon_for_folder=mock_folder,
        get_icon_for_open_folder=mock_open_folder,
    ):
        yield


def test_svg_to_class_simple():
    assert _svg_to_class("python.svg") == "tv-icon-python"


def test_svg_to_class_with_light():
    assert _svg_to_class("python_light.svg") == "tv-icon-python"


def test_svg_to_class_hyphenated():
    assert _svg_to_class("folder-src.svg") == "tv-icon-folder-src"


def test_render_flat_tree():
    root = parse("├── README.md\n└── main.py")
    registry = IconRegistry()
    html = render(root, registry)
    assert "treeview" in html
    assert "README.md" in html
    assert "main.py" in html


def test_render_nested_tree():
    root = parse("└── src/\n    └── main.py")
    registry = IconRegistry()
    html = render(root, registry)
    assert "tv-line" in html
    assert "src/" in html
    assert "main.py" in html
    # child indented with connector prefix
    assert "└──" in html


def test_render_registers_used_icons():
    root = parse("└── src/\n    └── main.py")
    registry = IconRegistry()
    render(root, registry)
    items = registry.items()
    assert len(items) >= 1
    # Each item is (css_class, dark_svg, light_svg)
    css_classes = {cls for cls, _, _ in items}
    assert any("folder" in cls for cls in css_classes)
    assert any("file" in cls for cls in css_classes)


def test_render_empty_tree():
    registry = IconRegistry()
    from mkdocs_treeview.parser import TreeNode

    html = render(TreeNode(is_root=True), registry)
    assert "treeview" in html
    assert registry.items() == []


def test_icon_registry_deduplicates():
    registry = IconRegistry()
    registry.add("tv-icon-python", "python.svg", "python.svg")
    registry.add("tv-icon-python", "python.svg", "python.svg")
    assert len(registry.items()) == 1


def test_icon_registry_clear():
    registry = IconRegistry()
    registry.add("tv-icon-python", "python.svg", "python.svg")
    registry.clear()
    assert registry.items() == []


# ── Regression tests ──────────────────────────────────────────────────────────


def test_render_escapes_html_in_name():
    # I1: node names with HTML special chars must be escaped, not injected
    from mkdocs_treeview.parser import TreeNode

    root = TreeNode(is_root=True)
    root.children = [TreeNode(name="<script>alert(1)</script>")]
    registry = IconRegistry()
    html = render(root, registry)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_escapes_ampersand_in_name():
    from mkdocs_treeview.parser import TreeNode

    root = TreeNode(is_root=True)
    root.children = [TreeNode(name="cats & dogs.md")]
    registry = IconRegistry()
    html = render(root, registry)
    assert "cats & dogs" not in html
    assert "cats &amp; dogs" in html
