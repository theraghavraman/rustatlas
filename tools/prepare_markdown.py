#!/usr/bin/env python3
"""Normalize source's Pandoc-wrapped HTML headings without changing their text.
Use the original Markdown as the immutable source, and generate an HTML intermediate.
"""
from pathlib import Path
import re
import subprocess
import argparse
from bs4 import BeautifulSoup
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'source'/'rust-book.original.md'

def normalize(source: str):
    lines=source.splitlines(keepends=True)
    out=[];i=0;merged=0
    while i<len(lines):
        line=lines[i]
        if re.match(r'^\s{0,3}#{1,6} +<a\b',line):
            pieces=[line.rstrip('\r\n')];i+=1
            while '</a>' not in pieces[-1] and i<len(lines):
                pieces.append(lines[i].rstrip('\r\n'));i+=1
            if '</a>' not in pieces[-1]:
                raise ValueError('Unclosed heading anchor at line '+str(i))
            out.append(' '.join(x.strip() for x in pieces)+'\n')
            merged+=1
        else:
            out.append(line);i+=1
    return ''.join(out), merged

def prepare(src: Path, out: Path, normalized: Path):
    raw=src.read_text(encoding='utf-8')
    result,count=normalize(raw)
    normalized.parent.mkdir(exist_ok=True, parents=True)
    normalized.write_text(result,encoding='utf-8')
    cmd=['pandoc','-f','markdown+raw_html+fenced_code_blocks+pipe_tables', '-t','html5', '--wrap=none','--output',str(out),str(normalized)]
    subprocess.run(cmd,check=True)
    fragment=out.read_text(encoding='utf-8')
    soup=BeautifulSoup(fragment,'html.parser')
    # Original source h1..h6 IDs are carried by their self-links, not by
    # Pandoc's automatically generated header anchors.
    for heading in soup.find_all(['h1','h2','h3','h4','h5','h6']):
        original_link=heading.find('a',class_='header',href=True)
        if original_link and original_link['href'].startswith('#'):
            heading['id']=original_link['href'][1:]
            # Pandoc's native_divs promotes a nested heading ID onto its
            # enclosing note section, leaving a duplicate when we restore
            # the book's explicit anchor. The section's ID is generated,
            # not from the uploaded Markdown, so keep the heading ID.
            parent=heading.find_parent('section')
            if parent is not None and parent.get('id')==heading.get('id'):
                del parent['id']
    # Pandoc reuses 'cb1' and line IDs for hundreds of independent code
    # listings in the single printable book. Scope these DOM-only IDs to
    # their listing so HTML ids remain globally unique.
    for i,code in enumerate(soup.select('div.sourceCode'),start=1):
        previous=code.get('id')
        if not previous:continue
        new=f'rust-code-{i:04d}'
        remap={previous:new}
        code['id']=new
        for child in code.find_all(id=True):
            old=child['id']
            if old.startswith(previous+'-'):
                remap[old]=new+old[len(previous):]
                child['id']=remap[old]
        for child in code.find_all('a',href=True):
            if child['href'].startswith('#') and child['href'][1:] in remap:
                child['href']='#'+remap[child['href'][1:]]
    # The uploaded source has a footnote backlink to #fr-siphash-1 but
    # omits the corresponding marker. Restore its target in derived HTML.
    backlink=soup.select_one('a[href="#footnote-siphash"]')
    if backlink and not soup.select_one('[id="fr-siphash-1"]'):
        target=backlink.find_parent('sup') or backlink
        target['id']='fr-siphash-1'
    duplicates=[x for x,n in Counter(x['id'] for x in soup.select('[id]')).items() if n>1]
    if duplicates:
        raise ValueError(f'HTML id collision remains: {duplicates[:10]}')
    fragment=str(soup)
    out.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"></head><body><main id="content">\n'+fragment+'\n</main></body></html>', encoding='utf-8')
    print(f'Normalized {count} source headings; converted {len(raw):,} chars of Markdown to {out.stat().st_size:,} HTML bytes')
    return count

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,default=DEFAULT)
    args=ap.parse_args()
    prepare(args.source,ROOT/'build'/'rust-book.pandoc.html',ROOT/'build'/'rust-book.normalized.md')
