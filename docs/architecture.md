# Rust Atlas architecture — complete uploaded Markdown build

The authoritative material for this build is the **user-provided `rust-book.md`**, archived verbatim at `source/rust-book.original.md` (SHA-256 `c5a6eefc965ca3ba97f0b776611fc0aaaf1805d00c43d7c5a9e7b15849ea141a`). It is the 2024 Edition book that identifies Rust 1.97.0 as its target. No alternate Rust Book edition is substituted.

## Three production presentation modes

- **Standalone document (`index.html`, `rust-atlas-complete.html`):** A single HTML file contains all original book HTML, chapter metadata, searchable text fragments, stylesheet and JavaScript for the entire interactive site. It does not fetch book chapters from a server. A user can open the file directly in an ordinary browser. External original-book illustrations are links and require network access.
- **Literal static book (`rust-book-complete-static.html`):** A readable, JavaScript-free HTML page contains all 111 source page sections and every original paragraph/code/table/figure markup. All 628 source headings, 957 code blocks, 433 figure containers, 13 tables and 28 image elements are preserved. The 28 images link to the official site and are not bundled offline.
- **Static site (`dist/`):** `dist/index.html` serves a lightweight frontend; generated `content/*.json` pages are fetched on demand by hash routes `#read/<slug>?anchor=<heading-id>`. The search index is prebuilt. It has no database/server business logic and is suitable for static hosting.

## Provenance-preserving pipeline

1. `tools/prepare_markdown.py` normalizes only the structural wrapper around 628 HTML-anchored Markdown headings, invokes Pandoc, restores original heading anchors, assigns unique IDs to code-line markup and repairs one missing footnote backlink (derived HTML only).
2. `tools/book_pipeline.py` parses 111 top-level book pages/sections in order, preserves their complete HTML block markup, creates stable per-element IDs/hashes, remaps internal links, records original image URLs, creates manifest and per-page JSON, and generates 4,938 source search documents.
3. The verifier independently checks page existence, element identities and normalized text fingerprints, code/table/image element inventories, search destinations, internal links and asset status. **Unverified images are explicitly reported**; the release flag is never set based solely on build or structural verification.
4. `tools/export_standalone.py` bundles the same verified page payloads and the maintained source UI into a single HTML deliverable without runtime book fetches. Script JSON is escaped to safely embed source examples containing HTML markup.
5. `tools/export_static_book.py` also emits literal, full-length semantic HTML with unmodified visible book text compared to the pinned source, independent of any JavaScript application.
6. A synthetic 10-test suite checks omissions, altered text, hashes, URLs and asset failures; seven actual book tests compare source-level headings/pages/counts; 27 Chromium DOM smoke cases exercise the exact standalone HTML at three widths.

## Presentation and educational features

`src/app.js` owns hash routing, navigation, search, reading tools and progress; `src/concepts.js` provides ten interactive pedagogical models; `src/practice.js` provides sixteen book-aligned supplementary activities. Original source text is not mixed into these scripts. The app uses browser localStorage when available for notes, bookmarks and progress. Original book content and supplementary lessons are labeled separately. User Rust code is never compiled, executed or simulated as verified compilation.

## Open engineering work

Complete local image acquisition and verification, a screen-reader audit, production URL/deployment routing checks, and storage persistence tests in an unrestricted browser. See `known-limitations.md` and `testing-report.md`.
