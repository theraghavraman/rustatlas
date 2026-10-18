import json
import tempfile
import unittest
from pathlib import Path
from tools.book_pipeline import create_manifest,verify,source_chapters
from bs4 import BeautifulSoup
from tools.book_pipeline import short_digest
from unittest.mock import patch

FIXTURE=Path(__file__).parent/'fixtures'/'sample-print.html'

class TestContentPipeline(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.out=self.root/'dist'
        self.docs=self.root/'docs'
        self.raw=FIXTURE.read_bytes()
        self.base=FIXTURE.resolve().as_uri()
    def tearDown(self):self.temp.cleanup()
    def make(self):
        return create_manifest(self.raw,self.base,self.out,download_assets=True)
    def test_source_inventory_has_all_blocks(self):
        c=source_chapters(BeautifulSoup(self.raw,'html.parser'))
        self.assertEqual([x['title'] for x in c],['Fixture Overview','Detailed Example'])
        m=self.make()
        self.assertEqual(len(m['chapters']),2)
        self.assertEqual(m['source_counts']['code_block'],1)
        self.assertEqual(m['source_counts']['table'],1)
        self.assertEqual(m['source_counts']['image'],1)
        self.assertEqual(m['source_counts']['list_item'],2)
        summary=verify(self.out,self.docs)
        self.assertEqual(summary['missing_elements'],0)
        self.assertEqual(summary['verified_elements'],summary['source_elements'])
        self.assertEqual(summary['fatal_errors'],0)
        self.assertEqual(summary['review_items'],0)
        # Automated fidelity does NOT mean that manual release approval occurred.
        self.assertFalse(summary['full_release_verified'])
    def test_resolves_internal_book_link(self):
        m=self.make()
        first=json.loads((self.out/'content'/'fixture-overview.json').read_text())
        self.assertIn('#read/details?anchor=details',first['html'])
    def test_rejects_truncated_text(self):
        self.make()
        page=self.out/'content'/'fixture-overview.json'
        data=json.loads(page.read_text())
        data['html']=data['html'].replace('This is a synthetic parser test','This was silently shortened')
        page.write_text(json.dumps(data))
        result=verify(self.out,self.docs)
        self.assertGreater(result['missing_elements'],0)
        self.assertGreater(result['fatal_errors'],0)
    def test_missing_asset_is_not_verified(self):
        manifest=self.make()
        asset=self.out/manifest['assets'][0]['local']
        asset.unlink()
        result=verify(self.out,self.docs)
        self.assertGreater(result['fatal_errors'],0)
    def test_broken_route_detected(self):
        self.make()
        page=self.out/'content'/'fixture-overview.json'
        data=json.loads(page.read_text())
        data['html']=data['html'].replace('#read/details?anchor=details','#read/does-not-exist?anchor=details')
        page.write_text(json.dumps(data))
        result=verify(self.out,self.docs)
        self.assertGreater(result['fatal_errors'],0)
    def test_rejects_fake_updated_hash_still_missing_against_source_manifest(self):
        self.make()
        page_path=self.out/'content'/'fixture-overview.json'
        data=json.loads(page_path.read_text())
        soup=BeautifulSoup(data['html'],'html.parser')
        paragraph=soup.find('p')
        paragraph.string='Falsely shortened content'
        paragraph['data-atlas-hash']=short_digest('Falsely shortened content')
        data['html']=str(soup)
        page_path.write_text(json.dumps(data))
        result=verify(self.out,self.docs)
        self.assertGreater(result['missing_elements'],0)
        self.assertFalse(result['automated_content_check_passed'])

    def test_rejects_modified_source_snapshot(self):
        self.make()
        path=self.root/'source'/'print.snapshot.html'
        path.parent.mkdir()
        path.write_bytes(b'TAMPERED SOURCE')
        with patch('tools.book_pipeline.ROOT',self.root):
            result=verify(self.out,self.docs)
        self.assertGreater(result['fatal_errors'],0)
        self.assertFalse(result['automated_content_check_passed'])

    def test_mutated_asset_detected(self):
        manifest=self.make()
        path=self.out/manifest['assets'][0]['local']
        path.write_bytes(b'different image')
        result=verify(self.out,self.docs)
        self.assertGreater(result['fatal_errors'],0)

    def test_orphan_book_text_is_not_silently_dropped(self):
        raw=self.raw.replace(b'<h1 id=', b'<span>Unexpected freestanding important content.</span><h1 id=',1)
        manifest=create_manifest(raw,self.base,self.out,download_assets=True)
        self.assertTrue(any(p['type']=='unmapped_source_text' for p in manifest['problems']))
        result=verify(self.out,self.docs)
        self.assertGreater(result['review_items'],0)
        self.assertFalse(result['automated_content_check_passed'])

    def test_coverage_not_imported_is_non_success(self):
        result=verify(self.out,self.docs)
        self.assertFalse(result['automated_content_check_passed'])
        self.assertEqual(result['source_elements'],'NOT_INVENTORIED')

if __name__=='__main__':unittest.main()
