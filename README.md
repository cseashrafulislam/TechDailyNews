# TechDaily News

**Website:** https://techdailynews.pages.dev/  
**GitHub:** https://github.com/cseashrafulislam/TechDailyNews

An independent, responsive global technology news aggregator on **Cloudflare Pages (Git integration)**. Headline metadata and short excerpts come from publicly available RSS/Atom feeds, with clear source attribution and direct article links.

## Features

- Categories: AI, Tech, Startups, Funding & VC, Cybersecurity, Gadgets, Software, Science.
- A featured lead article, top headlines, fast search, category and date filters, and saved articles.
- Responsive layout, accessible native controls, source links, and optional publisher thumbnails.
- Standard-library Python RSS/Atom collector: 21 feed endpoints, deduplication, source limits, and a rolling 21-day window.
- GitHub Actions runs every six hours, creates an updated `data/news.json`, and commits it to `main`.
- Cloudflare Pages Git integration deploys the updated branch automatically. **No Cloudflare API token, paid news API, database, or Node build required.**

## Your current Cloudflare Pages setup

- Connected repository: `cseashrafulislam/TechDailyNews`
- Production branch: `main`
- Automatic deployments: **enabled**
- Framework preset: **None** / static site
- Build command: **leave blank**
- Build output directory: **repository root (`.`)**
- Root directory: **leave blank**

The published `index.html`, `styles.css`, `app.js`, `favicon.svg`, `_headers`, and `data/news.json` are deliberately at the repository root, so a no-build Cloudflare deployment uses them directly.

## Daily news automation

Workflow file: `.github/workflows/refresh-news.yml`.

Schedule in Bangladesh: **06:17, 12:17, 18:17 and 00:17** (subject to GitHub Actions scheduling delays).

GitHub → **Actions** → **Refresh TechDaily News** → **Run workflow** to force a fresh collection at any time.

On the first push the workflow also runs automatically because its own YAML and script paths changed. It tests the collector, fetches RSS metadata, validates JSON, and commits the news file with the built-in GitHub token. Cloudflare listens to `main` branch commits and deploys the new version.

If you see **403 Resource not accessible by integration** or push permission errors, check the repository's **Settings → Actions → General → Workflow permissions**; the workflow needs **Read and write permissions** for its `contents: write` scope. Organization policy can restrict the setting.

To add sources, edit `FEEDS` in `scripts/update_news.py`. To customize the site, edit `index.html`, `styles.css`, and `app.js`.

## Verification

Run tests: `python -m unittest discover -s tests -v`  
Refresh data: `python scripts/update_news.py`  
Preview locally: `python -m http.server 8000` and open http://localhost:8000

If source feeds are temporarily inaccessible or return no usable articles, the script exits without replacing the previously committed news file. Feed availability and publication frequency depend on the original publishers. Site content is **news aggregation, not original reporting**; publishers retain rights to their content. Review source feed usage policies.

## Deployment caveat

Cloudflare Pages' Git integration is what performs the deployment. Do **not** configure the older Wrangler/Direct Upload deployment workflow; the Cloudflare project is already Git-connected. GitHub's default `GITHUB_TOKEN` suppresses some *new GitHub Actions workflow triggers* from bot commits; this is different from Cloudflare's external Git integration. After the first scheduled update, check Cloudflare's deployment log to confirm bot-commit deployments are arriving.