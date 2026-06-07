"""
Icon lookup for file and folder names.

Priority order for files:
1. Exact file name match, case-insensitive (e.g. Dockerfile, .gitignore)
2. Single extension match, case-insensitive (e.g. .py -> python)
3. Language ID match
4. Fallback to generic file icon

For folders:
1. Exact folder name match
2. Fallback to generic folder icon

Returns (dark_svg, light_svg) tuples. If no light variant exists, dark is used for both.
"""

from __future__ import annotations

try:
    from mkdocs_treeview.icon_map import (
        FILE_EXT1,
        FILE_EXT1_LIGHT,
        FILE_NAMES,
        FILE_NAMES_LIGHT,
        FOLDER_NAMES,
        FOLDER_NAMES_LIGHT,
        LANGUAGE_IDS,
    )
except ImportError:
    # icon_map.py not yet generated; return empty maps so tests can stub them
    FILE_NAMES = FILE_NAMES_LIGHT = {}
    FILE_EXT1 = FILE_EXT1_LIGHT = {}
    FOLDER_NAMES = FOLDER_NAMES_LIGHT = {}
    LANGUAGE_IDS = {}

DEFAULT_FILE = "file.svg"
DEFAULT_FOLDER = "folder.svg"


def get_icon_for_file(name: str) -> tuple[str, str]:
    """Return (dark_svg, light_svg) for a file name."""
    name_lower = name.lower()

    # 1. Exact file name, case-insensitive (Dockerfile, .gitignore, tsconfig.json)
    if name_lower in FILE_NAMES:
        dark = FILE_NAMES[name_lower]
        light = FILE_NAMES_LIGHT.get(name_lower, dark)
        return dark, light

    # 2. Single extension, case-insensitive
    if "." in name:
        ext = name.rsplit(".", 1)[-1].lower()
        if ext in FILE_EXT1:
            dark = FILE_EXT1[ext]
            light = FILE_EXT1_LIGHT.get(ext, dark)
            return dark, light

        # 3. Language ID
        if ext in LANGUAGE_IDS:
            dark = LANGUAGE_IDS[ext]
            return dark, dark

    return DEFAULT_FILE, DEFAULT_FILE


def get_icon_for_folder(name: str) -> tuple[str, str]:
    """Return (dark_svg, light_svg) for a folder name (without trailing slash)."""
    name = name.rstrip("/")
    if name in FOLDER_NAMES:
        dark = FOLDER_NAMES[name]
        light = FOLDER_NAMES_LIGHT.get(name, dark)
        return dark, light
    return DEFAULT_FOLDER, DEFAULT_FOLDER


def get_icon_for_open_folder(name: str) -> tuple[str, str]:
    """Return open-variant (dark_svg, light_svg) for a folder that has children.

    The vscode-material-icon-theme raw icons/ directory does not include
    pre-built -open variants. We derive the open icon name from the closed
    one and fall back to the closed icon if the open variant is not available.
    The CSS generator skips copying icons that don't exist on disk.
    """
    dark, light = get_icon_for_folder(name)
    dark_open = dark.replace(".svg", "-open.svg")
    light_open = light.replace(".svg", "-open.svg")
    return dark_open, light_open
