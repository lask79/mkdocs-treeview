# mkdocs-treeview — Specification

## Overview

A Python package that renders ASCII file trees inside markdown documents with
material icons, compatible with MkDocs, Material for MkDocs, and Zensical.
Based on the rendering approach of
[asciidoctor-treeview](https://github.com/lask79/asciidoctor-treeview) and
using SVG icons from
[vscode-material-icon-theme](https://github.com/material-extensions/vscode-material-icon-theme).

---

## Input Syntax

Fenced code block with `treeview` as the language identifier:

````markdown
```treeview
├── src/
│   ├── main.py
│   └── utils.py
└── README.md
```
````

Two input formats are supported, auto-detected:

**ASCII-tree** (output of the Linux `tree` command):
```
├── src/
│   └── main.py
└── README.md
```

**Symbol-based** (depth by repeating marker `*` or `#`):
```
* src/
** main.py
* README.md
```

Detection logic: if the source contains `│`, `├──`, or `└──` → ascii-tree
parser; otherwise → symbol parser. Mixed formats throw an error.

---

## Architecture

One Python package (`mkdocs-treeview`) that registers two entry points:

| Entry point | Type | Responsibility |
|---|---|---|
| `treeview` | MkDocs plugin | Asset injection: copies SVGs, injects CSS into build |
| `treeview` | Python-Markdown extension | Processes ` ```treeview ` blocks → HTML |

The Markdown extension renders tree blocks to HTML. The MkDocs plugin hooks
into `on_config` to register the extension and inject `extra_css`, and
`on_post_build` to write generated CSS (and copy SVGs in `files` mode).

### Supported frameworks

| Framework | Integration mechanism | CSS delivery |
|---|---|---|
| MkDocs (any theme) | MkDocs plugin (`treeview`) | `extra_css` registered in `on_config` → `<link>` injected by MkDocs |
| Material for MkDocs | Same as MkDocs; Material processes `extra_css` identically | Same |
| Zensical | Python-Markdown extension loaded via `zensical.toml`; `extra_css` in config | `TreeviewCSSPostprocessor` writes CSS after each page render |

---

## Icon Source

Icons come from `vscode-material-icon-theme` (MIT license). Attribution and
license are included in the package README and LICENSE file.

**Dev workflow:**
- No git submodule. `scripts/build_icons.py` downloads the npm package
  `material-icon-theme@<version>` via `npm pack`, extracts
  `dist/material-icons.json` (the pre-built manifest) and `icons/*.svg`,
  generates `mkdocs_treeview/icon_map.py` (Python dicts for lookup) and
  copies all SVGs to `mkdocs_treeview/icons/`
- Only dev dependency: Node.js / npm (for `scripts/build_icons.py`)
- Generated files (`icon_map.py`, `icons/`) are committed; end users have
  zero Node.js or npm dependency

**Version updates:** change `DEFAULT_VERSION` in `scripts/build_icons.py`,
re-run it, commit, cut release.

### Icon lookup priority (per entry, dark and light variants both resolved)

1. Exact file name match (e.g. `Dockerfile`, `.gitignore`)
2. Single extension match (e.g. `.py`, `.md`)
3. Language ID match (via vscode language definitions)
4. Folder name match (for directories)
5. Generic file or folder fallback

Note: double-extension lookup (`.test.ts`) is handled by the manifest's
`fileNames` table (the npm build expands patterns into explicit entries),
so a separate file_ext2 step is not needed.

---

## HTML Output

The renderer emits flat `<span class="tv-line">` rows with ASCII prefix connectors
(matching the asciidoctor-treeview approach). Spaces in connectors are replaced with
`&nbsp;` so they do not collapse in HTML.

```html
<div class="treeview">
  <span class="tv-line">
    <span class="tv-line-prefix">├──&nbsp;</span>
    <span class="tv-line-element">
      <i class="tv-icon tv-icon-folder-src-open"></i>
      <span class="tv-item-name">src/</span>
    </span>
  </span>
  <span class="tv-line">
    <span class="tv-line-prefix">│&nbsp;&nbsp;&nbsp;├──&nbsp;</span>
    <span class="tv-line-element">
      <i class="tv-icon tv-icon-python"></i>
      <span class="tv-item-name">main.py</span>
    </span>
  </span>
  <span class="tv-line">
    <span class="tv-line-prefix">│&nbsp;&nbsp;&nbsp;└──&nbsp;</span>
    <span class="tv-line-element">
      <i class="tv-icon tv-icon-python"></i>
      <span class="tv-item-name">utils.py</span>
    </span>
  </span>
  <span class="tv-line">
    <span class="tv-line-prefix">└──&nbsp;</span>
    <span class="tv-line-element">
      <i class="tv-icon tv-icon-markdown"></i>
      <span class="tv-item-name">README.md</span>
    </span>
  </span>
</div>
```

Folders with children → open variant (`folder-src-open.svg`).
Folders without children → closed variant (`folder-src.svg`).
Unknown file type → generic file icon fallback.

---

## CSS & Dark/Light Mode

The plugin generates a single CSS file containing base rules and one rule per used icon.
Icons are `<i>` elements with `background-image` set directly (no `::before` pseudo-element):

```css
.treeview { font-family: monospace; line-height: 1; }
.tv-line { display: flex; align-items: center; }
.tv-line-element { display: contents; }
.tv-item-name { margin-left: 5px; }
.tv-icon { width: 18px; height: 18px; flex-shrink: 0; background-repeat: no-repeat; background-size: contain; }

/* dark mode (default) */
.tv-icon-python { background-image: url(assets/treeview/icons/python.svg); }

/* light mode override */
:root:not([data-md-color-scheme="slate"]) .tv-icon-python {
  background-image: url(assets/treeview/icons/python_light.svg);
}
```

Only icons actually used across the built site appear in the CSS and are copied
to the output. Unused icons are not shipped.

### Dynamic CSS generation

- **MkDocs / Material**: icons accumulate in `IconRegistry` during page
  renders; `on_post_build` writes CSS once, containing only used icons.
- **Zensical**: `TreeviewCSSPostprocessor` (Python-Markdown `Postprocessor`,
  priority 0) writes CSS after every page. Because Zensical's Rust core spawns
  a fresh Python sub-interpreter for each page render, module-level state
  (like the `IconRegistry`) is reset between pages. A JSON manifest file
  persists the accumulated icon registry across these interpreter boundaries.
  See [Zensical multi-page accumulation](#zensical-multi-page-accumulation).

---

## Zensical multi-page accumulation

### Problem

Zensical's Rust binary spawns a fresh Python sub-interpreter for each page
render. This means every call to `zensical.markdown.render.render()` starts
with a clean Python state — module-level singletons, including the
`IconRegistry`, are reset to their initial values. If the CSS were rewritten
from the current page's registry alone, each page would overwrite the CSS with
only its own icons, discarding all icons from previously rendered pages.

### Solution: filesystem manifest

`TreeviewCSSPostprocessor` uses a JSON manifest file to persist the full icon
registry across interpreter boundaries:

1. Before writing CSS, load the manifest from disk (if it exists).
2. Merge the current page's icons into the loaded manifest.
3. Save the updated manifest back to disk.
4. Regenerate the full CSS from the merged manifest.

Every write is additive — no previously seen icon is ever discarded. After the
last page is rendered, the CSS contains every icon used across the entire site.

### Manifest location

The manifest is written to `.cache/<css_stem>.manifest.json` relative to the
CWD at build time (i.e., the project root). For the default config:

```toml
css_output_path = "docs/stylesheets/treeview.css"
```

The manifest is written to:

```text
.cache/treeview.manifest.json
```

The `.cache/` directory is a build artifact. Add it to `.gitignore`:

```text
.cache/
```

The CSS file itself (`docs/stylesheets/treeview.css`) stays where `extra_css`
points. The manifest is not served — it is only read and written by the
extension during a build.

### `zensical serve` behaviour

During `zensical serve`, the manifest accumulates icons as pages are rebuilt.
Icons are never removed from the manifest — if you delete a treeview block,
its icon class remains in the CSS until you delete `.cache/` and rebuild. This
is acceptable v1 behaviour; a future version may support manifest pruning.

### Optional `manifest_path` kwarg

For non-standard setups or tests, override the manifest location explicitly:

```toml
[project.markdown_extensions."mkdocs_treeview.extension"]
css_output_path = "docs/stylesheets/treeview.css"
icon_mode = "embedded"
manifest_path = ".cache/treeview.manifest.json"   # optional, this is the default
```

---

## Asset Modes

Configured via `mkdocs.yml` or `zensical.toml`:

```yaml
plugins:
  - treeview:
      icon_mode: embedded   # or: files, cdn
```

| Mode | Behavior | Use case |
|---|---|---|
| `files` | SVGs copied to `assets/treeview/icons/`, CSS uses relative URLs | Default for MkDocs |
| `embedded` | SVGs inlined as base64 data URIs in CSS, no separate icon files | Self-contained output |
| `cdn` | CSS references jsDelivr URLs, no local files | VSCode preview, GitHub rendering |

`icon_mode: files` is the default for the MkDocs plugin. Zensical users
configure `icon_mode` via `zensical.toml` extension kwargs.

---

## Configuration Reference

### MkDocs / Material for MkDocs (`mkdocs.yml`)

```yaml
plugins:
  - treeview:
      icon_mode: files   # files | embedded | cdn
```

### Zensical (`zensical.toml`)

```toml
[project]
extra_css = ["stylesheets/treeview.css"]

[project.markdown_extensions."mkdocs_treeview.extension"]
css_output_path = "docs/stylesheets/treeview.css"
icon_mode = "embedded"
# manifest_path defaults to .cache/<css_stem>.manifest.json relative to CWD
```

`css_output_path` must be absolute or relative to the CWD at build time
(the project root where `zensical build` is run).

The manifest file (`.cache/treeview.manifest.json`) is a build artifact that
persists the icon registry across Zensical's per-page Python sub-interpreters.
Add `.cache/` to your project's `.gitignore`.

---

## Out of Scope (v1)

- Callout / annotation support (v2 candidate)
- Custom icon path overrides
- CDN URL customization
- Per-block icon mode override

---

## Testing Strategy

### Unit tests (`tests/unit/`)

| What | How |
|---|---|
| ASCII-tree parser | Feed raw tree strings, assert parsed node tree structure and depth |
| Symbol parser | Same for `*` and `#` markers, including edge cases (empty, single node, mixed → error) |
| Auto-detection | Strings with `├──` → ascii, strings with `*` → symbol, mixed → error |
| Icon lookup | Given filename/extension/folder name, assert correct SVG filename returned for dark and light |
| Open/closed folder | Node with children → open variant, leaf node → closed variant |
| HTML renderer | Given a parsed tree + icon map, assert rendered HTML structure and CSS classes |
| CSS generator | Given a set of used icons + mode, assert correct CSS output for each of the three modes |

### Integration tests (`tests/integration/`)

| What | How |
|---|---|
| Full render pipeline | Markdown with ` ```treeview ` block → run through Markdown extension → assert HTML snapshot |
| MkDocs build | Minimal `mkdocs.yml` + treeview block → `mkdocs build` → assert CSS injected, HTML correct |
| MkDocs files mode | Build with `icon_mode: files` → assert SVGs copied, CSS uses relative URLs |
| MkDocs icon classes | Assert `tv-icon-*` classes present in rendered HTML |
| Material for MkDocs build | Same as MkDocs build with `theme: material` → assert identical plugin behaviour |
| Zensical render | Markdown through `zensical.markdown.render.render()` → assert treeview HTML, icon classes, registry populated |
| Zensical multiple trees | Multiple fenced blocks on one page all render correctly |
| Plain Markdown unaffected | Non-treeview content unchanged by extension |

### Demo builds (`tests/demos/`)

Full real builds, inspectable in VSCode. Rebuilt automatically on each test run.

| Demo | Location | Framework |
|---|---|---|
| MkDocs default theme | `tests/demos/mkdocs/` | MkDocs |
| Material for MkDocs | `tests/demos/material/` | MkDocs + Material theme |
| Zensical | `tests/demos/zensical/` | Zensical |

Each demo is covered by four automated assertions: treeview HTML present,
CSS `<link>` in HTML head, CSS file is lean (< 50 KB, only used icons),
all expected `tv-icon-*` classes in the HTML.

### Visual review (`tests/visual/`)

A standalone HTML file (`tests/visual/preview.html`) that renders a reference
tree covering:
- Mixed file types (Python, TypeScript, Markdown, Dockerfile, `.gitignore`, JSON, YAML)
- Nested folders (open and closed states)
- Named folders with specific icons (`src/`, `.github/`, `docs/`)
- Unknown/generic file type

This file is checked in and updated whenever the HTML output structure changes.
It serves as a quick visual sanity check without running a full build:
open in a browser, confirm icons render correctly in both light and dark mode.

### Review checklist (before each release)

- [ ] `scripts/build_icons.py --version <X.Y.Z>` runs cleanly (requires npm)
- [ ] All unit tests pass (`uv run pytest tests/unit/`)
- [ ] All integration tests pass (`uv run pytest tests/integration/`)
- [ ] Demo builds are clean and inspectable (`tests/demos/`)
- [ ] Visual preview (`tests/visual/preview.html`) checked in browser — light and dark mode
- [ ] `pip install -e .` in a fresh virtualenv, `mkdocs serve` renders correctly (default theme)
- [ ] Same verification with Material theme
- [ ] Same verification with `zensical build` — confirm CSS written, icons lean
- [ ] All three `icon_mode` values produce correct output
- [ ] LICENSE and attribution for `vscode-material-icon-theme` present in package
- [ ] `CHANGELOG.md` updated with icon theme version and any changes
