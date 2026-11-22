#!/usr/bin/env python3
"""Refresh TechDaily News from public RSS/Atom metadata without third-party packages."""
from __future__ import annotations

import concurrent.futures
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
from scripts.geography import country_tags, CODES
OUTPUT = BASE / 'data' / 'news.json'
DAYS = 21
MAX_STORIES = 360
SOURCE_LIMIT = 35
TIMEOUT = 15
MAX_BYTES = 1_500_000
ATOM = '{http://www.w3.org/2005/Atom}'
MEDIA = '{http://search.yahoo.com/mrss/}'
CONTENT = '{http://purl.org/rss/1.0/modules/content/}'

# Publisher, publicly available RSS or Atom URL, default news category.
FEEDS = [
    ('The Verge', 'https://www.theverge.com/rss/index.xml', 'Tech'),
    ('The Verge AI', 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml', 'AI'),
    ('TechCrunch', 'https://techcrunch.com/feed/', 'Tech'),
    ('TechCrunch AI', 'https://techcrunch.com/category/artificial-intelligence/feed/', 'AI'),
    ('TechCrunch Startups', 'https://techcrunch.com/category/startups/feed/', 'Startups'),
    ('TechCrunch Venture', 'https://techcrunch.com/category/venture/feed/', 'Funding'),
    ('TechCrunch Security', 'https://techcrunch.com/category/security/feed/', 'Cybersecurity'),
    ('EU-Startups', 'https://www.eu-startups.com/feed/', 'Startups'),
    ('Tech Funding News', 'https://techfundingnews.com/feed/', 'Funding'),
    ('Ars Technica', 'https://feeds.arstechnica.com/arstechnica/index', 'Tech'),
    ('Ars Technica AI', 'https://arstechnica.com/ai/feed/', 'AI'),
    ('Engadget', 'https://www.engadget.com/rss.xml', 'Gadgets'),
    ('Wired', 'https://www.wired.com/feed/rss', 'Tech'),
    ('MIT Technology Review', 'https://www.technologyreview.com/feed/', 'Science'),
    ('MIT Technology Review AI', 'https://www.technologyreview.com/topic/artificial-intelligence/feed', 'AI'),
    ('The Hacker News', 'https://feeds.feedburner.com/TheHackersNews', 'Cybersecurity'),
    ('Hacker News', 'https://hnrss.org/frontpage', 'Software'),
    ('GitHub Blog', 'https://github.blog/feed/', 'Software'),
    ('Cloudflare Blog', 'https://blog.cloudflare.com/rss/', 'Software'),
    ('VentureBeat', 'https://venturebeat.com/feed/', 'Tech'),
    ('The Verge Science', 'https://www.theverge.com/rss/science/index.xml', 'Science'),
    ('Digi Bangla Local', 'https://digibanglatech.news/rss/category/local-40', 'Tech'),
    ('Digi Bangla English', 'https://digibanglatech.news/rss/category/english', 'Tech'),
    ('The Business Standard ICT', 'https://www.tbsnews.net/tech/ict/rss.xml', 'Tech'),
]
KEYWORDS = [
    ('Funding', ('funding', 'fundraise', 'venture capital', 'series a', 'series b', 'series c', 'investment', 'valuation', 'ipo', 'seed round', 'raised $', 'raises $')),
    ('Cybersecurity', ('ransomware', 'cybersecurity', 'cyberattack', 'malware', 'breach', 'phishing', 'hackers', 'zero-day', 'vulnerability')),
    ('AI', ('artificial intelligence', 'generative ai', 'chatgpt', 'openai', 'anthropic', 'gpt-', 'llm', 'language model', 'ai model', 'ai agents', 'gemini ai')),
    ('Startups', ('startup', 'founder', 'y combinator', 'accelerator', 'entrepreneur')),
    ('Gadgets', ('iphone', 'smartphone', 'headphones', 'smartwatch', 'macbook', 'laptop', 'wearables', 'android phone')),
    ('Science', ('nasa', 'spacecraft', 'quantum', 'astronomy', 'science', 'researchers')),
    ('Software', ('software', 'developer', 'github', 'programming', 'cloud computing', 'open source', 'kubernetes', 'python ')),
]


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignore = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script'):
            self.ignore += 1

    def handle_endtag(self, tag):
        if tag in ('style', 'script') and self.ignore:
            self.ignore -= 1

    def handle_data(self, text):
        if not self.ignore:
            self.parts.append(text)


def clean(value, limit=240):
    parser = PlainText()
    parser.feed(str(value or ''))
    result = re.sub(r'\s+', ' ', html.unescape(' '.join(parser.parts))).strip()
    if len(result) > limit:
        result = result[:limit - 1].rsplit(' ', 1)[0].strip(' .,:;') + '…'
    return result


def canonical(value):
    try:
        parsed = urlsplit(html.unescape(str(value or '').strip()))
        if parsed.scheme.lower() not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
            return ''
        if parsed.hostname.lower() in ('localhost', '127.0.0.1'):
            return ''
        query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                 if not k.lower().startswith('utm_') and k.lower() not in {'fbclid', 'gclid', 'ref', 'source'}]
        return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(),
                           parsed.path.rstrip('/') or '/', urlencode(query), ''))
    except (TypeError, ValueError):
        return ''


def date_utc(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (ValueError, TypeError, IndexError):
        try:
            parsed = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
        except (ValueError, TypeError, AttributeError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def category_for(title, description, default):
    if default != 'Tech':
        return default
    subject = (title + ' ' + description).lower()
    for category, terms in KEYWORDS:
        if any(term in subject for term in terms):
            return category
    return 'Tech'


def image_from(entry):
    for path in (MEDIA + 'thumbnail', MEDIA + 'content', 'enclosure'):
        for element in entry.findall(path):
            raw = (element.attrib.get('url') or '').strip()
            if path == 'enclosure' and 'image' not in element.attrib.get('type', ''):
                continue
            url = canonical(raw)
            if url.startswith('https://'):
                return url
    return None


def one_article(title, summary, url, date, source, default, now, image=None):
    title = clean(title, 210)
    summary = clean(summary, 260)
    url = canonical(url)
    timestamp = date_utc(date)
    if not title or not url or not timestamp:
        return None
    if timestamp < now - timedelta(days=DAYS) or timestamp > now + timedelta(hours=24):
        return None
    result = {
        'id': hashlib.sha256(url.encode('utf-8')).hexdigest()[:16],
        'title': title, 'summary': summary, 'url': url,
        'source': source, 'category': category_for(title, summary, default),
        'countries': country_tags(title, source),
        'publishedAt': timestamp.isoformat(timespec='seconds').replace('+00:00', 'Z'),
    }
    if image:
        result['image'] = image
    return result


def parse_feed(raw, source, default, now):
    document = ET.fromstring(raw)
    result = []
    if document.tag == ATOM + 'feed':
        entries = document.findall(ATOM + 'entry')
        for entry in entries:
            link = ''
            for item in entry.findall(ATOM + 'link'):
                if item.get('rel') in (None, 'alternate') and item.get('href'):
                    link = item.get('href')
                    break
            item = one_article(
                entry.findtext(ATOM + 'title'),
                entry.findtext(ATOM + 'summary') or entry.findtext(ATOM + 'content'),
                link,
                entry.findtext(ATOM + 'published') or entry.findtext(ATOM + 'updated'),
                source, default, now, image_from(entry))
            if item:
                result.append(item)
    else:
        for entry in document.findall('.//item'):
            item = one_article(
                entry.findtext('title'),
                entry.findtext('description') or entry.findtext(CONTENT + 'encoded'),
                entry.findtext('link'),
                entry.findtext('pubDate') or entry.findtext('{http://purl.org/dc/elements/1.1/}date'),
                source, default, now, image_from(entry))
            if item:
                result.append(item)
    return result[:50]


def fetch_one(feed, now):
    source, url, category = feed
    try:
        request = Request(url, headers={
            'User-Agent': 'TechDailyNewsRSS/1.0 (public headline aggregation)',
            'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml',
        })
        limit = 10_000_000 if source.startswith('Digi Bangla') else MAX_BYTES
        with urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read(limit + 1)
        if len(raw) > limit:
            raise ValueError('RSS feed too large')
        return source, parse_feed(raw, source, category, now), None
    except Exception as error:
        return source, [], str(error)


def curate(previous, new, now):
    output = []
    urls = set()
    titles = set()
    per_source = {}
    cutoff = now - timedelta(days=DAYS)
    records = sorted(new + previous, key=lambda item: item.get('publishedAt') or '', reverse=True)
    for article in records:
        if not isinstance(article, dict):
            continue
        url = canonical(article.get('url'))
        title = clean(article.get('title'), 210)
        published = date_utc(article.get('publishedAt'))
        source = clean(article.get('source'), 80)
        if not url or not title or not source or not published or published < cutoff or published > now + timedelta(hours=24):
            continue
        title_key = re.sub(r'[^a-z0-9]', '', title.lower())
        if url in urls or title_key in titles or per_source.get(source, 0) >= SOURCE_LIMIT:
            continue
        item = {
            'id': hashlib.sha256(url.encode()).hexdigest()[:16],
            'title': title,
            'summary': clean(article.get('summary'), 260),
            'source': source,
            'countries': ([c for c in article.get('countries', []) if c in CODES] or country_tags(title, source)),
            'category': article.get('category') if article.get('category') in
                        {'Tech', 'AI', 'Startups', 'Funding', 'Cybersecurity', 'Gadgets', 'Software', 'Science'} else 'Tech',
            'publishedAt': published.isoformat(timespec='seconds').replace('+00:00', 'Z'),
            'url': url,
        }
        image = canonical(article.get('image'))
        if image.startswith('https://'):
            item['image'] = image
        output.append(item)
        urls.add(url)
        titles.add(title_key)
        per_source[source] = per_source.get(source, 0) + 1
        if len(output) >= MAX_STORIES:
            break
    return output


def main():
    now = datetime.now(timezone.utc)
    try:
        previous = json.loads(OUTPUT.read_text(encoding='utf-8')).get('articles', [])
    except (OSError, json.JSONDecodeError, AttributeError):
        previous = []
    fresh = []
    succeeded = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        for source, articles, error in pool.map(lambda feed: fetch_one(feed, now), FEEDS):
            if error:
                print('[WARN] ' + source + ': ' + error, file=sys.stderr)
            else:
                print('[OK] ' + source + ': ' + str(len(articles)) + ' articles')
                fresh.extend(articles)
                succeeded += 1
    merged = curate(previous, fresh, now)
    if succeeded == 0 or not merged:
        print('[ERROR] No usable RSS update. Existing news.json preserved.', file=sys.stderr)
        return 1
    payload = {
        'generatedAt': now.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'status': 'live',
        'successfulFeeds': succeeded,
        'totalFeeds': len(FEEDS),
        'articleCount': len(merged),
        'articles': merged,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix('.json.tmp')
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(OUTPUT)
    print('[DONE] ' + str(len(merged)) + ' stories from ' + str(succeeded) + '/' + str(len(FEEDS)) + ' working feeds.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
