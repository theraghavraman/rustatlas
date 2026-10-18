#!/usr/bin/env python3
"""End-to-end checks against the actual uploaded Rust Book, not a fixture."""
from __future__ import annotations
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
FULL_HTML=(ROOT/'rust-atlas-complete.html').read_text(encoding='utf-8')
def go(page,hash):page.evaluate('(value) => {location.hash=value}',hash)
results=[]

def check(name,fn):
    try:fn();results.append({'name':name,'status':'PASS'})
    except Exception as e:results.append({'name':name,'status':'FAIL','message':str(e)[:600]});print('FAIL',name,e)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in (1440,800,390):
        ctx=browser.new_context(viewport={'width':width,'height':900},service_workers='block',java_script_enabled=True)
        page=ctx.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.set_content(FULL_HTML,wait_until='domcontentloaded',timeout=100000)
        page.wait_for_selector('.home-hero',timeout=45000)
        check(f'{width}px embedded home loads',lambda: (
            (_ for _ in ()).throw(AssertionError('No learning studio')) if not page.get_by_text('Code with').count() else None))
        check(f'{width}px 111 original source sections displayed',lambda: (
            go(page,'#read'),page.wait_for_selector('.chapter-grid .chapter-tile',timeout=25000),
            (_ for _ in ()).throw(AssertionError('Expected 111 source sections, got '+str(page.locator('.chapter-grid .chapter-tile').count()))) if page.locator('.chapter-grid .chapter-tile').count()!=111 else None))
        check(f'{width}px real original ownership chapter displays',lambda: (
            go(page,'#read/what-is-ownership-1'),page.wait_for_selector('#book-content',timeout=25000),
            (_ for _ in ()).throw(AssertionError('Source text missing')) if 'ownership' not in page.locator('#book-content').inner_text().lower() else None))
        check(f'{width}px appendix destination works',lambda: (
            go(page,'#read/g-how-rust-is-made-and-nightly-rust'),page.wait_for_selector('#book-content',timeout=25000),
            (_ for _ in ()).throw(AssertionError('Appendix content missing')) if 'nightly' not in page.locator('#book-content').inner_text().lower() else None))
        check(f'{width}px search opens relevant book results',lambda: (
            page.locator('[data-open-search]').first.click(),page.locator('#search-input').fill('ownership'),
            page.wait_for_selector('.search-result',timeout=30000),
            (_ for _ in ()).throw(AssertionError('No search results')) if not page.locator('.search-result').count() else None,
            page.locator('#close-search').click()))
        check(f'{width}px lab visualization controls work',lambda: (
            go(page,'#lab'),page.wait_for_selector('.lab-panel',timeout=30000),
            page.locator('[data-lab-control="next"]').click(),
            (_ for _ in ()).throw(AssertionError('Next lab step did not advance')) if 'State 2 of' not in page.locator('.lab-counters').inner_text() else None))
        check(f'{width}px practice questions render',lambda: (
            go(page,'#practice'),page.wait_for_selector('[data-answer]',timeout=30000),
            (_ for _ in ()).throw(AssertionError('Choices missing')) if page.locator('[data-answer]').count()<2 else None))
        check(f'{width}px no uncaught JavaScript exceptions',lambda: (
            (_ for _ in ()).throw(AssertionError('; '.join(errors))) if errors else None))
        go(page,'#read/what-is-ownership-1')
        page.wait_for_selector('#book-content',timeout=30000)
        page.screenshot(path=str(ROOT/'build'/f'fullbook-reader-{width}.png'),full_page=False)
        # Horizontal scrolling within pre/table is allowed, viewport overflow is not.
        def overflow():
            info=page.evaluate('''() => ({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth})''')
            assert info['w']<=info['c']+8, f'horizontal overflow {info}'
        check(f'{width}px no page-level horizontal overflow',overflow)
        ctx.close()
    browser.close()

summary={'source':'uploaded Markdown, bundled standalone HTML','test_cases':len(results),
         'passed':sum(t['status']=='PASS' for t in results),
         'failed':sum(t['status']=='FAIL' for t in results),'results':results}
(ROOT/'docs'/'browser-fullbook-evidence.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({'passed':summary['passed'],'failed':summary['failed'],'count':summary['test_cases']}))
if summary['failed']:raise SystemExit(1)
