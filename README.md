# Rust Atlas — complete interactive HTML Rust Book

**The whole supplied `rust-book.md` is included in this delivery, not fetched when the website loads.** Two ready-to-open HTML deliverables are included: **`index.html` (also named `rust-atlas-complete.html`)** for the interactive learning studio, and **`rust-book-complete-static.html`** for the entire book as literal HTML markup (readable with JavaScript disabled). The interactive one is a standalone HTML document containing the original book text and code, styles, JavaScript, full-text search index, and all interactive learning tools. Open it in a normal web browser by double-clicking. No Python, Node, database, or web server is required for that standalone version.

The supplied book identifies **Rust 1.97.0 / Rust 2024 Edition**. The original 2.24 MB Markdown is preserved, unmodified, at `source/rust-book.original.md`.

> **Content status:** 111 source pages/sections, 628 headings, 957 code/terminal blocks, 433 figure elements, 13 tables and all the accompanying paragraphs were incorporated. The verifier checked 15,609/15,609 element fingerprints, with zero missing elements or automated integrity errors. **However, the Markdown only contains links to 28 original images, not their image bytes.** The HTML links those image URLs to the official Rust documentation and displays meaningful fallbacks if unavailable. Those 28 media files remain unverified and are not bundled offline, so the overall release is **not certified 100% complete**. See `docs/content-coverage-matrix.md` and `docs/testing-report.md`.

## Open the full site

**Option 1 — Single HTML file:** Open `index.html` or `rust-atlas-complete.html` directly in Chrome, Firefox, Edge or Safari. The complete supplied book and search data are already inside it. An internet connection is needed only for the 28 external illustrations and outbound reference links. The original prose, code and local learning features don't need a server.

**Option 2 — Pure HTML book:** Open `rust-book-complete-static.html`. The original book text is present as real `<h1>`, `<p>`, `<pre>`, `<table>` and `<figure>` tags rather than loaded from a JSON fragment, and it remains readable with JavaScript disabled. Native browser search (`Ctrl+F` / `Cmd+F`) searches the document.

**Option 3 — Multi-file static deployment:** Open a terminal in the project directory and run:

```bash
python3 -m http.server 8000 --directory dist
```

Then visit `http://localhost:8000`. The `dist/` directory contains the complete converted book split into JSON pages for efficient on-demand loading, plus frontend HTML/CSS/JS and the search index. This is suitable for ordinary static hosting with hash routes.

## Included functionality

- Complete uploaded Rust Book content with section navigation, anchors, copyable Rust code, paragraphs, tables, internal links and appendices A–G.
- 4,938 full-text search records with deep links into relevant source sections.
- Ten interactive learning models: ownership, borrowing, memory and slices, lifetimes, enums, iterators, traits, error handling, modules/Cargo, and concurrency.
- Sixteen supplementary practice questions/tasks with explanation, hints, deterministic quiz evaluation, and self-reviewed coding prompts.
- Reading progress, bookmarks, per-section notes, reading position, progress export and reset. Local browser storage is used when permitted by the browser.
- Responsive layouts checked at 1440, 800 and 390 pixels.
- Original source traceability, element-level checks and explicit unresolved-image reporting.

**Execution honesty:** The site is a Rust learning environment, *not* a working Rust compiler. The visualizations simulate carefully described concepts; user-supplied Rust code is not compiled or run by the site, and coding self-reviews are never recorded as compiler-verified.

## Source transformation and repeatable build

The unmodified book is in `source/rust-book.original.md`. The importer works with HTML, so `tools/prepare_markdown.py` converts the uploaded Markdown to a pinned, canonical HTML snapshot with Pandoc. It normalizes source-wrapped heading anchors, makes code-listing identifiers unique, and repairs one missing original footnote return anchor in **derived HTML only**; no prose or code is rewritten. Original text is retained.

Prerequisites to rebuild: Python 3.10+, `pandoc` 3.x, and packages in `requirements.txt`.

```bash
python3 -m pip install -r requirements.txt
python3 tools/prepare_markdown.py
python3 tools/book_pipeline.py import --source-file build/rust-book.pandoc.html --no-assets
python3 tools/export_standalone.py
python3 tools/export_static_book.py
```

**Import exit code:** The importer intentionally exits with a nonzero review status if the 28 images cannot be locally verified; it nonetheless writes the complete book text and an accurate coverage report. **Do not ignore a nonzero exit code without consulting `docs/coverage-summary.json`, `docs/content-coverage-matrix.md` and `docs/testing-report.md`.** For this supplied Markdown, content integrity is 15,609/15,609 with 28 external illustration references requiring review.

To validate the results:

```bash
python3 -m unittest discover -s tests -v
python3 tests/browser_fullbook.py
```

The browser test uses system Chromium through Playwright, if installed. In this execution environment, direct file/URL navigation was policy-blocked; the 27 full-book interaction and viewport checks instead loaded the exact standalone HTML directly into Chromium's document for a runtime/layout smoke test. Browser storage and production navigation require verification in an unrestricted browser.

## Project map

```text
index.html                         Standalone full HTML entry point
rust-atlas-complete.html          Identical interactive standalone HTML
rust-book-complete-static.html    Original full-book literal HTML; no JS required
src/                              Maintained application frontend
source/rust-book.original.md      Immutable user-supplied Markdown
source/print.snapshot.html        Derived HTML used for reproducible verification
build/                            Derived intermediate HTML, development evidence
  rust-book.pandoc.html
  rust-book.normalized.md
dist/                             Multi-file static website with full book pages
  index.html
  app.js, concepts.js, practice.js, styles.css, favicon.svg
  book-manifest.json              Full per-element provenance
  content/*.json                  All 111 source book pages
  data/search-index.json          All 4,938 source search entries
  data/coverage-summary.json
scripts: tools/prepare_markdown.py, tools/book_pipeline.py,
         tools/export_standalone.py, tools/export_static_book.py
tests/                            Unit and Chromium interaction/layout tests
docs/                             Source audit, inventory, coverage, QA, licenses
```

## Attribution

*The Rust Programming Language* is credited to Steve Klabnik, Carol Nichols, Chris Krycho and Rust Community contributors, as in the supplied title page. Source and license information: <https://github.com/rust-lang/book>. Rust Atlas is independently authored as an educational companion, not an official Rust project. Media-level redistribution rights still require review.
