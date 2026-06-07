from unittest.mock import patch

import pytest

from mkdocs_treeview import icon_finder

MOCK_FILE_NAMES = {
    "dockerfile": "docker.svg",
    ".gitignore": "git.svg",
    "tsconfig.json": "tsconfig.svg",
}
MOCK_FILE_NAMES_LIGHT = {
    "dockerfile": "docker_light.svg",
}
MOCK_FILE_EXT1 = {
    "py": "python.svg",
    "ts": "typescript.svg",
    "md": "markdown.svg",
}
MOCK_FILE_EXT1_LIGHT = {
    "ts": "typescript_light.svg",
}
MOCK_FOLDER_NAMES = {
    "src": "folder-src.svg",
    ".github": "folder-github.svg",
}
MOCK_FOLDER_NAMES_LIGHT = {}
MOCK_LANGUAGE_IDS = {
    "python": "python.svg",
}


@pytest.fixture(autouse=True)
def patch_maps():
    with patch.multiple(
        "mkdocs_treeview.icon_finder",
        FILE_NAMES=MOCK_FILE_NAMES,
        FILE_NAMES_LIGHT=MOCK_FILE_NAMES_LIGHT,
        FILE_EXT1=MOCK_FILE_EXT1,
        FILE_EXT1_LIGHT=MOCK_FILE_EXT1_LIGHT,
        FOLDER_NAMES=MOCK_FOLDER_NAMES,
        FOLDER_NAMES_LIGHT=MOCK_FOLDER_NAMES_LIGHT,
        LANGUAGE_IDS=MOCK_LANGUAGE_IDS,
    ):
        yield


# ── get_icon_for_file ─────────────────────────────────────────────────────────


def test_file_exact_name_match():
    dark, light = icon_finder.get_icon_for_file("Dockerfile")
    assert dark == "docker.svg"
    assert light == "docker_light.svg"


def test_file_exact_name_no_light_falls_back_to_dark():
    dark, light = icon_finder.get_icon_for_file(".gitignore")
    assert dark == light == "git.svg"


def test_file_compound_name_match():
    dark, light = icon_finder.get_icon_for_file("tsconfig.json")
    assert dark == "tsconfig.svg"


def test_file_single_extension():
    dark, light = icon_finder.get_icon_for_file("script.py")
    assert dark == "python.svg"
    assert light == "python.svg"


def test_file_extension_with_light_variant():
    dark, light = icon_finder.get_icon_for_file("app.ts")
    assert dark == "typescript.svg"
    assert light == "typescript_light.svg"


def test_file_unknown_extension_returns_fallback():
    dark, light = icon_finder.get_icon_for_file("binary.xyz")
    assert dark == icon_finder.DEFAULT_FILE
    assert light == icon_finder.DEFAULT_FILE


def test_file_no_extension_returns_fallback():
    dark, light = icon_finder.get_icon_for_file("Makefile_no_ext_no_match")
    assert dark == icon_finder.DEFAULT_FILE


# ── get_icon_for_folder ───────────────────────────────────────────────────────


def test_folder_named_match():
    dark, light = icon_finder.get_icon_for_folder("src")
    assert dark == "folder-src.svg"


def test_folder_trailing_slash_stripped():
    dark, light = icon_finder.get_icon_for_folder("src/")
    assert dark == "folder-src.svg"


def test_folder_unknown_returns_default():
    dark, light = icon_finder.get_icon_for_folder("unknown_folder")
    assert dark == icon_finder.DEFAULT_FOLDER


# ── get_icon_for_open_folder ──────────────────────────────────────────────────


def test_open_folder_appends_open_suffix():
    dark, light = icon_finder.get_icon_for_open_folder("src")
    assert dark == "folder-src-open.svg"


def test_open_folder_default_uses_open_suffix():
    dark, light = icon_finder.get_icon_for_open_folder("unknown_folder")
    assert dark == "folder-open.svg"


# ── Regression tests ──────────────────────────────────────────────────────────


def test_file_case_insensitive_exact_match():
    # B5: 'Dockerfile' must match even though FILE_NAMES key is lowercase 'dockerfile'
    dark, light = icon_finder.get_icon_for_file("Dockerfile")
    assert dark == "docker.svg"
    assert light == "docker_light.svg"


def test_file_makefile_uppercase_matches():
    # Makefile is another common capitalised filename — FILE_NAMES key is lowercase
    # Our mock doesn't have 'makefile' but we verify the lookup is lowercased
    dark, _ = icon_finder.get_icon_for_file("DOCKERFILE")
    assert dark == "docker.svg"


def test_file_extension_uppercase():
    # Extension case: 'script.PY' must match 'py' in FILE_EXT1
    dark, _ = icon_finder.get_icon_for_file("script.PY")
    assert dark == "python.svg"
