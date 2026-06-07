# Changelog

## [0.1.0] - 2026-06-07

Initial release.

### Added

- Renders ` ```treeview ` fenced code blocks as styled file trees in MkDocs, Material for MkDocs, and Zensical
- ASCII-tree format support (output of the `tree` command: `├──`, `│`, `└──`)
- Symbol-based format support (repeating `*` or `#` markers for depth)
- Material icon theme icons — automatically chosen by file extension, file name, or folder name
- Open/closed folder icon variants based on whether a folder has children
- Three asset modes: `files` (local SVGs), `embedded` (base64 in CSS), `cdn` (jsDelivr)
- Dynamic CSS generation — only icons actually used in a site are emitted (~7 KB instead of 1.3 MB)
- Dark/light mode support via separate light-variant icons for `[data-md-color-scheme="slate"]`
- MkDocs plugin (`treeview`) that auto-registers the extension and injects CSS
- Standalone Markdown extension for use without the MkDocs plugin (e.g. Zensical)
- Unit and integration test suites covering parser, renderer, CSS generator, and full demo builds
- Ruff (formatter + linter) and mypy type checking configured in `pyproject.toml`
- Pre-commit hooks for ruff, mypy, and unit tests
