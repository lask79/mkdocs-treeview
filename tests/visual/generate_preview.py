#!/usr/bin/env python3
"""
Generate tests/visual/preview.html — a self-contained visual test page.

Run with:
    uv run python tests/visual/generate_preview.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sure the package is importable from source
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

import markdown  # noqa: E402

from mkdocs_treeview.css_generator import generate_css  # noqa: E402
from mkdocs_treeview.extension import TreeviewExtension  # noqa: E402
from mkdocs_treeview.renderer import IconRegistry  # noqa: E402

ICONS_DIR = repo_root / "mkdocs_treeview" / "icons"

EXAMPLES = [
    (
        "ASCII tree — mixed files and folders",
        """\
```treeview
├── docs/
│   ├── index.md
│   └── api.md
├── src/
│   ├── main.py
│   ├── parser.py
│   └── utils/
│       └── helpers.py
├── tests/
│   └── test_main.py
├── pyproject.toml
├── Dockerfile
├── .gitignore
└── README.md
```""",
    ),
    (
        "Symbol format (star)",
        """\
```treeview
* src/
** components/
*** Button.tsx
*** Input.tsx
** hooks/
*** useAuth.ts
** index.ts
* public/
** favicon.ico
* package.json
* tsconfig.json
```""",
    ),
    (
        "Symbol format (hash)",
        """\
```treeview
# backend/
## api/
### routes.py
### models.py
## services/
### auth.py
### db.py
# frontend/
## pages/
### index.html
## styles/
### main.css
# docker-compose.yml
```""",
    ),
    (
        "Flat file list",
        """\
```treeview
├── main.py
├── requirements.txt
├── Makefile
└── .env
```""",
    ),
    (
        "Deep nesting",
        """\
```treeview
└── project/
    └── src/
        └── core/
            └── utils/
                └── helpers/
                    └── string.py
```""",
    ),
]

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>mkdocs-treeview visual preview</title>
  <style>
    /* MkDocs Material dark/light simulation */
    :root {{ --md-default-bg-color: #fff; color-scheme: light; }}
    [data-md-color-scheme="slate"] {{ --md-default-bg-color: #1e1e2e; color-scheme: dark; }}

    body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; background: var(--md-default-bg-color); transition: background 0.2s; }}
    body {{ color: #1a1a1a; }}
    [data-md-color-scheme="slate"] body {{ color: #cdd6f4; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 0.25rem; }}
    h2 {{ font-size: 1rem; color: #555; margin-top: 2rem; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.3rem; }}
    [data-md-color-scheme="slate"] h2 {{ color: #a6adc8; border-color: #313244; }}
    .controls {{ position: sticky; top: 0; background: inherit; padding: 0.5rem 0; margin-bottom: 1rem; display: flex; gap: 0.5rem; align-items: center; }}
    button {{ padding: 0.3rem 0.8rem; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; background: #f5f5f5; }}
    [data-md-color-scheme="slate"] button {{ background: #313244; border-color: #45475a; color: #cdd6f4; }}
    .example {{ margin-bottom: 2rem; }}
    pre.source {{ background: #f5f5f5; padding: 0.8rem; border-radius: 4px; font-size: 0.8rem; overflow-x: auto; }}
    [data-md-color-scheme="slate"] pre.source {{ background: #181825; }}
{icon_css}
  </style>
</head>
<body>
  <div class="controls">
    <strong>mkdocs-treeview preview</strong>
    <button onclick="toggleTheme()">Toggle dark/light</button>
  </div>
{examples_html}
  <script>
    function toggleTheme() {{
      const html = document.documentElement;
      html.dataset.mdColorScheme = html.dataset.mdColorScheme === "slate" ? "" : "slate";
    }}
  </script>
</body>
</html>
"""


def main():
    registry = IconRegistry()
    ext = TreeviewExtension(registry=registry)
    md = markdown.Markdown(extensions=[ext])

    example_parts = []
    for title, source in EXAMPLES:
        rendered = md.convert(source)
        md.reset()
        example_parts.append(
            f'  <div class="example">\n'
            f"    <h2>{title}</h2>\n"
            f"    {rendered}\n"
            f"    <details><summary>source</summary>"
            f'<pre class="source">{source.replace("<", "&lt;")}</pre></details>\n'
            f"  </div>"
        )

    icon_css = generate_css(
        registry.items(),
        icon_mode="embedded",
        icons_dir=ICONS_DIR,
    )
    # Indent into <style>
    icon_css_indented = "\n".join("    " + line for line in icon_css.splitlines())

    html = HTML_TEMPLATE.format(
        icon_css=icon_css_indented,
        examples_html="\n".join(example_parts),
    )

    out = Path(__file__).parent / "preview.html"
    out.write_text(html, encoding="utf-8")
    print(f"Written: {out}")
    print(f"Icons registered: {len(registry.items())}")


if __name__ == "__main__":
    main()
