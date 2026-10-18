# rule-engine
**Job:** durable pull consumer (`events/consumers.yaml` → `rule-engine`) that evaluates `rules/*.yaml` as a stream processor with per-key state in Postgres (`rule_state(rule_id, key, baseline, counters, last_fired)`): threshold rules on `seo.metric.collected`, pattern rules on `crawl.page.changed` after `cms.page.published`, state rules on `erp.order.status_changed` plus timers, time rules on `deadline.reminder.due`.
**Outputs:** `*.detected` events with evidence attached, `task.created`; shadow rules emit to `shadow.*`. Writes firing statistics for the console.
**Reference:** `assistant_core.rules` (ported 1:1 from the console; tests in `reference/python/tests/test_rules.py`).
