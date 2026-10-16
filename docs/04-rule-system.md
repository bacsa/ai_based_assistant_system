# 4. Rule system

## 4.1 What the rule system is for

The rule system is the deterministic, auditable part of the assistant. It answers:

1. **When** must the assistant look at something? (schedules, events)
2. **What** is abnormal or due? (thresholds, baselines, deadlines, stuck states)
3. **Who** must be told, how urgently, and what happens if they do not react? (routing, escalation)
4. **What is the assistant allowed to do** about it, with or without a human? (policy)

The LLM is deliberately *not* used for 1–4. An LLM deciding every morning whether a 30 %
traffic drop "feels" significant is unreproducible and unauditable. Rules fire; the LLM
then investigates, explains and proposes.

## 4.2 Four rule types

| Type | Question it answers | Typical source | Example |
|------|---------------------|----------------|---------|
| **Time rule** | Is something due? | deadlines.csv, contracts, calendars, document review dates | "VAT return due on the 20th; warn owner 10 days before, escalate 3 days before" |
| **Threshold / anomaly rule** | Is a signal outside normal? | signals.csv + baselines | "Organic clicks per landing page < 70 % of 28-day same-weekday median for 2 consecutive days" |
| **State rule** | Is a record stuck or inconsistent? | process inventory, SLAs | "Order in status *awaiting payment* for > 7 days", "ticket without response > 4 h" |
| **Policy rule** | May this action happen, and who must approve? | security/finance policies, blast-radius assessment | "`erp.create_payment_reminder` is auto if amount < 500 and customer not flagged, else needs Finance approval" |

Every fired rule produces a **task** with: rule id, severity, owner (role → person via
`people.yaml`), the evidence the rule evaluated, the suggested playbook, and the
allowed actions.

## 4.3 Representation – rules as YAML in git

Keep rules in a `rules/` folder, one file per rule, validated by a JSON schema, reviewed
through pull requests. Business users edit them through the admin console, which writes
the same files.

```yaml
# rules/seo-organic-drop.yaml   (full version in examples/rules/)
id: seo-organic-drop
type: threshold
description: Organic clicks on a key landing page fell well below its usual level.
signal: search_console.clicks
dimensions: [landing_page]
scope:
  landing_page: { in_list: key_pages }        # list maintained in entity store
baseline:
  method: same_weekday_median
  window_days: 28
condition:
  ratio_to_baseline: { lt: 0.70 }
  consecutive_periods: 2
  min_baseline_value: 20                      # ignore pages with tiny traffic
severity: high
owner_role: seo_owner
cooldown: 3d
playbook: seo-drop-triage
allowed_actions:
  - tool: slack.post_message          # auto
  - tool: cms.remove_noindex          # approval required (see policy rule)
  - tool: ticketing.create_issue
escalation:
  - after: 24h
    unacknowledged: true
    notify_role: marketing_lead
```

A **time rule**:

```yaml
id: vat-return
type: time
schedule: { cron: "0 0 20 * *" }              # due date
lead_times: [10d, 3d, 1d]                     # reminders before due
owner_role: finance_lead
requires_ack: true
escalation:
  - after: 48h
    unacknowledged: true
    notify_role: cfo
playbook: vat-return-checklist
context_tools:
  - erp.get_period_status                     # the agent pre-fetches these
  - kb.search: "VAT return procedure"
```

A **policy rule**:

```yaml
id: policy-payment-reminders
type: policy
tool: erp.create_payment_reminder
environment: production
decision:
  - when: { amount: { lt: 500 }, customer.flagged: false, reminder_level: { lte: 2 } }
    allow: auto
  - when: { reminder_level: 3 }
    allow: approve
    approver_role: finance_lead
  - otherwise: forbid
rate_limit: { max_per_day: 200 }
dry_run_first: true
```

## 4.4 Where rules come from

1. **Discovery tables** – deadlines, SLAs and the thresholds people already use become
   rules 1:1. This is 60–80 % of the initial rule set.
2. **Documents** – the KB enrichment step extracts dated obligations and "must/shall"
   sentences from policies and contracts. The LLM drafts a rule; a human confirms it in
   the console. Never auto-activate an extracted rule.
3. **Statistical defaults** – for signals without a human threshold: median ± 3×MAD
   over 28 days, or seasonal decomposition for weekly/yearly patterns. Start noisy,
   tune down using acknowledge/dismiss feedback.
4. **The learning loop** – repeated incidents and repeated manual actions get proposed
   as new rules (doc 06).

## 4.5 Rule lifecycle

```
draft → shadow (evaluates, logs, does not notify) → active → tuned → retired
```

- Run every new rule in **shadow mode** for 1–2 weeks and look at how often it would
  have fired. Then activate.
- Each rule has an **owner** and a **review date** (itself a time rule).
- Track per rule: fired, acknowledged, dismissed as noise, led to action. A rule with
  a high dismiss rate is automatically flagged for tuning.
- Rules are versioned; the audit log stores the rule version that fired.

## 4.6 Engine

A small service that:

1. Loads and validates the rule files (schema check, unknown tool/role check against the catalogues).
2. On schedule or event, evaluates the relevant rules against the metrics/entity stores (SQL for baselines; small Python for conditions).
3. Deduplicates (cooldown, open task already exists), applies severity and routing.
4. Emits a *task* to the orchestrator and writes the firing to the audit log.
5. Exposes `rules.explain(rule_id, timestamp)` so the agent and humans can see exactly which numbers caused a firing.

For policy rules evaluate inside the guardrail layer at tool-call time. Open Policy
Agent (OPA) is a good fit if policies become complex; a YAML matcher is enough at first.

## 4.7 Anti-patterns to avoid

- Thresholds in prompts ("alert if traffic looks low") – unreproducible.
- One giant rule file – ownership becomes impossible.
- Alerts without an owner or without an acknowledge action – they will be ignored.
- No cooldown – the same drop alerts every day.
- Activating LLM-extracted rules without human confirmation.
