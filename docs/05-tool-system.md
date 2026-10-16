# 5. Tool system

## 5.1 What a tool is

A tool is a **typed function** the agent can call: a name, a description the model
reads, a JSON schema for the arguments, a JSON schema for the result, and a
classification (read / write, risk level). The agent never touches a database or an API
directly; it only calls tools. This gives you one place to enforce permissions, log
everything, and test.

Expose tools through **MCP (Model Context Protocol)** servers: one server per system,
each with a handful of tools. Any MCP-compatible agent (Claude, Claude Code, others)
can then use them, and the tool catalogue is discoverable at runtime.

## 5.2 Tool taxonomy

| Class | Examples | Default policy |
|-------|----------|----------------|
| **Read – internal data** | `erp.get_invoice`, `crm.list_stale_opportunities`, `hr.list_contract_end_dates` | auto, scoped to the asking user's permissions |
| **Read – external / web** | `seo.get_search_console_series`, `analytics.get_sessions`, `crawler.fetch_page`, `uptime.status` | auto |
| **Knowledge** | `kb.search`, `kb.get_document`, `metrics.query`, `entities.query_sql` (read-only) | auto |
| **Communicate** | `slack.post_message`, `email.send`, `calendar.create_event` | auto for owner-of-task, approve for broadcast |
| **Write – low risk / reversible** | `ticketing.create_issue`, `crm.add_note`, `cms.set_meta_description` | auto after dry-run, or approve in early phases |
| **Write – high risk** | `erp.post_invoice`, `erp.create_payment_reminder`, `cms.publish`, `iam.change_role` | approve, or forbid |
| **Meta** | `tasks.ack`, `tasks.snooze`, `rules.explain`, `approval.request` | auto |

## 5.3 How to expose in-house software

Pick the highest option available per system (from discovery §1.1):

1. **Existing API** – wrap endpoints in a thin MCP server. Do *not* expose the raw API;
   expose the 5–15 business operations people actually do, with business-level names and
   defaults.
2. **Database access** – point a read-only MCP server at a **read replica** with a
   dedicated DB role that can see only the needed views. Pre-write the SQL for the common
   questions as tools; allow free SQL only with a row limit, a timeout and an allow-list
   of tables.
3. **Add a small API to the in-house app** – often the cheapest long-term path for
   write operations: a few internal endpoints with validation and idempotency keys.
4. **File / export based** – scheduled export to CSV/Parquet → loaded into the metrics
   store. Good for reporting signals.
5. **UI automation (browser / RPA)** – last resort for systems with no other path.
   Read-only screenshots and data extraction are acceptable; writes via UI automation
   need approval on every call and a human-visible recording.

## 5.4 Design rules for every tool

- **Narrow and business-named**: `erp.list_overdue_invoices(min_days=30)` beats `erp.query(sql)`.
- **Typed, validated input**, with enums for statuses and IDs, and a short description
  that tells the model *when* to use it and what it returns.
- **Bounded output**: pagination, row limits, summaries for large results; the agent's
  context is finite.
- **Idempotent writes**: accept an `idempotency_key`; repeating a call never duplicates
  an invoice.
- **`dry_run: true` on every write** – returns what *would* change. The guardrail layer
  runs dry-run first and shows it in the approval card.
- **Scoped credentials**: a service account per MCP server with least privilege; where
  the system supports it, act *on behalf of* the requesting user so their permissions apply.
- **Structured errors**: `{error_code, message, retryable}` so the agent can recover sensibly.
- **Observability**: every call logged with arguments (secrets masked), duration,
  result size, caller agent, task id, approval id.
- **Tests**: unit tests against the system's test instance; a contract test the CI runs
  nightly so you notice when the company changes an API.

## 5.5 Tool specification template

Each tool is described in a spec file that both generates the MCP server stub and feeds
the policy rules and the catalogue in the admin console.
See [examples/tools/tool-spec-template.yaml](../examples/tools/tool-spec-template.yaml)
and the SEO example [examples/tools/seo-search-console.yaml](../examples/tools/seo-search-console.yaml).

## 5.6 Starter tool catalogue

A realistic first set (adjust to the discovery inventory):

**Knowledge and meta**
- `kb.search(query, filters)`, `kb.get_document(id)`
- `metrics.query(signal, dimensions, from, to, agg)`
- `entities.sql(query)` (read-only, allow-listed tables)
- `rules.explain(rule_id, at)`, `tasks.ack(task_id)`, `tasks.snooze(task_id, until)`, `approval.request(action, payload)`

**Website / SEO**
- `seo.get_search_console_series(site, dimensions, from, to)`
- `analytics.get_sessions(site, dimensions, from, to)`
- `crawler.fetch_page(url)`, `crawler.diff_page(url, since)`, `crawler.run_site_audit(site)`
- `pagespeed.get_core_web_vitals(url)`
- `uptime.status(site)`, `tls.expiry(domain)`, `dns.records(domain)`
- `cms.get_page_meta(path)`, `cms.set_page_meta(path, …, dry_run)`, `cms.remove_noindex(path, dry_run)`
- `deploy.list_recent(system, days)`

**Business systems (in-house / ERP / CRM)**
- `erp.get_invoice`, `erp.list_overdue_invoices`, `erp.get_period_status`, `erp.create_payment_reminder(dry_run)`
- `crm.list_stale_opportunities`, `crm.add_note`
- `orders.list_by_status`, `orders.time_in_status`
- `hr.list_contract_end_dates`, `hr.list_training_expiry`

**Communication and calendar**
- `slack.post_message`, `slack.post_approval_card`, `email.send`, `email.search`
- `calendar.list_events`, `calendar.create_event`
- `ticketing.create_issue`, `ticketing.update_issue`

## 5.7 Permission flow at call time

```
agent requests tool call
  → schema validation
  → policy rules (doc 04 §4.3): auto | approve | forbid
      auto    → execute (dry-run first if write) → log
      approve → dry-run → approval card to approver_role → wait → execute → log
      forbid  → tool returns a structured refusal; agent tells the user why
  → rate limits and budget checks
  → audit log
```

## 5.8 Growing the catalogue

- Add tools in the order of the process priority list from discovery.
- Each new write tool goes: test instance → shadow (dry-run only, results reviewed) →
  approve mode → auto mode (after N clean approvals, decided per tool).
- Keep a **tool health page**: last successful call, error rate, latency, last contract-test run.
