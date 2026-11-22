import unittest
from scripts.geography import CODES, country_tags
from scripts import update_news as news

class CountryEditionTests(unittest.TestCase):
    def test_country_options(self):
        self.assertEqual(len(CODES), 10)
        self.assertEqual(set(CODES), {'BD','IN','US','GB','CA','AU','DE','AE','SG','JP'})

    def test_geography(self):
        self.assertEqual(country_tags('New AI model launches'), ['WORLD'])
        self.assertEqual(country_tags('Dhaka technology conference'), ['BD'])
        self.assertEqual(country_tags('India and US technology summit'), ['IN','US'])
        self.assertEqual(country_tags('Global startup investors in Japan'), ['JP'])
        self.assertEqual(country_tags('New broadband project', 'Digi Bangla Local'), ['BD'])

    def test_curation_preserves_tags(self):
        from datetime import datetime, timezone
        now=datetime.now(timezone.utc)
        article=news.one_article('Dhaka robotics startup raises funds','Funding for technology',
            'https://example.com/unique-bd-story',now.strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'Publisher','Tech',now)
        self.assertEqual(article['countries'],['BD'])
        curated=news.curate([], [article], now)
        self.assertEqual(curated[0]['countries'],['BD'])

if __name__=='__main__':
    unittest.main()
