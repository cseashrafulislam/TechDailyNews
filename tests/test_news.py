import unittest
from datetime import datetime, timedelta, timezone
from scripts import update_news as news

class NewsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.date = self.now.strftime('%a, %d %b %Y %H:%M:%S GMT')

    def test_clean_removes_markup(self):
        self.assertEqual(news.clean('<b>Hello</b> &amp; <script>bad()</script>world'), 'Hello & world')

    def test_url_tracking_removal(self):
        self.assertEqual(news.canonical('https://example.com/post/?utm_source=a&x=1#section'),
                         'https://example.com/post?x=1')

    def test_reject_unsafe_link(self):
        self.assertEqual(news.canonical('javascript:alert(1)'), '')

    def test_rss_parsing(self):
        xml = ('<rss version="2.0"><channel><item><title>AI model launches</title>'
               '<description>New model announced</description>'
               '<link>https://example.com/a</link><pubDate>' + self.date +
               '</pubDate></item></channel></rss>').encode()
        records = news.parse_feed(xml, 'Publisher', 'Tech', self.now)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['category'], 'AI')
        self.assertEqual(records[0]['countries'], ['WORLD'])

    def test_atom_parsing(self):
        updated = self.now.isoformat()
        xml = ('<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>New funding round</title>'
               '<link href="https://example.com/b"/><summary>Funding was announced</summary>'
               '<updated>' + updated + '</updated></entry></feed>').encode()
        records = news.parse_feed(xml, 'Publisher', 'Tech', self.now)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['category'], 'Funding')

    def test_merge_deduplicates(self):
        record = news.one_article('Unique news', 'Summary', 'https://example.com/a',
                                  self.date, 'Publisher', 'Tech', self.now)
        merged = news.curate([record], [record], self.now)
        self.assertEqual(len(merged), 1)

    def test_expired_items_removed(self):
        old = (self.now - timedelta(days=30)).strftime('%a, %d %b %Y %H:%M:%S GMT')
        self.assertIsNone(news.one_article('Old', '', 'https://example.com/old',
                                           old, 'Publisher', 'Tech', self.now))
if __name__ == '__main__':
    unittest.main()
