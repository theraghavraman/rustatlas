# Source audit — supplied Markdown, not a remote dependency

- **Authoritative input:** `source/rust-book.original.md`, copied unchanged from the user-supplied `rust-book.md`.
- **Original bytes:** 2,243,508; source lines: 39,383; original SHA-256: `c5a6eefc965ca3ba97f0b776611fc0aaaf1805d00c43d7c5a9e7b15849ea141a`.
- **Title:** *The Rust Programming Language*, by Steve Klabnik, Carol Nichols, Chris Krycho and Rust Community contributors.
- **Version declared in input:** Rust 1.97.0 or later, Rust 2024 Edition.
- **Original content:** book front matter, 21 numbered chapters, appendices A–G, 111 original top-level printable-book sections.
- **Original structural counts:** 628 Markdown heading elements, 433 source HTML figure elements, 28 referenced image elements (source assets not supplied).
- **Derived pinned snapshot:** `source/print.snapshot.html`; SHA-256 `1db75252aac487cc636489929ebe7a0c01610f5d945776ea224299967b3106ac`.
- **Conversion:** `tools/prepare_markdown.py` + Pandoc 3.1.11.1 generated semantic HTML; the duplicate `cb1` code IDs were made unique for single-page rendering, and one missing original footnote backlink anchor was restored. Original prose/code was not edited.
- **Generated book:** 111 page payloads, 628 headings, 957 code/terminal pre blocks, 433 figures, 13 tables, 28 referenced image tags, 15,609 tracked structural and text elements, 4,938 full-text search entries.
- **Traceability:** Every processed content element has a source page, destination page, deterministic ID and hash. `dist/book-manifest.json` and `docs/verification-details.json` preserve this mapping.

The HTML image tags are present and verified structurally, but **image bytes are not in the uploaded Markdown**. The reader links the 28 images to original Rust Book image URLs and records all 28 as unresolved media review items. There is no claim of complete offline image coverage.

Book repository and licensing information: <https://github.com/rust-lang/book> — see `licensing-and-attribution.md`.
