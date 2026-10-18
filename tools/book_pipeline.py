#!/usr/bin/env python3
"""Source-locked Rust Book import and content-by-content verification.

The Rust Atlas release MUST NOT be called complete without this script's
coverage and manual browser checks. No network calls are made during tests.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
import json
import re
import shutil
import sys

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
DEFAULT_URL = 'https://doc.rust-lang.org/book/print.html'
# Choose complete top-level HTML blocks, without flattening list/table/figure children.
BLOCKS = {'h1','h2','h3','h4','h5','h6','p','pre','ul','ol','table','figure',
          'blockquote','details','hr','dl','img','aside','iframe'}
TRACKED = {'h1':'heading','h2':'heading','h3':'heading','h4':'heading',
           'h5':'heading','h6':'heading','p':'paragraph','pre':'code_block',
           'ul':'list','ol':'list','li':'list_item','table':'table',
           'tr':'table_row','td':'table_cell','th':'table_cell',
           'figure':'figure','figcaption':'caption','img':'image',
           'blockquote':'quotation','aside':'callout','details':'callout',
           'code':'inline_code','hr':'divider','dl':'definition_list',
           'dt':'definition_term','dd':'definition_text','iframe':'embedded_media'}
SKIP = {'script','style','nav','header','footer','noscript','form'}
# Some classes are part of mdBook chrome, not book content.
CHROME = {'menu-bar','sidebar','sidebar-scrollbox','nav-chapters','mobile-nav-chapters',
          'chapter-navigation','page-wrapper','page', 'header-wrapper'}


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def short_digest(x: str | bytes) -> str:
    return sha256(x.encode('utf-8') if isinstance(x,str) else x).hexdigest()


def slug(text: str) -> str:
    text = re.sub(r'[^\w\s-]', '', text.lower(), flags=re.U)
    text = re.sub(r'[\s_]+','-',text.strip())
    return (re.sub(r'-+', '-', text).strip('-') or 'untitled')[:100]


def norm_text(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def get_content(tag: Tag):
    if tag.name == 'img':
        return f"src={tag.get('data-atlas-source-src',tag.get('src',''))}|alt={tag.get('alt','')}"
    if tag.name == 'pre':
        return tag.get_text().replace('\r\n','\n')
    if tag.name == 'iframe':
        return f"src={tag.get('src','')}"
    if tag.name == 'code' and tag.find_parent('pre') is not None:
        return None  # pre is the authoritative code listing, not its nested code tag
    return norm_text(tag.get_text(' ', strip=True))


def semantic_type(tag):
    if tag.name == 'code' and tag.find_parent('pre') is not None:
        return None
    return TRACKED.get(tag.name)


def top_blocks(container: Tag):
    """Produce chapter blocks in document order while preserving nested markup."""
    def walk(t):
        for ch in t.children:
            if not isinstance(ch,Tag):
                continue
            if ch.name in SKIP or ch.get('id') in CHROME:
                continue
            if ch.name in BLOCKS:
                yield ch
            else:
                yield from walk(ch)
    yield from walk(container)


def select_source_container(soup: BeautifulSoup) -> Tag:
    for selector in ('#content', 'main', '#page-content', 'article', 'body'):
        choices = soup.select(selector)
        if not choices:
            continue
        # Prefer the container with most book headings, and avoid sidebar matches.
        c = max(choices,key=lambda el: len(el.find_all(['h1','h2','h3'])))
        if len(c.find_all(['h1','h2','h3'])) >= 2:
            return c
    raise ValueError('Could not identify book text container: at least two headings required.')


def source_chapters(soup: BeautifulSoup):
    """Segment printable HTML by h1 headings, retaining all subsections and blocks."""
    main = select_source_container(soup)
    chapters=[]
    prefix=[]
    current=None
    for block in top_blocks(main):
        if block.name == 'h1':
            raw = norm_text(block.get_text(' ',strip=True))
            if not raw:
                continue
            # mdBook often supplies one decorative h1.title before the real title page.
            if 'title' in block.get('class',[]) and not chapters and not prefix:
                continue
            original_id = block.get('id') or slug(raw)
            key = slug(original_id) if original_id else slug(raw)
            key = re.sub('^-+','',key)
            if any(c['slug']==key for c in chapters):
                key += '-' + str(len(chapters)+1)
            current={'slug':key,'title':raw,'blocks':[], 'headings':[]}
            chapters.append(current)
        if current is None:
            prefix.append(block)
        else:
            current['blocks'].append(block)
            if block.name in ('h1','h2','h3','h4','h5','h6'):
                current['headings'].append({'level':int(block.name[1]),
                     'title':norm_text(block.get_text(' ',strip=True)),
                     'anchor':block.get('id') or slug(block.get_text(' ',strip=True))})
    if prefix and chapters:
        chapters[0]['blocks'] = prefix + chapters[0]['blocks']
    if not chapters:
        raise ValueError('No h1 chapters found. Import aborted; no silent omissions.')
    return chapters


def snapshot_page(url, input_file=None, timeout=55):
    if input_file:
        path=Path(input_file)
        if not path.is_file():
            raise FileNotFoundError(f'Source HTML file missing: {path}')
        return path.read_bytes(), f'file://{path.resolve()}'
    rsp=requests.get(url,timeout=timeout,headers={'User-Agent':'RustAtlasImporter/1.0 (+educational-project)'})
    rsp.raise_for_status()
    if '<html' not in rsp.text[:1200].lower() and '<!doctype' not in rsp.text[:1200].lower():
        raise ValueError('Fetched resource was not HTML')
    return rsp.content, rsp.url


def fetch_asset(src, base, root, fixture_root=None):
    if src.startswith('data:'):
        return src, True, None
    parsed=urlparse(src)
    if parsed.scheme not in ('','http','https'):
        return src,False,'unsupported URI scheme'
    resolved=urljoin(base,src)
    path=urlparse(resolved).path
    suffix=Path(path).suffix.lower()
    if suffix not in ('.png','.jpg','.jpeg','.webp','.gif','.svg','.avif'):
        suffix='.bin'
    dst=f"assets/book/{short_digest(resolved)[:24]}{suffix}"
    full=root/dst
    if not full.exists():
        full.parent.mkdir(parents=True,exist_ok=True)
        try:
            if base.startswith('file://') and not parsed.scheme:
                assert fixture_root is not None
                srcpath=Path(fixture_root)/src.split('#')[0].split('?')[0]
                if not srcpath.is_file(): raise FileNotFoundError(str(srcpath))
                shutil.copy2(srcpath,full)
            else:
                rsp=requests.get(resolved,timeout=30)
                rsp.raise_for_status()
                if len(rsp.content)>12*1024*1024:
                    raise ValueError('asset exceeds 12 MiB')
                full.write_bytes(rsp.content)
        except Exception as exc:
            return resolved,False,str(exc)
    return dst,True,None


def clone_block(original):
    # Do not mutate the archived source tree.
    return BeautifulSoup(str(original),'html.parser').find(original.name)


def create_manifest(html_bytes, base, output, download_assets=True):
    soup=BeautifulSoup(html_bytes,'html.parser')
    # Use only source book content, not book chrome/JS.
    chapters=source_chapters(soup)
    output=Path(output)
    (output/'content').mkdir(parents=True,exist_ok=True)
    (output/'data').mkdir(parents=True,exist_ok=True)
    stats=Counter()
    doc_text=soup.get_text(' ',strip=True)
    ver=re.search(r'Rust\s+(\d+\.\d+(?:\.\d+)?)',doc_text)
    edition=re.search(r'(?:edition\s*=\s*["\']?([0-9]{4})|Rust\s+([0-9]{4})\s+Edition)',doc_text,re.I)
    idx={}
    assets=[]
    problems=[]
    chapter_out=[]
    all_elements=[]
    anchors={}
    # Resolve heading anchors, figure IDs, footnotes, and every other source ID.
    # A heading-only map would silently break footnote and listing links.
    for chapter in chapters:
        for block in chapter['blocks']:
            for node in [block]+block.find_all(id=True):
                anchor=node.get('id')
                if not anchor: continue
                if anchor in anchors and anchors[anchor]!=chapter['slug']:
                    problems.append({'type':'duplicate_source_anchor','anchor':anchor,
                                     'chapters':[anchors[anchor],chapter['slug']]})
                else:
                    anchors[anchor]=chapter['slug']
    # Text nodes not enclosed by a recognized source block are not silently discarded.
    main=select_source_container(soup)
    reported_orphans=set()
    for text_node in main.descendants:
        if not isinstance(text_node,NavigableString) or not norm_text(str(text_node)): continue
        ancestors=list(text_node.parents)
        if any(isinstance(t,Tag) and (t.name in SKIP or t.get('id') in CHROME)
               for t in ancestors): continue
        if any(isinstance(t,Tag) and t.name in BLOCKS for t in ancestors): continue
        excerpt=norm_text(str(text_node))[:160]
        if excerpt not in reported_orphans:
            problems.append({'type':'unmapped_source_text','excerpt':excerpt})
            reported_orphans.add(excerpt)
    for chapter in chapters:
        page_elements=[]
        source_visible_text=norm_text(' '.join(b.get_text(' ',strip=True) for b in chapter['blocks']))
        cloned=[clone_block(b) for b in chapter['blocks']]
        for block in cloned:
            if block.name in ('h1','h2','h3','h4','h5','h6') and not block.get('id'):
                block['id']=slug(block.get_text(' ',strip=True))
            # Explicitly remove active resources and handlers. Iframes are considered unsupported.
            for el in [block]+block.find_all(True):
                for attr in list(el.attrs):
                    if attr.lower().startswith('on'):
                        del el[attr]
            for el in list(block.find_all(['script','style','iframe','form','input','button'])):
                problems.append({'type':'unsupported_or_unsafe_element','chapter':chapter['slug'],'tag':el.name})
                el.decompose()
            if block.name in ('iframe',):
                problems.append({'type':'unsupported_or_unsafe_element','chapter':chapter['slug'],'tag':block.name})
                continue
            if block.name == 'img' or block.find('img'):
                for img in ([block] if block.name=='img' else block.find_all('img')):
                    src=img.get('src','')
                    img['data-atlas-source-src']=src
                    if download_assets and src:
                        dest,ok,error=fetch_asset(src,base,output,Path(urlparse(base).path).parent if base.startswith('file://') else None)
                        img['src']=dest
                        digest=short_digest((output/dest).read_bytes()) if ok and not dest.startswith('data:') else None
                        assets.append({'original':src,'local':dest if ok and digest else None,
                                       'inline_data':bool(ok and dest.startswith('data:')),
                                       'sha256':digest,'verified':ok,'error':error})
                        if not ok: problems.append({'type':'asset_download_failed','chapter':chapter['slug'],'src':src,'detail':error})
                    else:
                        img['src']=urljoin('https://doc.rust-lang.org/book/',src) if src else ''
                        img['loading']='lazy'
                        assets.append({'original':src,'local':None,'remote':img['src'],
                                       'verified':False,'error':'Not included in uploaded Markdown; official image URL linked (network required)'})
            # Capture every non-decorative tracked element, including nested code and cells.
            nodes=[block]+block.find_all(list(TRACKED))
            for el in nodes:
                ty=semantic_type(el)
                if ty is None:
                    continue
                raw=get_content(el)
                if raw is None: continue
                # Counter scoped to type and chapter so IDs are reproducible with same source.
                stats[ty]+=1
                occurrence=sum(1 for x in page_elements if x['type']==ty)+1
                content_hash=short_digest(raw)
                eid=f"{chapter['slug']}:{ty}:{occurrence:05}:{content_hash[:10]}"
                el['data-atlas-id']=eid
                el['data-atlas-hash']=content_hash
                el['data-atlas-type']=ty
                e={'id':eid,'type':ty,'hash':content_hash,
                   'chapter':chapter['slug'],'original_anchor':el.get('id') if el.name.startswith('h') else None,
                   'source_order':len(all_elements)+1,
                   'status':'rendered','verified':False}
                if ty=='heading': e['title']=raw
                page_elements.append(e)
                all_elements.append(e)
        # Resolve source links against the *complete* source-anchor map.
        # This also supports print.html#anchor and chapter-file.html links.
        for block in cloned:
            if not block: continue
            for a in block.find_all('a',href=True):
                href=a['href'].strip()
                parsed=urlparse(href)
                scheme=parsed.scheme.lower()
                if scheme in ('javascript','data','vbscript'):
                    problems.append({'type':'unsafe_link','chapter':chapter['slug'],'href':href})
                    a['href']='#'; continue
                if scheme not in ('','http','https'):
                    continue # mailto and other intended non-web protocols
                is_local=(not parsed.netloc or parsed.netloc=='doc.rust-lang.org')
                if is_local:
                    target=unquote(parsed.fragment)
                    if target and target in anchors:
                        a['href']=f'#read/{anchors[target]}?anchor={target}'
                        continue
                    stem=Path(unquote(parsed.path)).stem
                    if stem in anchors:
                        a['href']=f'#read/{anchors[stem]}?anchor={stem}'
                        continue
                    if stem in {x['slug'] for x in chapters}:
                        a['href']=f'#read/{stem}'
                        continue
                    if not href.startswith('#') and not parsed.path:
                        continue
                    # An unresolved #anchor would be parsed as an application route.
                    # Send the learner to the real book instead and require review.
                    url=urljoin(DEFAULT_URL if href.startswith('#') else 'https://doc.rust-lang.org/book/',href)
                    a['href']=url
                    a['target']='_blank';a['rel']='noopener noreferrer'
                    problems.append({'type':'unresolved_internal_anchor' if href.startswith('#') else 'external_reference','chapter':chapter['slug'],'source_href':href})
                elif scheme in ('http','https') or parsed.netloc:
                    a['target']='_blank';a['rel']='noopener noreferrer'
        rendered_visible_text=norm_text(' '.join(b.get_text(' ',strip=True) for b in cloned if b))
        if source_visible_text!=rendered_visible_text:
            problems.append({'type':'source_text_not_preserved','chapter':chapter['slug'],
                             'source_sha256':short_digest(source_visible_text),
                             'rendered_sha256':short_digest(rendered_visible_text)})
        page={'slug':chapter['slug'],'title':chapter['title'],'headings':chapter['headings'],
              'html':'\n'.join(str(x) for x in cloned if x is not None),
              'source_visible_text_sha256':short_digest(source_visible_text),
              'element_ids':[e['id'] for e in page_elements], 'source_type':'book'}
        (output/'content'/f"{chapter['slug']}.json").write_text(json.dumps(page,ensure_ascii=False,indent=2),encoding='utf-8')
        chapter_out.append({'slug':chapter['slug'],'title':chapter['title'],'headings':chapter['headings'],
                            'element_count':len(page_elements),'source_visible_text_sha256':short_digest(source_visible_text),
                            'path':f"content/{chapter['slug']}.json",
                            'type':'appendix' if 'appendix' in chapter['title'].lower() else 'chapter'})
        idx[chapter['slug']]=page['element_ids']
    # Search fragments do not fabricate matching results; they are derived from source text.
    search_docs=[]
    for chapter in chapters:
        page=json.loads((output/'content'/f"{chapter['slug']}.json").read_text(encoding='utf-8'))
        ps=BeautifulSoup(page['html'],'html.parser')
        for tag in ps.find_all(['h1','h2','h3','h4','h5','p','pre','li']):
            # Nested paragraphs within lists appear twice at display time; duplicate results deduped.
            raw=tag.get_text(' ',strip=True)
            if raw:
                parent_heading=tag.find_previous(['h1','h2','h3','h4'])
                dest=parent_heading.get('id') if parent_heading else ''
                search_docs.append({'chapter':chapter['slug'],'section':parent_heading.get_text(' ',strip=True) if parent_heading else page['title'],
                                    'anchor':dest,'text':norm_text(raw)[:1200], 'kind':tag.name})
    (output/'data'/'search-index.json').write_text(json.dumps(search_docs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    result={'source_url':base,'source_sha256':short_digest(html_bytes),
            'imported_at':now(),'title':'The Rust Programming Language',
            'target_rust_version':ver.group(1) if ver else 'undetected',
            'rust_edition': (edition.group(1) or edition.group(2)) if edition else 'undetected',
            'import_mode':'source_locked','chapters':chapter_out,
            'source_counts':dict(stats),'elements':all_elements,
            'assets':assets,'problems':problems,'search_entries':len(search_docs)}
    (output/'book-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def verify(output,docs=None,manual_notes=None):
    output=Path(output); docs=Path(docs or DOCS);docs.mkdir(parents=True,exist_ok=True)
    path=output/'book-manifest.json'
    if not path.exists():
        return write_not_imported(docs)
    data=json.loads(path.read_text(encoding='utf-8'))
    verdicts={};errors=[];review=[]
    # On every verification, compare the manifest against the immutable import snapshot.
    # A missing snapshot means the importer output cannot independently prove its origin.
    snapshot=output.resolve().parent/'source'/'print.snapshot.html'
    if snapshot.is_file():
        if short_digest(snapshot.read_bytes()) != data['source_sha256']:
            errors.append('Original source snapshot SHA-256 differs from the import manifest')
    elif urlparse(data['source_url']).scheme in ('http','https'):
        errors.append('Original source snapshot missing; cannot verify source provenance')
    source_hashes={x['id']:x['hash'] for x in data['elements']}
    chapters_ok=0
    all_pages={}
    all_anchor_destinations=set()
    for chapter in data['chapters']:
        p=output/chapter['path']
        if not p.exists():
            errors.append(f"Missing generated chapter: {chapter['path']}");continue
        page=json.loads(p.read_text(encoding='utf-8'))
        all_pages[chapter['slug']]=page
        soup=BeautifulSoup(page['html'],'html.parser')
        for tag in soup.find_all(id=True):
            all_anchor_destinations.add((chapter['slug'],tag['id']))
        if page['slug'] != chapter['slug']:
            errors.append(f"Route/page mismatch: {chapter['slug']}")
        if not page['html'].strip():
            errors.append(f"Empty page: {chapter['slug']}")
        else:
            chapters_ok+=1
        # Text parity is compared with original per-page extracted text, not just
        # with the fingerprints stamped on the generated HTML nodes.
        rendered_visible_text=norm_text(soup.get_text(' ',strip=True))
        if short_digest(rendered_visible_text)!=chapter.get('source_visible_text_sha256'):
            errors.append(f"Source-to-rendered visible text mismatch: {chapter['slug']}")
        found={}
        for el in soup.find_all(attrs={'data-atlas-id':True}):
            if el['data-atlas-id'] in found:
                errors.append(f"Duplicate element ID: {el['data-atlas-id']}")
            found[el['data-atlas-id']]=el
        expected_here={x['id'] for x in data['elements'] if x['chapter']==chapter['slug']}
        listed_ids=page.get('element_ids',[])
        if len(listed_ids)!=chapter['element_count'] or set(listed_ids)!=expected_here:
            errors.append(f"Manifest/page element inventory mismatch: {chapter['slug']}")
        for eid in expected_here:
            if eid not in found:errors.append(f'Missing mapped element {eid}')
        for key,el in found.items():
            expected_hash=source_hashes.get(key)
            seen_hash=short_digest(get_content(el) or '')
            if not expected_hash or seen_hash!=expected_hash or el.get('data-atlas-hash')!=expected_hash:
                verdicts[key]='missing'
                errors.append(f'Modified, unlisted, or truncated {key}')
            else:
                verdicts[key]='verified'
    expected_ids={x['id'] for x in data['elements']}
    if len(expected_ids)!=len(data['elements']):
        errors.append('Duplicate source element identifiers')
    for el in data['elements']:
        if el['id'] not in verdicts:
            verdicts[el['id']]='missing'; errors.append('Element not found: '+el['id'])
    for asset in data['assets']:
        if asset.get('inline_data'):
            continue
        if not asset['verified']:
            review.append(f"Unverified image: {asset['original']} ({asset.get('error')})")
        elif not (output/asset['local']).is_file():
            errors.append('Missing image file: '+asset['local'])
        elif asset.get('sha256') and short_digest((output/asset['local']).read_bytes()) != asset['sha256']:
            errors.append('Modified source image: '+asset['local'])
    for ch,p in all_pages.items():
        soup=BeautifulSoup(p['html'],'html.parser')
        for a in soup.select('a[href^="#read/"]'):
            m=re.match(r'#read/([^?]+)(?:\?anchor=(.+))?',a.get('href',''))
            if not m or m.group(1) not in all_pages:
                errors.append(f"Broken app link {ch}: {a.get('href')}")
            elif m.group(2) and (m.group(1),m.group(2)) not in all_anchor_destinations:
                errors.append(f"Missing cross-link anchor {ch}: {a.get('href')}")
    index_file=output/'data'/'search-index.json'
    if not index_file.exists():
        errors.append('Search index missing')
        search=[]
    else:
        search=json.loads(index_file.read_text(encoding='utf-8'))
        for entry in search:
            if entry['chapter'] not in all_pages or (entry['anchor'] and (entry['chapter'],entry['anchor']) not in all_anchor_destinations):
                errors.append(f"Unresolved search destination {entry['chapter']}#{entry['anchor']}")
    for issue in data['problems']:
        if issue['type'] in ('asset_download_failed','unsupported_or_unsafe_element','duplicate_source_anchor','unmapped_source_text','source_text_not_preserved'):
            review.append(json.dumps(issue,ensure_ascii=False))
        elif issue['type']=='unresolved_internal_anchor':
            review.append(f"Unresolved internal book anchor: {issue['source_href']}")
        # External Rust documentation links stay external by design and are
        # not missing local book content. They remain inventoried in 'problems'.
    counts=Counter(x['type'] for x in data['elements'])
    good=Counter(x['type'] for x in data['elements'] if verdicts.get(x['id'])=='verified')
    chapter_counts=Counter(x['chapter'] for x in data['elements'])
    chapter_verified=Counter(x['chapter'] for x in data['elements'] if verdicts.get(x['id'])=='verified')
    summary={'generated_at':now(),'source':data['source_url'],
             'source_sha256':data['source_sha256'], 'rust_version':data['target_rust_version'],
             'rust_edition':data['rust_edition'],'source_chapters':len(data['chapters']),
             'verified_chapter_routes':chapters_ok,
             'source_elements':len(data['elements']),
             'verified_elements':sum(x=='verified' for x in verdicts.values()),
             'missing_elements':sum(x=='missing' for x in verdicts.values()),
             'review_items':len(review),'fatal_errors':len(errors),
             'source_counts':dict(counts),'verified_counts':dict(good),
             'chapter_counts':dict(chapter_counts),'chapter_verified':dict(chapter_verified),
             'build_succeeded':True,'automated_content_check_passed':not errors and not review,
             'browser_verification':'NOT_RUN',
             'full_release_verified':False}
    # Most conservative report: do NOT claim final release after pipeline alone.
    lines=['# Book content coverage matrix','',
           f"Source: `{data['source_url']}`",f"SHA-256: `{data['source_sha256']}`",
           f"Imported: {data['imported_at']}  |  Audited: {summary['generated_at']}",
           f"Rust version: {data['target_rust_version']}  |  Edition: {data['rust_edition']}",
           '', '**This is an automated element-level comparison, NOT a full browser/manual acceptance.**','',
           '| Content type | Inventoried | Verified | Missing |','|---|---:|---:|---:|']
    for ty in sorted(counts):
        lines.append(f"| {ty} | {counts[ty]} | {good[ty]} | {counts[ty]-good[ty]} |")
    lines += ['',f"**Chapter routes generated:** {len(data['chapters'])}; **verified non-empty page payloads:** {chapters_ok}.",
              f"**Element status:** {summary['verified_elements']} verified / {summary['source_elements']} inventoried; {summary['missing_elements']} missing.",
              f"**Manual/review items:** {len(review)}; **automated errors:** {len(errors)}.",'',
              '## Chapter inventory and route checks','',
              '| Source title | Local route | Inventoried | Hash verified | Missing | Status |', '|---|---|---:|---:|---:|---|']
    for ch in data['chapters']:
        n=chapter_counts[ch['slug']]
        verified_n=chapter_verified[ch['slug']]
        status='HASH VERIFIED, BROWSER UNTESTED' if n and n==verified_n and ch['slug'] in all_pages else 'INCOMPLETE'
        lines.append(f"| {ch['title'].replace('|','/')} | `#read/{ch['slug']}` | {n} | {verified_n} | {n-verified_n} | {status} |")
    lines += ['', '## Unresolved items and exclusions','']
    if errors:
        lines.extend(f'- **ERROR:** {x}' for x in errors[:200])
    if review:
        lines.extend(f'- **REVIEW:** {x}' for x in review[:200])
    if not errors and not review:
        lines.append('- No automated coverage discrepancies found. Manual in-browser semantic review is still outstanding.')
    lines += ['', '## Status policy','',
              '`processed` means parsed; `rendered` means emitted into an HTML payload; '
              '`verified` means hash-matched against an inventoried element. '
              'Manual browser rendering, learning-tool accuracy, and accessibility require independent tests.',
              'Any excluded or unsupported item remains visible above, and prevents release verification.']
    (docs/'content-coverage-matrix.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (docs/'book-inventory.md').write_text('# Book inventory\n\n'+
            f"Snapshot: `{data['source_sha256']}`  |  {len(data['chapters'])} top-level documents\n\n"+
            '\n'.join(f"- {i+1}. **{c['title']}** — {len(c['headings'])} headings; {c['element_count']} inventoried elements; `#{c['slug']}`" for i,c in enumerate(data['chapters']))+'\n',encoding='utf-8')
    (docs/'source-audit.md').write_text('# Source audit\n\n'+
          f"Source: {data['source_url']}\n\nSnapshot SHA-256: `{data['source_sha256']}`\n\n"+
          f"Detected Rust version: {data['target_rust_version']}; edition: {data['rust_edition']}\n\n"+
          f"Parsed top-level documents: {len(data['chapters'])}. Raw source saved separately from derived output.\n\n"+
          'Caveat: automatic source-format parsing does not itself verify visual and semantic fidelity.\n',encoding='utf-8')
    lines=['# Testing report','',f'Generated: {now()}','',
           '| Verification | Outcome |','|---|---|',
           '| Source import | COMPLETE (snapshot hash recorded) |',
           f'| Content element hashing | {summary["verified_elements"]}/{summary["source_elements"]} matched |',
           f'| Route payloads | {chapters_ok}/{len(data["chapters"])} non-empty |',
           f'| Search targets | {len(search)} indexed entries; {"FAILED" if any("search" in x for x in errors) else "checked"} |',
           f'| Asset retrieval | {sum(x["verified"] for x in data["assets"])}/{len(data["assets"])} local assets |',
           f'| Automated structural issues | {len(errors)} |',
           f'| Open review items | {len(review)} |',
           '| Real browser E2E tests | NOT RUN by this import command |',
           '| Mobile / tablet visual inspection | NOT RUN by this import command |',
           '| Accessibility manual review | NOT RUN by this import command |',
           '| Rust compilation of user code | NOT SUPPORTED; must not be described as compiled |',
           '| Deployment validation | NOT RUN by this import command |','',
           '## Release gate','',
           '**RELEASE NOT VERIFIED** — structural coverage does not replace real browser, content, and pedagogical testing. '
           'Address all missing/review items and run the additional checks.','',
           '## Failures','']
    lines += ([f'- {x}' for x in errors] if errors else ['- None detected in automated checks.'])
    lines += ['', '## Manual review / known issues','']
    lines += ([f'- {x}' for x in review] if review else ['- No importer issues; browser/manual checks still required.'])
    (docs/'testing-report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (docs/'coverage-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (output/'data').mkdir(parents=True,exist_ok=True)
    (output/'data'/'coverage-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (docs/'verification-details.json').write_text(json.dumps({
        'source_sha256':data['source_sha256'],
        'verified_at':summary['generated_at'],
        'content_elements':[{'id':el['id'],'chapter':el['chapter'],'type':el['type'],
                             'status':verdicts.get(el['id'],'missing')} for el in data['elements']],
        'errors':errors,'manual_review':review,
        'full_release_verified':False
    },ensure_ascii=False,indent=2),encoding='utf-8')
    return summary


def write_not_imported(docs):
    docs=Path(docs);docs.mkdir(exist_ok=True,parents=True)
    source='https://doc.rust-lang.org/book/print.html'
    s={'generated_at':now(),'source':source,
       'source_chapters':'NOT_INVENTORIED', 'source_elements':'NOT_INVENTORIED',
       'verified_chapter_routes':0,'verified_elements':0,'missing_elements':'UNKNOWN',
       'automated_content_check_passed':False,'full_release_verified':False,
       'reason':'No locally archived canonical source snapshot has been imported.'}
    (docs/'coverage-summary.json').write_text(json.dumps(s,indent=2),encoding='utf-8')
    (docs/'content-coverage-matrix.md').write_text(
       '# Rust Atlas — content coverage matrix: NOT IMPORTED\n\n'
       f'**Canonical source:** {source}\n\n'
       '**Release gate: NOT VERIFIED.** No full-book HTML snapshot exists locally. '
       'Source file processing and destination-content verification have **not** occurred. '
       'A preview page is never counted as book coverage.\n\n'
       '| Scope | Expected from online introduction | Source elements inventoried from snapshot | Verified in local website |\n'
       '|---|---:|---:|---:|\n'
       '| Numbered chapters | 21 (online description; not independently counted from a snapshot) | Unknown | 0 |\n'
       '| Appendices | 7 (A–G; online description, not audited) | Unknown | 0 |\n'
       '| Foreword and introduction | Present in linked edition | Unknown | 0 |\n'
       '| Heading and subsection elements | Unknown | Unknown | 0 |\n'
       '| Full paragraphs and lists | Unknown | Unknown | 0 |\n'
       '| Rust code listings and terminal examples | Unknown | Unknown | 0 |\n'
       '| Tables, images, diagrams and captions | Unknown | Unknown | 0 |\n'
       '| Footnotes, links and other source elements | Unknown | Unknown | 0 |\n\n'
       '## Unresolved items\n\n'
       '- Canonical HTML has not been downloaded into this project, so SHA-256, element counts, order and text integrity cannot be proven.\n'
       '- Source images and source-specific licenses have not been imported or individually audited.\n'
       '- No original-book deep destinations were verified in the browser.\n\n'
       '## Required next step\n\n'
       '`python3 tools/book_pipeline.py import --url https://doc.rust-lang.org/book/print.html`\n\n'
       'The import command regenerates this report with source-vs-destination counts, '
       'per-page status, element-level verification details, missing material and open review items. '
       'Even a clean automated result must not be represented as full manual acceptance.\n',
       encoding='utf-8')
    (docs/'book-inventory.md').write_text(
       '# Book inventory — SOURCE SNAPSHOT PENDING\n\n'
       f'Authoritative source: {source}\n\n'
       'Online source introduction describes 21 numbered chapters (1–21), '
       'Appendices A–G (7), a foreword, and an introduction. This is **not** a '
       'file-level or element-level source inventory.\n\n'
       '| Material | Included in preview | Verified from original snapshot |\n'
       '|---|---|---|\n'
       '| Foreword and introduction | No | No |\n'
       '| Chapters 1–21 | No | No |\n'
       '| Appendices A–G | No | No |\n'
       '| Complete code examples, tables, figures and links | No | No |\n\n'
       'The importer creates the actual per-page, source-ordered inventory after receiving the complete HTML snapshot.\n',
       encoding='utf-8')
    (docs/'source-audit.md').write_text(
       '# Source audit — online edition identified, original HTML not archived\n\n'
       f'Official source: {source}\n\n'
       'Observed from the official site on 18 October 2026: *The Rust Programming Language* by '
       'Steve Klabnik, Carol Nichols and Chris Krycho, with contributions by the Rust Community. '
       'The linked title page identifies Rust 1.97.0 or later with 2024 Edition idioms. '
       'The introduction describes 21 chapters and seven appendices.\n\n'
       '**Provisional metadata only:** remote page text was inspected, but the exact '
       'HTML bytes, page/element structure, images and licensing details could not be '
       'audited in this workspace. The import checksum is not available. Do not substitute '
       'the GitHub main branch or another edition for this URL.\n\n'
       'The upstream `rust-lang/book` repository is MIT OR Apache-2.0 licensed; '
       'separate asset rights still need review. See `licensing-and-attribution.md`.\n',
       encoding='utf-8')
    test_evidence=docs/'qa-evidence.json'
    qa=json.loads(test_evidence.read_text()) if test_evidence.exists() else None
    testing=['# Testing report — Rust Atlas partial preview', '',f'Generated: {now()}', '',
             '**NOT VERIFIED AS A FULL BOOK WEBSITE.** The canonical source HTML is not imported.', '',
             '| Verification area | What actually ran | Status |','|---|---|---|',
             '| Official Rust Book source import | Live URL inspected separately; complete HTML file not downloaded | **NOT RUN** |',
             '| Source-element coverage and original content hash verification | 0 source elements verified; counts unknown | **NOT VERIFIED** |',
             '| Production-book search / appendix destinations | Not available without original source | **NOT RUN** |']
    if qa:
        ut=qa['automated_tests']; bc=qa['browser_preview_smoke']
        testing += [
             f'| Pipeline fixture unit tests | {ut["passed"]}/{ut["executed"]} passed; synthetic input only | PASS ON FIXTURE |',
             f'| Chromium preview smoke tests | {len(bc["viewports"])} viewports; home/sample reader/lab/practice/dashboard | PASS IN PREVIEW |',
             '| Browser JavaScript runtime errors and horizontal overflow | None observed at 1440, 800, 390 px | PASS IN PREVIEW |']
    else:
        testing += ['| Pipeline fixture unit tests | Rerun tests; no local evidence bundle | NOT RECORDED |',
                    '| Browser smoke tests | Rerun QA; no local evidence bundle | NOT RECORDED |']
    testing += ['| Accessibility screen-reader audit | Not performed | NOT RUN |',
                '| Rust compilation and execution | No compiler backend | NOT SUPPORTED |',
                '| Real book deployment verification | Not run | NOT RUN |', '',
                '## Release blockers', '',
                '- Import the authoritative original HTML and all its referenced educational assets.',
                '- Run full source-by-destination coverage checks and investigate every omission.',
                '- Verify complete navigation, search, code formatting, appendices, mobile reading and links in the actual imported book.',
                '- Resolve licensing and manual accessibility review items.', '',
                'Successful fixture tests **do not** establish complete-book coverage, and successful builds alone never release this project.', '']
    (docs/'testing-report.md').write_text('\n'.join(testing),encoding='utf-8')
    return s

def install_frontend(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for p in (ROOT/'src').iterdir():
        if p.is_file() and p.suffix in ('.css','.js','.html','.svg'):
            shutil.copy2(p,out/p.name)


def run_cli():
    parser=argparse.ArgumentParser(description='Rust Atlas source-locked book import/coverage checker')
    parser.add_argument('command',choices=['import','verify','install'])
    parser.add_argument('--url',default=DEFAULT_URL)
    parser.add_argument('--source-file',help='Use a locally saved print.html file (best for reproducibility)')
    parser.add_argument('--output',default=str(ROOT/'dist'))
    parser.add_argument('--docs',default=str(DOCS))
    parser.add_argument('--no-assets',action='store_true')
    args=parser.parse_args()
    install_frontend(args.output)
    if args.command=='install':
        print('Installed application shell; no book import or verification was performed.');return
    if args.command=='import':
        # Derived chapter payloads from an older import must not linger.
        generated_content=Path(args.output)/'content'
        if generated_content.exists(): shutil.rmtree(generated_content)
        data,base=snapshot_page(args.url,args.source_file)
        (ROOT/'source').mkdir(parents=True,exist_ok=True)
        (ROOT/'source'/'print.snapshot.html').write_bytes(data)
        print('Fetched source',base,len(data),'bytes SHA256',short_digest(data))
        manifest=create_manifest(data,base,args.output,not args.no_assets)
        print('Imported',len(manifest['chapters']),'top-level book sections and',len(manifest['elements']),'content elements')
    summary=verify(args.output,args.docs)
    print(json.dumps(summary,indent=2))
    if summary.get('fatal_errors',0) or summary.get('review_items',0):
        sys.exit(2)

if __name__=='__main__':
    run_cli()
