#!/usr/bin/env python3
"""Publish the complete uploaded book as literal readable HTML, no JavaScript required."""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
from html import escape
import hashlib

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'source'/'print.snapshot.html'
OUT=ROOT/'rust-book-complete-static.html'
SOURCE_URL='https://doc.rust-lang.org/book/print.html'

CSS='''
:root{color-scheme:light;--paper:#fcf9f4;--ink:#243630;--copper:#ad6b3d;--edge:#e9e0d5}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.75 Georgia,serif}
a{color:#96572f;text-underline-offset:3px}a:focus-visible,button:focus-visible{outline:3px solid #bd7344;outline-offset:3px}
header{position:sticky;top:0;z-index:9;display:flex;align-items:center;justify-content:space-between;gap:14px;padding:13px clamp(15px,3vw,44px);background:#fffefaee;backdrop-filter:blur(12px);border-bottom:1px solid var(--edge);font:14px/1.4 system-ui,sans-serif}
.brand{display:flex;align-items:center;gap:12px;font-weight:850;font-size:18px;text-decoration:none;color:#314038}.brand b{background:#b77543;color:white;padding:7px 10px;border-radius:11px}.brand span{color:#b77543}.top-links{display:flex;gap:17px;align-items:center}.top-links a{font-size:12px;text-decoration:none;font-weight:700}
.layout{max-width:1650px;margin:auto;padding:28px clamp(15px,3vw,46px);display:grid;grid-template-columns:280px minmax(0,1fr);gap:clamp(24px,5vw,90px);align-items:start}
aside{position:sticky;top:90px;max-height:calc(100vh - 108px);overflow:auto;padding:16px;background:#fffefa;border:1px solid var(--edge);border-radius:18px;font:12px/1.5 system-ui,sans-serif;scrollbar-width:thin}
aside .label{display:block;color:#a46f49;font-size:10px;letter-spacing:1.3px;text-transform:uppercase;font-weight:850;margin:0 0 12px 6px}
aside a{display:block;color:#5e6b64;text-decoration:none;line-height:1.4;padding:8px;border-radius:9px;border-bottom:1px solid #f1ebe4}aside a:hover,aside a:focus{background:#f8eadc;color:#9e5d30}
#content{min-width:0;max-width:880px;width:100%;background:white;border:1px solid var(--edge);border-radius:24px;padding:clamp(24px,4vw,65px);box-shadow:0 15px 60px #64563e0d;overflow-wrap:anywhere}
#content h1,#content h2,#content h3,#content h4,#content h5,#content h6{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;letter-spacing:-.035em;line-height:1.24;color:#253b32;scroll-margin-top:90px}
#content h1{font-size:clamp(28px,3.3vw,41px);padding-top:40px;margin-top:60px;border-top:1px solid var(--edge)}#content h1:first-child{padding-top:0;margin-top:0;border:none}#content h2{font-size:clamp(23px,2.8vw,31px);margin-top:35px}#content h3{font-size:22px;margin-top:32px}#content h4{font-size:18px;margin-top:27px}
#content p{margin:15px 0}#content li{margin:8px 0}#content ul,#content ol{padding-left:24px}#content .header{color:inherit;text-decoration:none}
#content pre{max-width:100%;overflow:auto;white-space:pre;background:#26372f;border:1px solid #425348;color:#f6f4ea;border-radius:13px;padding:18px 20px;line-height:1.65;font:13px/1.7 'SFMono-Regular',Consolas,ui-monospace,monospace}
#content pre code{background:transparent;color:inherit;padding:0}#content code:not(pre code){font:.85em ui-monospace,Consolas,monospace;background:#f4eee6;color:#844f2f;padding:2px 4px;border-radius:4px}
#content img{display:block;max-width:100%;height:auto;margin:15px auto}#content figure{max-width:100%;min-width:0;overflow-x:auto;margin:24px 0}#content figcaption{font:12px/1.5 system-ui,sans-serif;color:#718076;margin:9px 0}
#content table{font:13px/1.5 system-ui,sans-serif;border-collapse:collapse;display:block;max-width:100%;overflow:auto;margin:19px 0}#content th,#content td{padding:10px;border:1px solid #e7dfd3;text-align:left}#content th{background:#f6f0e7}
#content .table-wrapper{max-width:100%;overflow-x:auto}#content blockquote{border-left:4px solid #d2a77b;background:#fff6eb;margin:22px 0;padding:12px 21px}#content .note{padding:16px 19px;margin:22px 0;border-left:3px solid #bb854e;background:#fcf5e8;border-radius:9px}
#content hr{border:0;border-top:1px solid #e5dfd5;margin:28px 0}
#content .source-image-fallback{display:flex;gap:4px;flex-direction:column;background:#fff6ea;border:1px dashed #d7aa75;border-radius:9px;padding:12px 15px;font:12px/1.5 system-ui,sans-serif}
#content .source-image-fallback a{font-weight:750}#content img:not([alt]){min-height:20px}
.breadcrumb{font:11px system-ui,sans-serif;color:#8b714f;margin-bottom:25px;letter-spacing:.7px}.reading-disclaimer{font:12px/1.65 system-ui,sans-serif;border:1px solid #e8d5bd;background:#fff5e6;color:#80613d;border-radius:12px;padding:14px 16px;margin-bottom:32px}
footer{padding:30px;max-width:850px;margin:auto;color:#8c938a;font:12px system-ui,sans-serif;text-align:center}#jump{position:fixed;right:16px;bottom:20px;border:1px solid var(--edge);box-shadow:0 4px 19px #3b30222a;background:#fff;padding:10px 14px;border-radius:12px;text-decoration:none;font:12px system-ui,sans-serif}
@media(max-width:850px){.layout{grid-template-columns:minmax(0,1fr)}aside{position:static;max-height:210px;overflow:auto}#content{padding:24px 22px}.top-links{display:none}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto!important}}
'''


def build():
    soup=BeautifulSoup(SRC.read_text(encoding='utf-8'),'html.parser')
    main=soup.select_one('#content')
    assert main is not None
    text_before=' '.join(main.stripped_strings)
    sections=[]
    for h in main.find_all('h1'):
        if not h.get('id'):continue
        sections.append((h['id'],h.get_text(' ',strip=True)))
    for img in main.find_all('img'):
        path=img.get('src','')
        if path and not urlparse(path).scheme:img['src']=urljoin(SOURCE_URL,path)
        img['loading']='lazy'
        img['decoding']='async'
        img['title']=img.get('alt') or 'Official Rust Book illustration'
    for a in main.find_all('a',href=True):
        href=a['href']
        if href.startswith('#'):continue
        if not urlparse(href).scheme and not href.startswith('mailto:'):
            a['href']=urljoin(SOURCE_URL,href)
        a['rel']='noopener noreferrer';a['target']='_blank'
    assert len(sections)==111
    assert ' '.join(main.stripped_strings)==text_before, 'Unexpected change in original book visible text'
    lis='\n'.join(f'<a href="#{escape(id,quote=True)}">{i+1:03d} &nbsp; {escape(title)}</a>' for i,(id,title) in enumerate(sections))
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>The Rust Programming Language — Complete Book HTML · Rust Atlas</title><meta name="description" content="Complete The Rust Programming Language, Rust 2024 Edition, from the supplied Markdown, faithfully converted to HTML."><style>{CSS}</style></head>
<body id="top"><header><a class="brand" href="#top"><b>✳</b>rust<span>atlas</span> / THE BOOK</a><div class="top-links"><a href="rust-atlas-complete.html">Interactive learning studio ↗</a><a href="https://github.com/rust-lang/book">Rust Book source ↗</a></div></header>
<div class="layout"><aside aria-label="All original book sections"><span class="label">Complete source contents · {len(sections)} sections</span>{lis}</aside><div><div class="reading-disclaimer"><strong>Complete supplied book prose, code, tables and structural figures.</strong> This HTML contains the full text of the uploaded Markdown and works without JavaScript. The Markdown did not supply the image files for 28 illustrations, which reference official external URLs and require an internet connection. <a href="rust-atlas-complete.html">Open interactive learning version ↗</a>.</div><article id="content" aria-label="The Rust Programming Language">{''.join(str(x) for x in main.contents)}</article></div></div>
<footer>Book authors: Steve Klabnik, Carol Nichols, Chris Krycho and the Rust Community · <a href="https://github.com/rust-lang/book">Original source and license</a> · Independent Rust Atlas reading layout</footer><a id="jump" href="#top">↑ Back to top</a></body></html>'''
    OUT.write_text(html,encoding='utf-8')
    print(f'Pure static full-book HTML: {OUT.stat().st_size:,} bytes, {len(sections)} full source sections')

if __name__=='__main__':build()
