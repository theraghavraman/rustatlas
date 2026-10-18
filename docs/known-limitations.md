# Known limitations — complete book-text build

1. **28 illustrations are external, not offline-bundled.** The supplied `rust-book.md` references 28 SVG/PNG files but does not contain them. Original `src` references were retained in the manifest; rendered HTML links to the official Rust Book image URLs. The reader has accessible text and a link fallback if an image cannot load. Image byte-level integrity, offline imagery and image licensing are **unverified**. These are open review items.
2. **No actual Rust compilation or execution.** Interactive Concept Lab is a conceptual model, quizzes have deterministic answer keys, and coding challenges are self-reviewed. No arbitrary Rust code runs in the browser or on a server.
3. **Browser policy limits navigation and persistence testing.** Chromium returned `ERR_BLOCKED_BY_ADMINISTRATOR` when navigating to local `file://` and `127.0.0.1` URLs. The 27 browser smoke tests ran against the **exact single-file HTML** injected into the Chromium document using Playwright, validating navigation/reader DOM, search, labs, practice, appendices, responsive layout and absence of uncaught JS errors. Production URL/deployment navigation, offline image loading and browser-local persistence need unrestricted browser testing.
4. **Semantic and accessibility acceptance remains.** Automatic text/code/heading hash checks verify structural preservation but not every lesson's pedagogical suitability, screen-reader behavior or all long-table edge cases.
5. **Source-format conversion is version-specific.** The uploaded Pandoc-style Markdown has headings wrapped in HTML anchors and hundreds of repeated generated code-block IDs. The derived HTML normalizes these IDs without modifying user source. The uploaded Markdown contains one broken footnote backlink; its corresponding anchor is restored in the derived HTML.
6. **Public redistribution licensing requires follow-up.** Preserve the Rust Book contributor attribution and verify any rights and notices for external images/third-party resources.
7. **Progress is stored locally** in browsers that allow localStorage; no cross-device accounts or backups are provided, though progress JSON export is available.

## Content coverage release gate

**All 15,609 tracked source-text/code/structural elements were present and passed hash checks.** This is not the same as certifying that every original image is packaged or that all interactions have passed production-browser/manual accessibility review. `full_release_verified` remains `false` until outstanding items are resolved and audited.
