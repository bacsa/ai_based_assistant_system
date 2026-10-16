# 7. Roadmap

Build in thin vertical slices: each phase delivers something employees use, and each
later phase reuses the plumbing of the earlier ones.

## Phase 0 – Discovery and baseline (weeks 1–4)

- Run the checklist in [doc 01](01-discovery-checklist.md).
- Stand up the metrics store and the first pollers for 5–10 signals (SEO + two business
  domains) so baselines start accumulating **now**.
- Collect the golden document set and the first 50 golden questions.
- Agree success metrics and the non-functional requirements (hosting, privacy).

**Exit criteria:** inventories written, baselines flowing, priority list of 10 processes.

## Phase 1 – Knowledge assistant (weeks 4–8)

- Document pipeline with 2–3 connectors, ACL-aware hybrid retrieval, citations.
- Slack/Teams bot for Q&A; admin console with KB health and unanswered-question log.
- Entity store filled from discovery; `kb.*`, `metrics.query`, `entities.sql` tools.
- Tracing and the evaluation harness.

**Exit criteria:** ≥ 85 % correct-and-cited on the golden set; 20+ weekly active users.

## Phase 2 – Monitoring and reminders (weeks 8–14)

- Rule engine with time, threshold and state rules; first 20–40 rules from the
  deadline and signal inventories; shadow → active.
- Alert routing, acknowledge/snooze, escalation, cooldowns.
- Read-only MCP servers for the SEO stack and 1–2 business systems; `seo-drop-triage`
  and 2–3 deadline playbooks.
- Dashboards: alerts fired / acknowledged / dismissed per rule.

**Exit criteria:** deadlines tracked in one place; anomaly-to-awareness time measured and
down; dismiss rate < 30 %.

## Phase 3 – Assisted actions (weeks 14–22)

- Guardrail layer with policy rules, dry-run, approval cards, audit log.
- First write tools (ticket creation, CMS meta edits, payment reminders…) at autonomy
  level 1–2, proven on test instances first.
- Episodic memory and the weekly lessons queue.

**Exit criteria:** 3–5 repetitive tasks executed through approvals; hours saved reported.

## Phase 4 – Autonomy and learning (week 22+)

- Promotion ladder in operation; low-risk actions at level 3.
- Process mining job drafting new rules/playbooks from episodes and logs.
- More systems and departments onboarded using the same templates.

## Team and effort (indicative)

- 1 engineer for integrations / MCP servers (the biggest share of work),
- 1 engineer for the agent runtime, rules engine and console,
- 0.5 data/ML engineer for the KB pipeline and evaluation,
- a business owner per department for 2–4 h per week during discovery and rule review.

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Alert fatigue, assistant gets muted | shadow mode, cooldowns, owner per rule, dismiss-rate review |
| Wrong write in a business system | read-first, dry-run, approvals, autonomy ladder, test instances |
| Data leakage through the KB | chunk-level ACLs, negative tests, redaction |
| Integration cost explodes | prioritise by process score; prefer API/DB over UI automation |
| Knowledge rots | document owners, review-date rules, unanswered-question log |
| Vendor lock-in | MCP for tools, model behind a gateway, rules/playbooks as files |

## Repository layout proposal

```
.
├── docs/                 # this plan
├── inventory/            # discovery outputs (systems.csv, processes.md, deadlines.csv, signals.csv, people.yaml)
├── rules/                # one YAML per rule, schema-validated
├── playbooks/            # versioned procedures the agent follows
├── tools/                # tool specs (YAML) → generate MCP server stubs
├── services/
│   ├── gateway/          # channels (Slack/Teams/email/web)
│   ├── orchestrator/     # agent runtime, sub-agents, playbook executor
│   ├── rule-engine/
│   ├── scheduler/        # cron, pollers, webhook receivers
│   ├── kb-pipeline/      # connectors, parsing, chunking, indexing
│   ├── guardrails/       # policy evaluation, approvals, audit log
│   └── mcp-*/            # one MCP server per company system
├── evals/                # golden questions, anomaly scenarios, task scenarios
└── infra/                # docker-compose / k8s, secrets wiring
```
