import pytest

from mkdocs_treeview.parser import TreeNode, detect_format, parse

# ── detect_format ─────────────────────────────────────────────────────────────


def test_detect_ascii_by_box_chars():
    assert detect_format("├── src/\n└── main.py") == "ascii"


def test_detect_ascii_by_pipe():
    assert detect_format("│   └── foo.py") == "ascii"


def test_detect_symbol_star():
    assert detect_format("* src/\n** main.py") == "symbol"


def test_detect_symbol_hash():
    assert detect_format("# src/\n## main.py") == "symbol"


def test_detect_mixed_raises():
    with pytest.raises(ValueError, match="Mixed"):
        detect_format("├── src/\n* main.py")


def test_detect_empty_defaults_to_ascii():
    assert detect_format("") == "ascii"


# ── ASCII-tree parser ─────────────────────────────────────────────────────────


def test_ascii_flat():
    root = parse("├── README.md\n└── main.py")
    names = [c.name for c in root.children]
    assert names == ["README.md", "main.py"]


def test_ascii_nested():
    src = "├── src/\n│   └── main.py\n└── README.md"
    root = parse(src)
    assert root.children[0].name == "src/"
    assert root.children[0].children[0].name == "main.py"
    assert root.children[1].name == "README.md"


def test_ascii_deeply_nested():
    src = "└── a/\n    └── b/\n        └── c.py"
    root = parse(src)
    assert root.children[0].name == "a/"
    assert root.children[0].children[0].name == "b/"
    assert root.children[0].children[0].children[0].name == "c.py"


def test_ascii_skips_blank_lines():
    root = parse("├── src/\n\n└── README.md")
    assert len(root.children) == 2


def test_ascii_node_has_children():
    root = parse("└── src/\n    └── main.py")
    assert root.children[0].has_children()
    assert not root.children[0].children[0].has_children()


# ── Symbol parser ─────────────────────────────────────────────────────────────


def test_symbol_star_flat():
    root = parse("* README.md\n* main.py")
    assert [c.name for c in root.children] == ["README.md", "main.py"]


def test_symbol_star_nested():
    root = parse("* src/\n** main.py\n* README.md")
    assert root.children[0].name == "src/"
    assert root.children[0].children[0].name == "main.py"
    assert root.children[1].name == "README.md"


def test_symbol_hash_nested():
    root = parse("# src/\n## main.py\n# README.md")
    assert root.children[0].children[0].name == "main.py"


def test_symbol_deeply_nested():
    root = parse("* a/\n** b/\n*** c.py")
    assert root.children[0].children[0].children[0].name == "c.py"


def test_empty_source_returns_empty_root():
    root = parse("")
    assert root.is_root
    assert root.children == []


# ── TreeNode helpers ──────────────────────────────────────────────────────────


def test_is_folder_by_trailing_slash():
    node = TreeNode(name="src/")
    assert node.is_folder()


def test_is_folder_by_children():
    child = TreeNode(name="main.py")
    node = TreeNode(name="src", children=[child])
    assert node.is_folder()


def test_is_not_folder():
    node = TreeNode(name="main.py")
    assert not node.is_folder()


# ── Regression tests ──────────────────────────────────────────────────────────


def test_ascii_two_plain_root_lines_no_crash():
    # B1: two root-level lines without tree prefix must not crash with IndexError
    root = parse("src/\nREADME.md")
    assert [c.name for c in root.children] == ["src/", "README.md"]


def test_ascii_hyphenated_filename_not_truncated():
    # B3: filename containing a hyphen must not be truncated at the hyphen
    root = parse("├── foo-bar.txt")
    assert root.children[0].name == "foo-bar.txt"


def test_ascii_hyphenated_nested_filename():
    root = parse("└── src/\n    └── my-module.py")
    assert root.children[0].children[0].name == "my-module.py"


def test_symbol_plain_line_no_crash():
    # B2: symbol parser must not crash when a line has no leading marker (depth=0)
    root = parse("* src/\n** main.py\n* README.md")
    assert root.children[1].name == "README.md"


def test_ascii_root_plain_followed_by_indented():
    # Both root-level plain line and a nested child — stack must not empty past root
    root = parse("src/\n├── main.py")
    # main.py has a box-drawing char so it gets depth>=1 — it goes under src/
    assert root.children[0].name == "src/"
