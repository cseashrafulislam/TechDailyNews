#!/usr/bin/env python3
"""Generate crawlable category pages and XML sitemap/RSS from news.json."""
import json
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://techdailynews.pages.dev"
VERIFY = "1qQMCUHekjvhhgPfjwAEE-Zfl5rO4Td-0qGCgL5AGAs"
SPECS = [
 ("AI", "ai", "Artificial Intelligence News", "Global artificial intelligence news, AI models, research, apps and emerging AI businesses.", "Discover AI launches, research and companies shaping how technology is used."),
 ("Tech", "technology", "Latest Global Technology News", "Global technology news, digital innovation, platform launches and major tech industry developments.", "Follow technology trends, major product updates and the latest digital developments."),
 ("Startups", "startups", "Global Startup News", "Startup news about founders, accelerators, emerging businesses, entrepreneurship and new products.", "Discover startup stories, ambitious founders and emerging tech ventures."),
 ("Funding", "funding", "Startup Funding & Venture Capital News", "Read technology investment, startup funding rounds, venture capital and global deal news.", "Follow startup fundraising, venture investment news and financial developments across tech."),
 ("Cybersecurity", "cybersecurity", "Cybersecurity News & Threat Updates", "Global cybersecurity news covering vulnerabilities, breaches, ransomware and data privacy.", "Stay current with cybersecurity incidents, threat research and digital security trends."),
 ("Gadgets", "gadgets", "Gadgets, Smartphones & Consumer Technology", "The latest gadget launches, smartphones, laptops, wearables and consumer electronics news.", "Explore device announcements, consumer hardware and connected technology."),
 ("Software", "software", "Software, Developers & Cloud News", "Software news covering developer tools, open source, programming, cloud and platforms.", "Keep up with the software ecosystem, cloud tools and developer platforms."),
 ("Science", "science", "Science & Emerging Technology News", "Science and emerging technology news on research, quantum computing, space and discoveries.", "Read about breakthrough research and emerging technologies shaping the future."),
]

def h(value):
    return escape(str(value or ""), quote=True)

def trusted_url(value):
    try:
        p = urlsplit(str(value or ""))
        return value if p.scheme == "https" and p.hostname and not p.username and not p.password else ""
    except ValueError:
        return ""

def make_pages(articles):
    for cat, slug, title, desc, intro in SPECS:
        uri = f"{BASE}/category/{slug}/"
        items = [a for a in articles if a.get("category") == cat and trusted_url(a.get("url"))][:25]
        nav = ''.join(f'<a class="{"active" if c == cat else ""}" href="/category/{s}/">{h(c)}</a>' for c, s, *_ in SPECS)
        cards = ''.join(
            f'<article class="seo-headline"><small>{h(a.get("source"))}</small><h2><a href="{h(a.get("url"))}" target="_blank" rel="noopener noreferrer">{h(a.get("title"))} ↗</a></h2>'
            f'<time datetime="{h(str(a.get("publishedAt", ""))[:10])}">{h(str(a.get("publishedAt", ""))[:10])}</time><p>{h(a.get("summary") or "Read the original reporting.")}</p></article>'
            for a in items
        ) or "<p>No articles yet. Check back soon for updates.</p>"
        schema = json.dumps({"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": uri,
                             "isPartOf": {"@type": "WebSite", "name": "TechDaily News", "url": BASE + "/"}}).replace("<", "\\u003c")
        page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google-site-verification" content="{VERIFY}"><meta name="robots" content="index,follow"><meta name="theme-color" content="#080e19">
<meta name="description" content="{h(desc)}"><link rel="canonical" href="{uri}"><link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta property="og:type" content="website"><meta property="og:site_name" content="TechDaily News"><meta property="og:title" content="{h(title)} | TechDaily News">
<meta property="og:url" content="{uri}"><meta property="og:description" content="{h(desc)}"><meta name="twitter:card" content="summary">
<link rel="stylesheet" href="/styles.css"><title>{h(title)} | TechDaily News</title><script type="application/ld+json">{schema}</script></head>
<body><div class="signal-bar"><div class="wrap signal-inside"><span class="signal-pill"><i></i> GLOBAL TECH RADAR</span><span>TECHDAILY NEWS</span><span>GLOBAL HEADLINES</span></div></div>
<header class="header"><div class="wrap header-inside"><a href="/" class="logo"><span class="logo-symbol">T<span>✦</span></span><span class="logo-words"><b>TECH<span>DAILY</span></b><small>NEWS / WORLDWIDE</small></span></a>
<nav class="seo-nav"><a href="/">Home</a><a href="/category/ai/">AI News</a><a href="/category/startups/">Startups</a><a href="/contact/">Contact</a></nav></div></header>
<main class="wrap seo-page"><nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> / {h(cat)} News</nav>
<span class="eyebrow"><i></i> TECH NEWS COVERAGE</span><h1>{h(title)}<em>.</em></h1><p class="seo-intro">{h(intro)}</p>
<nav class="category-nav" aria-label="Browse all news topics">{nav}</nav>
<span class="eyebrow">LATEST {h(cat.upper())} HEADLINES</span>
<p class="seo-note">News headlines and short summaries link to the original publishers. This page is refreshed automatically.</p>
<div class="seo-headlines">{cards}</div>
<p class="seo-note">{len(items)} recent headlines · <a href="/">View all tech news</a></p></main>
<footer><div class="wrap footer-main"><div class="footer-brand">TECH<span>DAILY</span><small>NEWS</small><p>Global technology briefing.</p></div>
<div class="footer-disclaimer"><nav class="footer-links"><a href="/">Home</a><a href="/contact/">Contact</a><a href="https://ashraful.pages.dev/" target="_blank" rel="noopener noreferrer">Contact Website ↗</a><a href="/sitemap.xml">Sitemap</a></nav><b>INDEPENDENT NEWS AGGREGATOR</b><p>News excerpt rights belong to their original publishers. Follow links to view the original articles.</p></div></div>
<div class="wrap footer-bottom"><span>© TechDaily News</span><span>GLOBAL TECHNOLOGY HEADLINES</span></div></footer></body></html>'''
        target = ROOT / "category" / slug / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")

def write_xml(data, articles):
    stamp = (data.get("generatedAt") or datetime.now(timezone.utc).isoformat())[:10]
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)
    root = ET.Element(f"{{{namespace}}}urlset")
    for path in ["/", "/contact/"] + [f"/category/{s}/" for _, s, *_ in SPECS]:
        obj = ET.SubElement(root, f"{{{namespace}}}url")
        ET.SubElement(obj, f"{{{namespace}}}loc").text = BASE + path
        if path.startswith("/category/"):
            ET.SubElement(obj, f"{{{namespace}}}lastmod").text = stamp
    ET.ElementTree(root).write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    feed = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(feed, "channel")
    for k, v in [("title", "TechDaily News — Global Technology Headlines"), ("link", BASE + "/"),
                 ("description", "Global technology headlines linked to original publishers."), ("language", "en"),
                 ("lastBuildDate", format_datetime(datetime.now(timezone.utc)))]:
        ET.SubElement(channel, k).text = v
    for a in [a for a in articles if trusted_url(a.get("url"))][:40]:
        entry = ET.SubElement(channel, "item")
        for k, v in [("title", a.get("title", "")), ("link", a["url"]), ("description", a.get("summary", "")),
                     ("category", a.get("category", "Tech"))]:
            ET.SubElement(entry, k).text = str(v)
        ET.SubElement(entry, "guid", {"isPermaLink": "true"}).text = a["url"]
        try:
            d = datetime.fromisoformat(str(a.get("publishedAt", "")).replace("Z", "+00:00"))
            ET.SubElement(entry, "pubDate").text = format_datetime(d)
        except ValueError:
            pass
    ET.ElementTree(feed).write(ROOT / "feed.xml", encoding="utf-8", xml_declaration=True)

def main():
    data = json.loads((ROOT / "data" / "news.json").read_text(encoding="utf-8"))
    articles = data.get("articles", [])
    if not isinstance(articles, list):
        raise ValueError("news.json articles must be a list")
    articles = sorted([a for a in articles if isinstance(a, dict)], key=lambda a: a.get("publishedAt", ""), reverse=True)
    make_pages(articles)
    write_xml(data, articles)
    print(f"Created {len(SPECS)} category pages, sitemap.xml and feed.xml from {len(articles)} articles.")

if __name__ == "__main__":
    main()
