# Testing report

Generated: 2026-10-18T14:59:05Z

| Verification | Outcome |
|---|---|
| Source import | COMPLETE (snapshot hash recorded) |
| Content element hashing | 15609/15609 matched |
| Route payloads | 111/111 non-empty |
| Search targets | 4938 indexed entries; checked |
| Asset retrieval | 0/28 local assets |
| Automated structural issues | 0 |
| Open review items | 28 |
| Real browser E2E tests | 27/27 passed in actual standalone Chromium DOM smoke test; policy prevented direct-URL navigation |
| Mobile / tablet visual inspection | Tested at 1440, 800 and 390 px; no page-level horizontal overflow |
| Accessibility manual review | NOT RUN by this import command |
| Rust compilation of user code | NOT SUPPORTED; must not be described as compiled |
| Deployment validation | Still requires unrestricted real-URL/browser test |

## Release gate

**RELEASE NOT VERIFIED** — structural coverage does not replace real browser, content, and pedagogical testing. Address all missing/review items and run the additional checks.

## Failures

- None detected in automated checks.

## Manual review / known issues

- Unverified image: img/ferris/does_not_compile.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/ferris/panics.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/ferris/not_desired_behavior.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl04-01.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl04-02.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl04-03.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl04-04.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl04-05.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl04-06.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl04-07.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl14-01.png (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl14-02.png (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl14-03.png (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl14-04.png (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl15-01.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl15-02.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl15-03.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl15-04.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl17-01.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl17-02.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl17-03.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl17-04.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl17-05.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl17-06.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl17-07.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl17-08.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl17-09.svg (Not included in uploaded Markdown; official image URL linked (network required))
- Unverified image: img/trpl21-01.png (Not included in uploaded Markdown; official image URL linked (network required))

## Uploaded-book and browser acceptance evidence

- **17/17 Python automated tests passed**: ten importer regression/omission checks plus seven actual book/source integrity checks.
- **27/27 Chromium DOM and layout checks passed** across desktop 1440 px, tablet 800 px and mobile 390 px. Checks covered embedded HTML startup, all 111 contents routes listed, the actual ownership chapter, appendix G content, full-book search, lab state change, practice choices, uncaught JavaScript errors, and horizontal overflow.
- **Browser execution method:** Playwright/Chromium loaded the *exact standalone HTML* with `page.set_content()`. The environment's managed Chromium blocked navigation to both `file:///` and `http://127.0.0.1/` with `ERR_BLOCKED_BY_ADMINISTRATOR`. This permits meaningful rendered-DOM and interaction verification but **does not** count as file/HTTP navigation or deployment acceptance.
- **Additional unverified aspects:** all 28 original media files, exact-screen-reader audit, browser persistence in an unrestricted origin, local-file launch in a user's browser, and public hosting.
- **Proof artifacts:** `docs/browser-fullbook-evidence.json`, `docs/coverage-summary.json`, `docs/verification-details.json`, `tests/test_uploaded_fullbook.py`, and `tests/browser_fullbook.py`.

**Verdict:** Full uploaded-book **text and code** imported and structurally verified. **Full website release remains NOT CERTIFIED** due media and manual/deployment review. A successful build by itself is never proof of completeness.

## Pure HTML original-book parity

- Generated `rust-book-complete-static.html` containing literal HTML paragraphs, headings, code listings, figures, tables and the full body content, with JavaScript not required to read any chapter.
- Compared the normalized visible text of the static document against the original converted source body: **exact equality**.
- Structural element counts matched exactly: 111 `h1`, 120 `h2`, 293 `h3`, 103 `h4`, 1 `h5`, 957 `pre`, 433 `figure`, 13 `table` and 28 `img`.
- All 119 multi-file static site resources (111 content pages plus 8 entry assets/manifests) were served and retrieved successfully with a real local HTTP server. See `docs/http-delivery-evidence.json`. Chromium URL navigation was separately blocked by environment policy.
