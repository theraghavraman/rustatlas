from pathlib import Path

p=Path(__file__).resolve().parents[1]/'src'/'app.js'
s=p.read_text()
original=s
s=s.replace("let store=loadStore();", "const EMBEDDED=window.__ATLAS_EMBEDDED || null;\nlet store=loadStore();")
s=s.replace("'Book import pending'", "'Book import pending'")
s=s.replace('`${pct()}% chapters completed`','`${pct()}% sections completed`')
s=s.replace("`${manifest.source_elements??manifest.elements?.length??0} content elements inventoried`", "`${manifest.source_elements??manifest.elements?.length??0} content elements inventoried`")
s=s.replace("`${imported?`${pct()}% of chapters`:'Ready to explore'}`", "`${imported?`${pct()}% of sections`:'Ready to explore'}`")
s=s.replace("${imported?'Imported book pages':'Chapters + appendices in source'}", "${imported?'Book sections including appendices':'Chapters + appendices in source'}")
start=s.index('function sourceStatus(){')
end=s.index('function labRef(',start)
s=s[:start]+'''function sourceStatus(){
 if(!imported)return '<span class="pill pill-amber">PREVIEW MODE · BOOK NOT IMPORTED</span>';
 return `<span class="pill ${coverage?.fatal_errors?'pill-amber':'pill-slate'}">FULL RUST BOOK TEXT · ${coverage?.fatal_errors?'CHECK FAILED':'STRUCTURALLY VERIFIED'}</span>`;
}
function banner(){
 if(!imported)return `<div class="status-banner" role="status"><span class="status-symbol">!</span><div>Rust Book source is not imported yet. <a href="${SOURCE}">Official book ↗</a></div></div>`;
 const total=coverage?.source_elements??manifest.source_elements??0;
 const checked=coverage?.verified_elements??0;
 const assets=coverage?.review_items??0;
 return `<div class="status-banner" role="status"><span class="status-symbol">${coverage?.fatal_errors?'!':'✓'}</span><div><b>The complete supplied book text is here:</b> ${checked.toLocaleString()} / ${total.toLocaleString()} mapped text, code and structure elements passed automated integrity checks. ${assets?`${assets} original images are linked to the official source and are not bundled for offline use.`:'All referenced media audited.'} This is distinct from final manual accessibility and image verification. <a href="#read">Explore all sections →</a></div></div>`;
}
''' + s[end:]
s=s.replace("async function getPage(chapter){if(demo", "async function getPage(chapter){if(EMBEDDED?.pages?.[chapter.slug])return EMBEDDED.pages[chapter.slug];if(demo")
s=s.replace("async function getIndex(){if(searchDocs)return searchDocs;", "async function getIndex(){if(searchDocs)return searchDocs;if(EMBEDDED?.search){searchDocs=EMBEDDED.search;return searchDocs;}")
old="async function init(){try{const response=await fetch('book-manifest.json');"
new="async function init(){if(EMBEDDED?.manifest){manifest=EMBEDDED.manifest;coverage=EMBEDDED.coverage??null;imported=Boolean(manifest.chapters?.length&&(manifest.source_elements||manifest.elements?.length));render();return;}try{const response=await fetch('book-manifest.json');"
assert old in s
s=s.replace(old,new)
s=s.replace("function enhanceCode(){main.querySelectorAll('.book-content pre').forEach", "function enhanceCode(){enhanceImages();main.querySelectorAll('.book-content pre').forEach")
needle='async function copyText(s)'
pos=s.index(needle)
s=s[:pos]+'''function enhanceImages(){
 main.querySelectorAll('.book-content img').forEach(img=>{
  if(img.dataset.atlasImageEnhanced)return;
  img.dataset.atlasImageEnhanced='1';
  const figure=img.closest('figure');
  const label=img.getAttribute('alt')||'Original Rust Book illustration';
  const official=img.src;
  const fallback=document.createElement('span');
  fallback.className='source-image-fallback';
  fallback.hidden=true;
  const heading=document.createElement('strong');heading.textContent='Figure from the Rust Book';
  const description=document.createElement('span');description.textContent=label;
  const link=document.createElement('a');link.href=official;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Open original figure ↗';
  fallback.append(heading,description,link);
  img.insertAdjacentElement('afterend',fallback);
  img.addEventListener('error',()=>{img.hidden=true;fallback.hidden=false},{once:true});
  if(img.complete&&img.naturalWidth===0){img.hidden=true;fallback.hidden=false}
 });
}
''' + s[pos:]
if s==original:raise RuntimeError('No patch applied')
p.write_text(s)
print('Updated app for bundled and standalone book content. Bytes:',len(s))
