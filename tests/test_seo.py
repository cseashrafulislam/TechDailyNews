import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TOKEN = '1qQMCUHekjvhhgPfjwAEE-Zfl5rO4Td-0qGCgL5AGAs'

class SeoTests(unittest.TestCase):
    def test_homepage_verification(self):
        html = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertIn(f'<meta name="google-site-verification" content="{TOKEN}">', html)
        self.assertIn('https://techdailynews.pages.dev/', html)
        self.assertIn('application/ld+json', html)

    def test_contact_link(self):
        html = (ROOT / 'contact/index.html').read_text(encoding='utf-8')
        self.assertIn('https://ashraful.pages.dev/', html)
        self.assertIn('rel="noopener noreferrer"', html)

    def test_sitemap(self):
        root = ET.parse(ROOT / 'sitemap.xml').getroot()
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [x.text for x in root.findall('.//s:loc', ns)]
        self.assertIn('https://techdailynews.pages.dev/', urls)
        self.assertIn('https://techdailynews.pages.dev/contact/', urls)
        self.assertIn('https://techdailynews.pages.dev/category/ai/', urls)
        self.assertEqual(len(urls), 10)

    def test_robots(self):
        robots = (ROOT / 'robots.txt').read_text(encoding='utf-8')
        self.assertIn('Sitemap: https://techdailynews.pages.dev/sitemap.xml', robots)

if __name__ == '__main__':
    unittest.main()
