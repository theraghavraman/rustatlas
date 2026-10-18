#!/usr/bin/env python3
"""Serve the actual compiled dist/ and verify all 111 source routes are retrievable."""
from pathlib import Path
import json,threading,urllib.request
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler

root=Path(__file__).resolve().parents[1]
static=root/'dist'
manifest=json.loads((static/'book-manifest.json').read_text())
class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kwargs):super().__init__(*a,directory=str(static),**kwargs)
    def log_message(self,*a):return

server=ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f'http://127.0.0.1:{server.server_port}/'
ok=[];errors=[]
urls=['index.html','app.js','concepts.js','practice.js','styles.css','book-manifest.json','data/search-index.json','data/coverage-summary.json']+[c['path'] for c in manifest['chapters']]
try:
    for path in urls:
        try:
            with urllib.request.urlopen(base+path,timeout=6) as rsp:
                data=rsp.read()
                assert rsp.status==200 and len(data)>0,(rsp.status,len(data))
                if path.startswith('content/'):
                    payload=json.loads(data)
                    assert payload['html'].strip()
            ok.append(path)
        except Exception as e:errors.append({'path':path,'error':str(e)})
finally:
    server.shutdown();server.server_close();thread.join(timeout=5)
report={'source':'actual static dist/ via local Python HTTP server','verified_resources':len(ok),'expected_resources':len(urls),
        'source_chapters':len(manifest['chapters']),'errors':errors,'status':'PASS' if not errors else 'FAIL'}
(root/'docs'/'http-delivery-evidence.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if errors:raise SystemExit(1)
