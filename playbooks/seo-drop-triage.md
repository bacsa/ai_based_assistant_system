---
id: seo-drop-triage
title: SEO drop triage
owner: marketing
autonomy: 2
triggeredBy:
- seo-organic-drop
- seo-impressions-drop
---

# SEO drop triage

**Done when:** Alert sent to the owner with a ranked cause list, and either a fix is approved or a ticket exists.

## Steps

1. Rule out measurement problems: is Search Console data complete, does analytics show the same drop?
2. Rule out availability: uptime for 7 days, page returns 200, canonical points to itself.
3. Check on-page changes with the crawl diff: title, meta, robots, canonical, H1, structured data.
4. Correlate with CMS deployments in the 2 days before the drop.
5. Compare impressions and clicks: both down means ranking or indexing; only clicks down means snippet or CTR.
6. Check whether the drop is site-wide (algorithm update or seasonality).
7. Compose the alert with numbers, ranked causes, evidence and recommended action.
8. Propose the fix: noindex or canonical regression → CMS tool with dry run → approval card; otherwise create a ticket.
9. Record the episode: cause category, evidence, action, time to detect.
