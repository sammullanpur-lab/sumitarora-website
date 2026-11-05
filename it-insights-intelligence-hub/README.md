# IT Insights — Technology Intelligence Hub

## What's new
- Premium **Technology Intelligence** section on homepage with featured original writing, editorial perspective, latest industry briefing and live CISA KEV entries.
- Dedicated `news.html` with Microsoft, Fortinet, Cybersecurity and Infrastructure & AI filters.
- `content/news.json` snapshot with honest "not configured" state; **no fabricated news**.
- Optional GitHub Actions updater for verified source headlines (every 6 hours).

## Preview locally
Open the extracted folder in VS Code, start Live Server on `index.html`, then browse the homepage and `news.html`. File URLs (`file://`) cannot fetch JSON.

## Enable automatic news (one-time)
1. Put this entire site in a GitHub repository. In Netlify, connect the **existing** site to that repository (Site configuration → Build & deploy → Continuous deployment / Link repository). Set publish directory to repository root and no build command.
2. Commit `.github/workflows/update-news.yml` and `scripts/update_news.py` (already included).
3. In GitHub → Actions, enable workflows. Run **Update technology briefing** manually once, or wait for the scheduled run. GitHub Actions must have permission to write repository contents (Settings → Actions → General → Workflow permissions → Read and write permissions, or equivalent repo policy).
4. Confirm `content/news.json` is updated and Netlify automatically deploys the commit.
5. If GitHub Actions is unavailable, run `python scripts/update_news.py` on a computer with Internet access, then manually redeploy the resulting folder to Netlify. The browser cannot reliably fetch cross-domain RSS directly due to CORS.

The updater fetches a small set of official public feeds, removes duplicates, and publishes only valid source URLs. Some publishers may change feeds or block requests; those sources are skipped without inventing stories. It keeps the last successful feed snapshot when all sources fail. No API keys are required. This is an optional publishing workflow and **is not active until configured**.

## Important
- Replace placeholder email and LinkedIn in `content/site.json` with your real information before deployment.
- Preserve your existing `content/site.json` and `content/articles.json` when upgrading from an earlier version.
- Use the existing `editor.html` locally to edit your original articles. Do not publicly deploy the editor if you don't need it.
- The featured original article is selected from `content/articles.json`; it is **not** generated from news automatically.
- CISA KEV is a live client-side request and may be blocked by some networks; fallback link remains.
- Keep full articles on publisher sites; display only headline, attribution, date and a short source-provided excerpt.
- This package is a deployable static site, not an authenticated CMS.
