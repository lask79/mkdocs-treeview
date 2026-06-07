"""
Generate docs/images/treeview-light.png and treeview-dark.png by screenshotting
the actual rendered demo site with Playwright.

Run from the project root:
    uv run python scripts/generate_preview_images.py
"""

import pathlib
import subprocess
import sys

DEMO_DIR = pathlib.Path("tests/demos/zensical")
SITE_DIR = DEMO_DIR / "site"
OUT_DIR = pathlib.Path("docs/images")


def build_demo() -> None:
    print("Building demo site...")
    result = subprocess.run(
        ["uv", "run", "zensical", "build", "--config-file", str(DEMO_DIR / "zensical.toml")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)


def screenshot(theme: str, out_path: pathlib.Path) -> None:
    from playwright.sync_api import sync_playwright

    html_file = (SITE_DIR / "treeview" / "index.html").resolve()
    url = f"file://{html_file}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(color_scheme=theme)
        page.goto(url, wait_until="networkidle")

        # Switch to dark palette if needed (mkdocs-material uses data-md-color-scheme on body)
        if theme == "dark":
            page.evaluate("""
                document.body.setAttribute('data-md-color-scheme', 'slate');
            """)

        # Find the treeview element and screenshot just it
        element = page.query_selector(".treeview")
        if element is None:
            # Fall back to the article content
            element = page.query_selector("article")
        if element is None:
            element = page.query_selector(".md-content")

        element.screenshot(path=str(out_path))
        print(f"Written {out_path}")
        browser.close()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not SITE_DIR.exists():
        build_demo()

    screenshot("light", OUT_DIR / "treeview-light.png")
    screenshot("dark", OUT_DIR / "treeview-dark.png")


if __name__ == "__main__":
    main()
