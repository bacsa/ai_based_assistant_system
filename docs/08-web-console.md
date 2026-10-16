# 8. Web console

The console is the place where the people who run the assistant see what it knows,
tell it what to watch, give it tools, approve what it wants to do, and test all of
that before it touches real systems. A clickable prototype with working in-browser
engines lives in [`console/index.html`](../console/index.html).

## 8.1 Who uses it

| Persona | Needs |
|---------|-------|
| Assistant owner / admin | health, rule and tool lifecycle, audit, evaluation |
| Department owner (finance lead, SEO owner…) | their rules and deadlines, approvals addressed to them, knowledge gaps in their area |
| Knowledge curator | sources, documents, glossary, unanswered questions |
| Developer | tool catalogue, tool test bench, event log, traces |

Access is role-based through the company identity provider. A department owner sees
only rules, tasks and approvals routed to their roles; admins see everything.

## 8.2 Screen map

```
Overview            tiles: open tasks · pending approvals · rules · knowledge · gaps · tool health
                    open tasks (ack / open agent run) · upcoming deadlines · recent activity
Knowledge base      Documents (list + chunks + ACL)  ·  Ask (search with citations)
                    Add knowledge (paste / upload / URL → pipeline → extracted obligations → draft rule)
                    Sources (connectors, sync)  ·  Entities (deadlines, people, systems)
                    Glossary  ·  Gaps (unanswered questions → document request)
Rules               list with type / status / fire statistics
                    editor per type (threshold, time, state, policy) · YAML as stored in git
                    lifecycle: draft → shadow → active → paused
                    Simulate on history (chart with baseline and threshold, firings per page / timeline / matching records)
Events              Live stream (every event with its consumers, acks, latency, envelope, causal chain)
                    Publish (send a test event through ingress, idempotency and all consumers; see the chain it causes)
                    Catalogue (event types, producers, keys, retention, consumers)
                    Consumers (durable subscriptions, filters, ack policy, processed counts)
                    Producers & timers (timer service with armed timers, webhook ingress, outbox/CDC connectors,
                                        the periodic remainder: collectors and reconciliation)
                    Dead letters (failed deliveries with replay)
Flows               Monitor board (live cards per flow) · Canvas (nodes, ports, branches, live run overlay)
                    Inspector (parameters, last input/output) · Executions (per-node steps, replay)
                    Test run with a sample event · activate / pause · export JSON   (design in doc 10)
Tools               catalogue (server, class, risk, health) · spec the model reads
                    test bench: form from the input schema, dry run, live run through policy
Playbooks           steps, allowed tools, autonomy level, "done" definition
Test lab            Scenario runner: inject a signal → rules evaluate → agent trace → alert → proposed action → approve
                    Talk to the assistant (intent routing, citations, gap logging)
                    Golden questions (retrieval evaluation with pass / fail per question)
Approvals & audit   approval cards (dry-run preview, policy reason, approver) · append-only audit log
```

## 8.3 What each area must be able to do

**Knowledge base**
- Browse documents with metadata (type, department, owner, source, last update, review cycle, ACL) and the chunks as indexed.
- Add knowledge three ways: paste text, upload a file, register a URL or connector. Show the pipeline stages and the result (chunks, ACL, owner).
- Surface what enrichment found: dated obligations and thresholds, offered as **draft rules** that a person confirms.
- Search with the same retrieval the agent uses, with scores, matched terms and citations, filterable by department; log misses as gaps.
- Manage the glossary; retrieval expands synonyms immediately.
- Structured entities (deadlines, people/roles, systems) are tables, editable, and linked to rules.

**Rules**
- One list for all four rule types; filters by type and status; firing statistics per rule (fired, acknowledged, dismissed) so noisy rules stand out.
- Type-specific editors that write the same YAML a developer would commit; the YAML is always visible.
- Lifecycle buttons that enforce draft → shadow → active; every transition is audited.
- Simulation against history before activation: for threshold rules a chart with signal, same-weekday-median baseline, threshold line and firing markers per page; for time rules the reminder timeline; for state rules the matching records; for policy rules a link to the tool bench.

**Events** (design in [doc 09](09-event-messaging.md))
- Live stream of the bus: type, subject, which consumers acked, latency, delivery status; click an event for its CloudEvents envelope, what each consumer did, and the causal chain by correlation id.
- Publish a test event of any catalogued type and watch the chain it causes (for example `cms.page.published` → `crawl.page.changed` → pattern rule → `task.created` → `approval.requested`). Publishing twice with the same idempotency key shows the duplicate being dropped.
- Catalogue and consumers as rendered from the files in git; processed counts per consumer.
- Timer service view: every armed durable timer with "fire now"; webhook ingress with signed test deliveries; outbox and CDC connectors with lag; the periodic remainder (collectors for pull-only sources and reconciliation sweeps) clearly separated from the push path.
- Dead-letter queue with the failing consumer, error and attempts, and a replay button. A "make the rule engine crash on the next event" switch exists to rehearse this.

**Tools**
- Catalogue with server, class (read / write / communicate / knowledge / meta), risk, health and last call.
- Test bench: a form generated from the input schema, "dry run" and "live". Live calls pass the policy engine: auto executes, approve creates an approval card, forbid returns the reason.
- The spec the model reads, so a developer sees exactly what the LLM sees.

**Test lab**
- Scenario runner that injects a synthetic signal (page, size of drop, duration, hidden cause) and runs the daily collection: rule evaluation table, chart, the agent's trace step by step with tool calls and findings, the alert the owner would receive, and the proposed action with its approval card.
- Chat with the assistant for ad-hoc tests; citations on every document answer; misses become gaps.
- Golden question evaluation with pass / fail per question against the expected source document.

**Approvals and audit**
- Approval cards show the dry-run preview, the policy rule and the reason, the approver role and the originating task. Approve executes and closes the task; reject records a correction for the learning loop.
- The audit log is append-only and shows actor, kind and detail for rule firings, tool calls, approvals, edits and tests.

## 8.4 Data model the console works with

```
documents(id, title, type, dept, owner_role, source_id, updated_at, review_every_days, acl[], url)
chunks(id, document_id, heading, text, embedding, tokens, enrichment jsonb)
sources(id, name, kind, default_acl, last_sync_at, status)
glossary(term, meaning, synonyms[])
gaps(question, asked_count, asked_by, last_asked_at, status)
people(role, name, team, channel, backup_role)
systems(name, type, access_path, auth, test_instance, criticality, mcp_server)
rules(id, type, status, owner, owner_role, severity, definition jsonb, version, review_date)
rule_stats(rule_id, window, fired, acked, dismissed)
schedules(id, name, cron, collectors[], rule_ids[], last_run_at, next_run_at, status)
webhooks(id, event, path, source, last_received_at, count_30d)
pollers(id, name, tool, interval, rule_ids[], last_poll_at, status)
events(at, kind, what, detail, payload jsonb)
tasks(id, rule_id, type, key, severity, owner_role, status, created_at, evidence, trace jsonb)
approvals(id, tool, args jsonb, dry_run_result, requested_by, approver_role, policy_rule, status, decided_by, decided_at, result jsonb, task_id)
audit(at, actor, kind, detail, ref)
metrics(signal, dimension, ts, value)
playbooks(id, title, owner, autonomy_level, triggered_by[], steps[], done_when, version)
tools(name, server, class, risk, spec jsonb, health, last_call_at)
```

## 8.5 API surface (backend for the console)

```
GET  /kb/documents  /kb/documents/{id}        POST /kb/documents (multipart or JSON)  DELETE /kb/documents/{id}
POST /kb/search {query, filters}               GET  /kb/sources   POST /kb/sources   POST /kb/sources/{id}/sync
GET/POST /kb/glossary                          GET  /kb/gaps      POST /kb/gaps/{id}/request-document
GET  /entities/{table}  POST/PUT /entities/{table}

GET  /rules  GET /rules/{id}  POST /rules  PUT /rules/{id}  POST /rules/{id}/status {to}
POST /rules/{id}/simulate {from, to}           GET  /rules/{id}/explain?at=

GET  /events/stream (SSE)  GET /events?type=&correlation=&since=   POST /events/publish {type, subject, data, idempotencykey}
GET  /events/catalogue  GET /events/consumers  GET /events/timers  POST /events/timers/{id}/fire
GET  /events/dlq  POST /events/dlq/{id}/replay      POST /producers/webhooks/{id}/test   POST /jobs/{id}/run

GET  /tools  GET /tools/{name}                 POST /tools/{name}/call {args, dry_run}   (passes the policy engine)
GET  /playbooks  GET /playbooks/{id}

POST /lab/scenario {signal, dimension, drop, days, cause}      GET /lab/tasks/{id}/trace
POST /lab/chat {message}                                        POST /lab/evals/run

GET  /approvals?status=   POST /approvals/{id}/approve   POST /approvals/{id}/reject {reason}
GET  /audit?actor=&kind=&since=
GET  /tasks?status=       POST /tasks/{id}/ack   POST /tasks/{id}/snooze {until}
```

Rules, playbooks and tool specs are files in git; the API writes them through a
branch and pull request (or directly in a development environment) so the console and
the repository never diverge.

## 8.6 Implementation notes

- **Stack**: React or Vue single-page app, or server-rendered pages with HTMX; FastAPI/NestJS backend over Postgres; the same backend the Slack/Teams gateway uses.
- **Auth**: OIDC with the company identity provider; roles map to `people.role`.
- **Realtime**: server-sent events for the event log, task list and approval queue.
- **Safety**: the console's "live" tool calls go through exactly the same guardrail path as the agent's; there is no admin bypass of policy rules, only a separate "break-glass" role with its own audit tag.
- **The prototype** keeps all state in the browser (localStorage) with demo data. Its engines (keyword retrieval with glossary expansion, same-weekday-median baselines, policy decisions, mock tool handlers, trace generation) are deliberately small so each can be replaced by the real service behind the same screen.
