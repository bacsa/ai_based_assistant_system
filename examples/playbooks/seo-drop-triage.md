---
id: seo-drop-triage
version: 1
owner: marketing
triggered_by: [seo-organic-drop, seo-impressions-drop, seo-index-coverage-drop]
tools_allowed:
  - metrics.query
  - seo.get_search_console_series
  - analytics.get_sessions
  - crawler.fetch_page
  - crawler.diff_page
  - pagespeed.get_core_web_vitals
  - deploy.list_recent
  - uptime.status
  - kb.search
  - slack.post_message
  - ticketing.create_issue
  - cms.remove_noindex        # needs approval
  - cms.set_page_meta         # needs approval
autonomy_level: 2
done_when: alert sent to owner with a ranked cause list, and either a fix is approved or a ticket exists
---

# SEO drop triage

## Preconditions
- The task carries: landing page, baseline value, current value, ratio, days persisting.
- Pre-fetched context: impressions series, page diff for 7 days, CMS deployments for 7 days.

## Steps

1. **Rule out measurement problems.**
   - Is the Search Console data complete for the period (the last 2 days are provisional)?
   - Does `analytics.get_sessions` for the same page show the same drop? If analytics is
     flat while Search Console dropped, suspect a tracking/reporting issue, not SEO.

2. **Rule out availability.**
   - `uptime.status(site)` for the last 7 days; `crawler.fetch_page(url)` must return 200,
     not 3xx/4xx/5xx, and the canonical must point to itself.

3. **Check on-page changes.**
   - Read `crawler.diff_page`: changes to `<title>`, meta description, `robots`/`noindex`,
     canonical, H1, hreflang, structured data, or large content removals.
   - Correlate with `deploy.list_recent(system=cms)`: a deployment inside 2 days before
     the drop started is a prime suspect.

4. **Check impressions vs clicks.**
   - Impressions down too → ranking/indexing problem (steps 3, 5).
   - Impressions flat, clicks down → snippet/CTR problem (title or meta changed, rich
     result lost) or a competitor took a SERP feature.

5. **Check wider scope.**
   - Is the drop site-wide (`metrics.query` over all key pages)? Site-wide + no change on
     our side → likely algorithm update or seasonal; check the KB for past incidents and
     the "seasonality" note for this page.

6. **Technical health.**
   - `pagespeed.get_core_web_vitals(url)`: did any metric move to "poor"?

7. **Compose the alert** (to `owner_role`, channel from people.yaml):
   - one-line summary with numbers, a ranked list of likely causes with evidence, the
     recommended action, and links to the task and the rule explanation.

8. **Propose the fix.**
   - For a `noindex` or canonical regression: propose `cms.remove_noindex` / `cms.set_page_meta`
     with `dry_run` output attached → approval card to `seo_owner`.
   - Otherwise create a ticket with `ticketing.create_issue` assigned to the page owner.

9. **Record the episode**: cause category, evidence, action taken, time-to-detect.

## Decision points for a human
- Any change to live page content or metadata.
- Declaring "algorithm update, no action" – the assistant may suggest it, the owner confirms.
