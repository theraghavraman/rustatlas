#!/usr/bin/env python3
"""Build one self-contained HTML file with every Rust Book section, not runtime fetches."""
from __future__ import annotations
from pathlib import Path
from html import escape
import json, re

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
OUT=ROOT/'rust-atlas-complete.html'


def inline_js():
    parts=[]
    for script in ['concepts.js','practice.js','app.js']:
        js=(ROOT/'src'/script).read_text(encoding='utf-8')
        js=re.sub(r'^import\s+\{[^}]+\}\s+from\s+[\'\"][^\'\"]+[\'\"];?\s*$', '', js, flags=re.M)
        js=re.sub(r'^export\s+(?=(const|function)\b)', '', js, flags=re.M)
        parts.append(f'\n/* source: {script} */\n'+js)
    return '\n'.join(parts).replace('</script','<\\/script')


def export(out:Path=OUT):
    manifest=json.loads((DIST/'book-manifest.json').read_text(encoding='utf-8'))
    coverage=json.loads((DIST/'data'/'coverage-summary.json').read_text(encoding='utf-8'))
    assert coverage['verified_elements']==coverage['source_elements'] and coverage['fatal_errors']==0, 'Failed core content integrity verification'
    assert len(manifest['chapters'])==coverage['verified_chapter_routes'], 'Missing chapter routes'
    pages={c['slug']:json.loads((DIST/c['path']).read_text(encoding='utf-8')) for c in manifest['chapters']}
    search=json.loads((DIST/'data'/'search-index.json').read_text(encoding='utf-8'))
    # UI needs only source metadata, chapter headings and counts, not the 5MB
    # per-element checker database. That full database remains in the ZIP.
    metadata={k:v for k,v in manifest.items() if k in ('title','source_url','source_sha256','target_rust_version','rust_edition','import_mode','chapters','source_counts')}
    metadata['source_elements']=len(manifest['elements'])
    payload={'manifest':metadata,'coverage':coverage,'pages':pages,'search':search}
    # U+003c escaping prevents embedded book text containing </script> from
    # closing the script element early, while preserving content on parsing.
    literal=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    html=(ROOT/'src'/'index.html').read_text(encoding='utf-8')
    svg=(ROOT/'src'/'favicon.svg').read_text(encoding='utf-8')
    from urllib.parse import quote
    html=html.replace('href="favicon.svg"',f'href="data:image/svg+xml,{quote(svg)}"')
    html=html.replace('<link rel="stylesheet" href="styles.css" />','<style>\n'+(ROOT/'src'/'styles.css').read_text(encoding='utf-8')+'\n</style>')
    html=html.replace('<script type="module" src="app.js"></script>',
                      '<script>window.__ATLAS_EMBEDDED='+literal+';</script>\n<script>\n'+inline_js()+'\n</script>')
    html=html.replace('with the complete official book (when source imported)', 'with the entire supplied Rust Book embedded locally')
    if 'src="app.js"' in html or 'href="styles.css"' in html:
        raise RuntimeError('Standalone HTML still depends on external JS/CSS')
    out.write_text(html,encoding='utf-8')
    print(f'Standalone HTML: {out.name} ({out.stat().st_size:,} bytes); {len(pages)} sections; '+
          f'{len(search)} search entries; {coverage["verified_elements"]} checked content elements.')
    return out

if __name__=='__main__':export()
