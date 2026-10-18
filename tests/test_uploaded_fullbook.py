"""Checks the actual uploaded book, not only the synthetic importer fixture."""
from __future__ import annotations
from pathlib import Path
import json, re, unittest,hashlib
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'source'/'rust-book.original.md'
MANIFEST=ROOT/'dist'/'book-manifest.json'
SUMMARY=ROOT/'docs'/'coverage-summary.json'
STANDALONE=ROOT/'rust-atlas-complete.html'

class TestActualBookCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=SOURCE.read_text(encoding='utf-8')
        cls.manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
        cls.summary=json.loads(SUMMARY.read_text(encoding='utf-8'))
        cls.pages=[json.loads((ROOT/'dist'/p['path']).read_text(encoding='utf-8')) for p in cls.manifest['chapters']]
    def test_every_original_header_exists_in_destination(self):
        headings=len(re.findall(r'^#{1,6}\s',self.text,re.M))
        top=len(re.findall(r'^#\s',self.text,re.M))
        self.assertEqual(headings,628)
        self.assertEqual(top,111)
        self.assertEqual(len(self.manifest['chapters']),top)
        self.assertEqual(self.manifest['source_counts']['heading'],headings)
        self.assertEqual(sum(len(p['headings']) for p in self.pages),headings)
    def test_original_main_sections_and_appendices_all_present(self):
        titles=[p['title'] for p in self.manifest['chapters']]
        for chapter in ('Getting Started','Programming a Guessing Game','Understanding Ownership',
                        'Common Collections','Error Handling','Writing Automated Tests',
                        'Asynchronous Programming','Advanced Features',
                        'Final Project: Building a Multithreaded Web Server'):
            self.assertTrue(any(chapter.lower() in title.lower() for title in titles),chapter)
        self.assertEqual(titles[-7:],['A - Keywords','B - Operators and Symbols','C - Derivable Traits',
            'D - Useful Development Tools','E - Editions','F - Translations of the Book',
            'G - How Rust is Made and “Nightly Rust”'])
    def test_all_book_html_blocks_are_verified(self):
        expected={'heading':628,'code_block':957,'figure':433,'image':28,'table':13}
        for k,n in expected.items():
            self.assertEqual(self.manifest['source_counts'][k],n)
            self.assertEqual(self.summary['verified_counts'][k],n)
        self.assertEqual(self.summary['verified_elements'],self.summary['source_elements'])
        self.assertEqual(self.summary['fatal_errors'],0)
        self.assertEqual(self.summary['missing_elements'],0)
    def test_each_declared_book_page_is_nonempty(self):
        self.assertEqual(len(self.pages),111)
        for page in self.pages:
            self.assertGreater(len(BeautifulSoup(page['html'],'html.parser').get_text(' ',strip=True)),3,page['title'])
    def test_referenced_illustrations_explicitly_flagged_external(self):
        self.assertEqual(len(self.manifest['assets']),28)
        self.assertEqual(self.summary['review_items'],28)
        for asset in self.manifest['assets']:
            self.assertFalse(asset['verified'])
            self.assertTrue(asset.get('remote','').startswith('https://doc.rust-lang.org/book/img/'))
    def test_standalone_file_contains_full_book_payload_and_no_runtime_assets(self):
        html=STANDALONE.read_text(encoding='utf-8')
        self.assertGreater(len(html),4_000_000)
        self.assertIn('window.__ATLAS_EMBEDDED=',html)
        self.assertIn('"source_elements":15609',html)
        self.assertIn('"g-how-rust-is-made-and-nightly-rust"',html)
        self.assertIn('"what-is-ownership-1"',html)
        self.assertNotIn('type="module" src="app.js"',html)
        self.assertNotIn('rel="stylesheet" href="styles.css"',html)
    def test_original_markdown_checksum_is_preserved(self):
        hash_original=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        self.assertEqual(hash_original,'c5a6eefc965ca3ba97f0b776611fc0aaaf1805d00c43d7c5a9e7b15849ea141a')

if __name__=='__main__':unittest.main()
