"""Browser QA without network: in-memory document plus fetch stubs for preview data.
This does not replace HTTP/deployment QA. Does not verify imported Rust Book.
"""
from pathlib import Path
import json,re,os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).parents[1]
source=(ROOT/'src'/'index.html').read_text()
source=re.sub(r'<link rel="stylesheet"[^>]*>', '', source)
source=re.sub(r'<script type="module" src="app.js"></script>', '', source)
css=(ROOT/'src'/'styles.css').read_text()
mod1=(ROOT/'src'/'concepts.js').read_text().replace('export const','const').replace('export function','function')
mod2=(ROOT/'src'/'practice.js').read_text().replace('export const','const').replace('export function','function')
app=re.sub(r'^import[^;]+;\n','',(ROOT/'src'/'app.js').read_text(),flags=re.MULTILINE)
script=mod1+'\n'+mod2+'\n'+app
fetched=json.loads((ROOT/'dist'/'data'/'demo.json').read_text())
with sync_playwright() as p:
    chromium_path=os.environ.get('CHROMIUM_PATH')
    if not chromium_path and Path('/usr/bin/chromium').is_file():
        chromium_path='/usr/bin/chromium'
    options={'headless':True}
    if chromium_path: options['executable_path']=chromium_path
    if os.environ.get('CI'): options['args']=['--no-sandbox']
    browser=p.chromium.launch(**options)
    for name,width,height in [('desktop',1440,900),('tablet',800,1024),('mobile',390,844)]:
        page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(source)
        page.add_style_tag(content=css)
        page.evaluate("""data => {window.__demo=data;window.fetch=async url=>({ok:String(url).includes('demo.json'), status: String(url).includes('demo.json')?200:404,json:async()=>window.__demo});} """,fetched)
        page.add_script_tag(content=script)
        page.wait_for_timeout(350)
        assert 'Code with' in page.locator('main').inner_text(), (name,page.locator('main').inner_text()[:400],errors)
        page.screenshot(path=str(ROOT/f'{name}-home.png'),full_page=True)
        print(name,'home',len(page.locator('main').inner_text()),'errors:',errors)
        page.evaluate("location.hash='#read/start'")
        page.wait_for_timeout(320)
        assert 'A first look' in page.locator('main').inner_text()
        page.screenshot(path=str(ROOT/f'{name}-reader.png'),full_page=True)
        page.evaluate("location.hash='#lab'")
        page.wait_for_timeout(320)
        before=page.locator('.lab-explain').inner_text()
        page.locator('[data-lab-control="next"]').click()
        after=page.locator('.lab-explain').inner_text()
        assert before!=after
        page.screenshot(path=str(ROOT/f'{name}-lab.png'),full_page=True)
        page.evaluate("location.hash='#practice'")
        page.wait_for_timeout(320)
        page.locator('[data-answer="1"]').click()
        page.locator('[data-submit-answer]').click()
        assert 'Correct—here is why' in page.locator('main').inner_text()
        page.screenshot(path=str(ROOT/f'{name}-practice.png'),full_page=True)
        page.evaluate("location.hash='#learning'")
        page.wait_for_timeout(320)
        assert 'Concept checks' in page.locator('main').inner_text()
        page.screenshot(path=str(ROOT/f'{name}-learning.png'),full_page=True)
        assert not errors,(name,errors)
        dims=page.evaluate('({width:document.documentElement.scrollWidth, inner:window.innerWidth})')
        assert dims['width']<=dims['inner']+3,(name,dims)
        print(name,'passed routes/read/lab/practice/dashboard, dimensions',dims)
        page.close()
    browser.close()
