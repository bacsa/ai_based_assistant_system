# Handover: AI Operations Assistant blueprint

This repository is a complete, reusable blueprint for adding an AI assistant to a company
that already has its own systems and workflows. It was built for a fictional company
(an ERP, a CMS, Search Console, Jira, Slack) so that every part could be demonstrated end
to end. **Everything specific to that company is demo data and is marked as such.** The
method, the architecture, the definition formats, the engines and the console are the
reusable parts.

If you are an AI agent (or a person) starting a new client project from this repository,
read this file first, then follow the order of work in §4.

## 1. What the assistant does

- Answers questions from the company's documents with citations (knowledge base).
- Watches deadlines and signals and alerts the right person at the right time.
- Reacts to changes in the company's systems within seconds through an event bus.
- Executes repetitive tasks through typed tools, first behind approvals, later autonomously, with every step audited.
- Lets the client see and shape its behaviour in a web console: knowledge, rules, events, flows (an n8n-style canvas), tools, test lab, approvals and audit.

## 2. Map of the repository

| Path | What | Status |
|------|------|--------|
| `README.md` | overview and principles | reusable |
| `docs/00-index.md` | reading order for the documents | reusable |
| `docs/01` … `docs/11` | discovery, architecture, knowledge base, rules, tools, learning loop, roadmap, console, events, flows, decisions | reusable |
| `inventory/templates/` | blank discovery templates (systems, processes, deadlines, signals, people, documents, NFR) | reusable |
| `inventory/*.csv|yaml` | the demo company's inventory | **demo data** |
| `rules/*.yaml` | rule definitions (threshold, time, state, pattern, policy) | demo content, reusable format |
| `tools/*.yaml` | tool specs, one per MCP tool | demo content, reusable format |
| `playbooks/*.md` | procedures the agent follows | demo content, reusable format |
| `flows/*.json` | visual flows over the bus; `node-types.json` is the palette | demo content, reusable format |
| `events/catalogue.yaml`, `events/consumers.yaml` | event types and durable consumers | demo content, reusable format |
| `schemas/*.json` + `scripts/validate.py` | JSON Schemas and the cross-reference validator | reusable |
| `reference/python/assistant_core` | tested Python implementation of events, rules, policy, flow interpreter, knowledge | reusable |
| `services/*/README.md` | the application frame: one README per service with job, inputs, outputs, storage | reusable |
| `infra/` | docker compose (NATS, Postgres, Temporal, Qdrant, Langfuse, console) and SQL schema | reusable |
| `contracts/openapi.yaml` | console backend API | reusable |
| `console/index.html` | clickable prototype with working in-browser engines; `console/tests` smoke tests | reusable shell, demo data inside |
| `evals/` | golden questions and demo documents | demo content, reusable format |
| `examples/` | earlier hand-written examples of rules, tools, events, playbooks | reference |

## 3. The architecture in one paragraph

An **event bus** (NATS JetStream) carries every change from the company systems (outbox,
change data capture, webhook ingress, a timer service for deadlines, change-only
collectors for pull-only sources, people's button clicks). A **rule engine** consumes it
as a stream processor and emits derived events with evidence. An **orchestrator**
(Temporal) runs playbooks with the agent and interprets the visual **flows**, waiting on
approvals, events and timers as signals. Every action goes through **guardrails**
(policy from `rules/policy-*.yaml`, dry run, approval, audit) to **MCP tool servers**,
one per system. A **knowledge pipeline** indexes documents with chunk-level ACLs. The
**console** is a projection of all of it. Cron survives only for reconciliation.
Principles: events for latency, reconciliation for correctness, durable workflows for
anything that waits; rules decide, the model reasons; read before write; humans in the
loop by default, out by evidence; everything is a file in git.

## 4. Order of work for a new client

Each step names its inputs, its outputs and its definition of done.

### Step 0 – Set up
- Copy this repository. Keep `docs/`, `schemas/`, `scripts/`, `reference/`, `services/`, `infra/`, `contracts/`, `console/`. Empty or replace the demo content in `inventory/`, `rules/`, `tools/`, `playbooks/`, `flows/`, `events/`, `evals/` as the steps below produce real ones.
- Run `python3 scripts/validate.py` and `cd reference/python && pytest -q` to confirm the toolchain. Open `console/index.html` to learn the target experience.
- Done when: validator and tests pass; the team has clicked through the console.

### Step 1 – Discovery (docs/01)
- Fill `inventory/templates/*` with the client: systems and how a program can reach each one, recurring processes with frequency and cost, deadlines, signals with baselines, documents and ACLs, people and channels, non-functional requirements.
- Prioritise processes by `(frequency × minutes) + penalty of forgetting − complexity`.
- Done when: inventories written; the top 10 processes chosen; 4 to 12 weeks of history for the first signals is being collected; 50 golden questions drafted.

### Step 2 – Knowledge base (docs/03)
- Connectors for the client's sources; chunk ACLs; glossary from day one; golden set in `evals/golden-questions.json`.
- Use `assistant_core.knowledge` for chunking and obligation extraction while the production pipeline is built; obligations become **draft** rules, never active ones.
- Done when: ≥ 85 % correct-and-cited on the golden set; negative ACL tests pass; unanswered questions are logged as gaps.

### Step 3 – Trigger points and the event system (docs/09)
- For every system in `inventory/systems.csv` decide the producer mechanism: outbox (in-house, changeable), CDC (in-house, database access), webhook ingress (SaaS), collector (pull-only, change-only), timer service (deadlines). Write the result into `events/catalogue.yaml`: one entry per event type with producer, key, retention, consumers.
- Bring up `infra/docker-compose.yml`; implement `webhook-ingress`, `timer-service` and the first collector; publish real events; verify idempotency, per-key ordering, DLQ and replay.
- Done when: the catalogue is validated; domain events from at least two systems flow; `producer.heartbeat` and silence detection work; p95 ingress-to-decision < 5 s on staging.

### Step 4 – Rules (docs/04)
- Turn `inventory/deadlines.csv` into time rules and `inventory/signals.csv` into threshold rules; add state rules for stuck records and pattern rules for "change X followed by Y". Keep policy rules per write tool.
- Port `assistant_core.rules` into the `rule-engine` consumer; run every rule in **shadow** for 1 to 2 weeks; tune by dismiss rate.
- Done when: 20 to 40 rules active; dismiss rate < 30 %; every rule has an owner and a review date.

### Step 5 – Tools (docs/05)
- One MCP server per system; 5 to 15 business-level tools each, from `tools/*.yaml`. Read tools first. Write tools with `dry_run` and `idempotency_key`, least-privilege service accounts, contract tests against test instances.
- Guardrails: `assistant_core.policy` semantics from `rules/policy-*.yaml`; approval cards; audit sink.
- Done when: the tool health page is green; every write tool has a policy rule; first approvals flow through Slack/Teams.

### Step 6 – Playbooks, flows and the agent (docs/06, docs/10)
- Write playbooks for the top processes; model each process as a flow in `flows/*.json` using the node palette; validate with `scripts/validate.py`; run the interpreter tests pattern from `reference/python/tests/test_flows.py` with the client's flows.
- Orchestrator: Temporal workflows wrapping the agent runtime and the flow interpreter; waits are signals.
- Done when: 3 to 5 processes run at autonomy level 1 to 2; episodes are recorded; the weekly lessons queue produces drafts.

### Step 7 – Console (docs/08, docs/10)
- Build the production console against `contracts/openapi.yaml`, screen by screen as in the prototype; React Flow for the canvas; SSE for live views; OIDC roles from `inventory/people.yaml`.
- Done when: the client can monitor events and flows live, edit rules and flows with versioning, test with sample events, and approve from the console.

### Step 8 – Operate and promote autonomy
- Monthly: rule precision table, autonomy promotions per (playbook, tool) from `approval.decided` and `task.resolved` events, golden-set accuracy, hours saved vs baseline. Promotion needs evidence; demotion is automatic on a correction.

## 5. Conventions the next agent must keep

- Event types are `domain.entity.past_tense`; schema versions live in `dataschema`, not in the name.
- Rule, tool and flow ids are kebab-case and equal their file names.
- Thresholds, deadlines and permissions live in rules, never in prompts or filters.
- Every write tool: `dry_run`, `idempotency_key`, a policy rule, a contract test.
- No new capability enters a flow palette unless it is a registered tool, rule or playbook.
- Definitions change through git; the console writes files, it does not own state.
- Run `python3 scripts/validate.py` and `pytest` before committing definition changes; run `npm test` in `console/` after changing the prototype.

## 6. What is finished, what is a frame, what is open

| Finished | Frame (contract fixed, code per client) | Open questions per client |
|----------|------------------------------------------|---------------------------|
| architecture and method documents | all `services/*` | which bus (NATS recommended; Kafka if present) |
| definition formats, schemas, validator | console backend and React Flow UI | model hosting and data residency |
| Python reference engines with tests | MCP servers per system | identity provider and role mapping |
| console prototype with smoke tests | collectors for pull-only sources | embed n8n for glue or not (docs/10 §10.7) |
| infra compose and SQL schema | | autonomy appetite per team |

## 7. Honest limits

The prototype's engines are small by design (keyword retrieval instead of embeddings,
pattern-based obligation extraction, mock tools). The Python reference mirrors them and
is tested, but it is not a service: it has no I/O, no persistence and no concurrency. The
production build is real engineering work, estimated in `docs/07-roadmap.md` at two
engineers plus half a data engineer for about six months to reach assisted actions.
