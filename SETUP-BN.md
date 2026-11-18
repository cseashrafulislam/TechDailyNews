# TechDaily News — বাংলা সেটআপ

**GitHub:** https://github.com/cseashrafulislam/TechDailyNews  
**Website:** https://techdailynews.pages.dev/

আপনার Cloudflare Pages Git Integration ইতিমধ্যে `main` branch-এর সাথে connected আছে। তাই আর Direct Upload বা Wrangler API token লাগবে না।

## Cloudflare Build Configuration

- Build command: **খালি**
- Build output directory: **`.` অথবা root** (বর্তমানে ফাঁকা থাকলে Cloudflare repository root ধরে)
- Root directory: **খালি**
- Production branch: **main**
- Automatic deployments: **Enabled**

কারণ project-এর `index.html` repository root-এই রয়েছে, `public/` folder-এর ভেতরে নয়।

## Live News Update

GitHub → Actions → **Refresh TechDaily News** → Run workflow চাপলে এখনই RSS news সংগ্রহ হবে। GitHub Actions প্রতি ৬ ঘণ্টায় নিজে run করবে: বাংলাদেশ সময় সকাল ৬:১৭, দুপুর ১২:১৭, সন্ধ্যা ৬:১৭, রাত ১২:১৭।

Workflow প্রথমে news সংগ্রহ করবে, তারপর `data/news.json` ফাইলে commit করবে। GitHub push-এর পরে Cloudflare Pages নতুন deployment শুরু করবে।

কোনো action-এ push permission error দেখালে GitHub → Settings → Actions → General → Workflow permissions-এ Read and write permissions নিশ্চিত করুন।

RSS source সাময়িকভাবে বন্ধ থাকলে আগের news data থাকবে। Cloudflare Pages → Deployments থেকে Success দেখুন।