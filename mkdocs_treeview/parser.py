"""
Parsers for treeview blocks.

Supports two input formats, auto-detected:
- ASCII-tree: uses box-drawing characters (│, ├──, └──) from the `tree` command
- Symbol-based: uses repeating markers (* or #) for depth

In both formats an entry may end with an inline comment: whitespace, ``#`` and
the comment text (``src/  # sources``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Whitespace before the "#" keeps names such as "C#" or "#notes" intact.
_COMMENT = re.compile(r"\s+#(?=\s|$)")


@dataclass
class TreeNode:
    name: str = ""
    children: list[TreeNode] = field(default_factory=list)
    is_root: bool = False
    comment: str = ""

    def has_children(self) -> bool:
        return len(self.children) > 0

    def is_folder(self) -> bool:
        return self.name.endswith("/") or self.has_children()


_ASCII_PATTERNS = ("│", "├──", "└──", "├", "└")


def detect_format(source: str) -> str:
    """Return 'ascii' or 'symbol'. Raises ValueError on mixed input."""
    lines = source.strip().splitlines()
    has_ascii = False
    has_symbol = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(p in line for p in _ASCII_PATTERNS):
            if has_symbol:
                raise ValueError("Mixed ASCII tree and symbol markers detected.")
            has_ascii = True
        elif stripped.startswith("*") or stripped.startswith("#"):
            if has_ascii:
                raise ValueError("Mixed ASCII tree and symbol markers detected.")
            has_symbol = True

    if has_ascii or not has_symbol:
        return "ascii"
    return "symbol"


def parse(source: str) -> TreeNode:
    """Parse a treeview block and return the root TreeNode."""
    fmt = detect_format(source)
    if fmt == "ascii":
        return _parse_ascii(source)
    return _parse_symbol(source)


def _split_comment(entry: str) -> tuple[str, str]:
    """Split ``name  # comment`` into the name and the comment text."""
    match = _COMMENT.search(entry)
    if match is None:
        return entry, ""
    return entry[: match.start()].strip(), entry[match.end() :].strip()


def _parse_ascii(source: str) -> TreeNode:
    root = TreeNode(name="", is_root=True)
    stack: list[TreeNode] = [root]
    lines = source.strip().splitlines()

    for line in lines:
        if not line.strip():
            continue

        # Depth is determined by position of last box-drawing dash only.
        # ASCII hyphen is intentionally excluded to avoid truncating hyphenated names.
        last_dash = line.rfind("─")
        if last_dash == -1:
            depth = 0
            name = line.strip()
        else:
            depth = max(1, (last_dash + 1 + 3) // 4)
            name = line[last_dash + 1 :].strip()

        name, comment = _split_comment(name)
        if not name:
            continue

        node = TreeNode(name=name, comment=comment)

        # Guard against emptying the stack: depth-0 items attach to root (index 0).
        while len(stack) > max(depth, 1):
            stack.pop()

        stack[-1].children.append(node)
        stack.append(node)

    return root


def _parse_symbol(source: str) -> TreeNode:
    lines = source.strip().splitlines()
    if not lines:
        raise ValueError("Source is empty")

    # Detect marker from first non-empty line
    marker = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("*"):
            marker = "*"
            break
        elif stripped.startswith("#"):
            marker = "#"
            break

    if marker is None:
        marker = "*"

    root = TreeNode(name="", is_root=True)
    stack: list[TreeNode] = [root]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        depth = 0
        while depth < len(stripped) and stripped[depth] == marker:
            depth += 1

        name = stripped[depth:].strip()
        name, comment = _split_comment(name)
        if not name:
            continue

        node = TreeNode(name=name, comment=comment)

        while len(stack) > max(depth, 1):
            stack.pop()

        stack[-1].children.append(node)
        stack.append(node)

    return root
