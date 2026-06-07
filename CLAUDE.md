# Project overview

A Python-Markdown extension and MkDocs plugin that renders ASCII file trees with
[Material icon theme](https://github.com/material-extensions/vscode-material-icon-theme) icons.
Inspired by [@https://github.com/lask79/asciidoctor-treeview].

Supports MkDocs, Material for MkDocs, and Zensical.

## Goal

See @docs/spec.md

## Architecture

```
mkdocs_treeview/
  parser.py        — parses ASCII-tree and symbol-based (* / #) input into TreeNode tree
  renderer.py      — walks TreeNode tree, emits HTML, collects (name, dark_svg, light_svg) into IconRegistry
  icon_finder.py   — maps filenames/extensions/folder names to icon slugs using icon_map.py
  icon_map.py      — generated file (do not edit); maps names → icon slugs (FILE_NAMES, FILE_EXT1, etc.)
  css_generator.py — generates lean CSS from IconRegistry; supports files / embedded / cdn modes
  extension.py     — Python-Markdown extension: TreeviewPreprocessor + TreeviewCSSPostprocessor
  plugin.py        — MkDocs plugin: registers extension, injects extra_css, copies icons on post_build
  icons/           — SVG icon files (dark + light variants)
```

## Key conventions

- The package ships only `mkdocs_treeview/**` (see `[tool.hatch.build.targets.wheel]` in pyproject.toml)
- `icon_map.py` is excluded from mypy and should never be edited manually — regenerate with `scripts/build_icons.py`
- CSS has three modes: `files` (local SVGs), `embedded` (base64), `cdn` (jsDelivr)
- Dark mode: icons have a `-light` variant used under `[data-md-color-scheme="slate"]`
- HTML output uses flat `<span class="tv-line">` rows (not nested ul/li), matching asciidoctor-treeview

## Dev workflow

```bash
uv sync                          # install all deps including dev
uv run pre-commit install        # set up git hooks (run once after clone)

uv run pytest tests/unit/        # fast unit tests
uv run pytest tests/integration/ # builds real demo sites (slower)

uv run ruff format mkdocs_treeview/ tests/ scripts/
uv run ruff check mkdocs_treeview/ tests/ scripts/
uv run mypy mkdocs_treeview/

uv run python scripts/generate_preview_images.py  # regenerate docs/images/*.png via Playwright
uv run python scripts/build_icons.py --version 5.x.y  # update icon bundle (needs npm)

uv build                         # produces dist/*.whl and dist/*.tar.gz
UV_PUBLISH_TOKEN=pypi-... uv publish
```

## Test structure

```
tests/
  unit/        — parser, renderer, css_generator, icon_finder (no filesystem, fast)
  integration/ — test_extension.py, test_mkdocs.py, test_zensical.py, test_build_demos.py
  demos/       — built demo sites (gitignored output, written by integration tests)
  visual/      — generate_preview.py (standalone HTML preview, not part of test suite)
```

## Tooling

- **Build**: hatchling via `uv build`
- **Linter/formatter**: ruff (`E`, `F`, `I`, `UP`; line length 100)
- **Type checker**: mypy (`disallow_untyped_defs`, `warn_return_any`; skips icon_map.py)
- **Pre-commit hooks**: ruff format → ruff check → mypy → pytest unit (runs on every commit)
- **Screenshots**: Playwright/Chromium used by `scripts/generate_preview_images.py`

## Demo sites

Each integration test builds a real site under `tests/demos/`:

| Dir | Tool | Config |
|---|---|---|
| `mkdocs/` | MkDocs default | `tests/demos/mkdocs/mkdocs.yml` |
| `material/` | Material for MkDocs | `tests/demos/material/mkdocs.yml` |
| `zensical/` | Zensical | `tests/demos/zensical/zensical.toml` |

The zensical demo is also used by `scripts/generate_preview_images.py` to produce
`docs/images/treeview-light.png` and `docs/images/treeview-dark.png`.
