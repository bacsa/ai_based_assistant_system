# Services (application frame)

One directory per deployable service. Each README states the service's job, what it consumes and produces on the bus, its storage, its interfaces and the definition files it reads. The code is to be written per client; the contracts here are fixed so services can be built and tested independently.

```
                 ┌──────────────┐    events     ┌────────────┐  derived events  ┌──────────────┐
 company systems │ webhook-     │──────────────▶│            │─────────────────▶│ orchestrator │──▶ MCP servers
 SaaS webhooks   │ ingress      │               │ rule-engine│                  │ (Temporal)   │    (tools)
 outbox / CDC ──▶│ collectors   │   NATS        │ timer-svc  │   task.created   │ flow runner  │
 timer service   │ (producers)  │   JetStream   │            │ approval.*       │ agent runtime│
                 └──────────────┘               └────────────┘                  └──────┬───────┘
                                                      ▲                                │
      Slack/Teams/email ◀── notifier ◀────────────────┴──── guardrails (policy, dry run, approvals, audit)
      console (SSE, REST) ◀── console-api ◀── projections (Postgres) ◀── kb-pipeline (Qdrant + Postgres)
```

| Service | Role | Consumes | Produces |
|---------|------|----------|----------|
| `webhook-ingress` | receive signed SaaS deliveries, dedupe, normalise, publish | HTTP | domain events |
| `collectors` | event-triggered pulls from sources without push; change-only publishing | `day.closed`, `cms.page.published` | `seo.metric.collected`, `crawl.page.changed`, `tls.certificate.observed` |
| `timer-service` | durable timers created and cancelled by events | `erp.invoice.*`, `erp.order.*`, deadlines, `ticket.created` | `deadline.reminder.due`, `day.closed`, `flow.delay.elapsed` |
| `rule-engine` | stream processor for threshold, time, state and pattern rules | domain + timer events | `*.detected`, `task.created` |
| `orchestrator` | Temporal workflows: playbook agent runs and flow interpreter | `task.created`, `approval.decided`, awaited events | `agent.step.*`, `flow.run.*`, tool calls |
| `guardrails` | policy decision, dry run, approval queue, audit sink | tool call requests, `>` for audit | `approval.requested`, `tool.call.*` |
| `notifier` | render events to channels, one message per task updated in place | `task.*`, `approval.*`, `*.detected` | `notification.sent` |
| `kb-pipeline` | connectors, parse, chunk, enrich, embed, index, ACL stamp | `kb.document.changed` | `kb.document.indexed` |
| `gateway` | Slack/Teams/email front-ends; buttons become events | human input | `message.received`, `approval.decided`, `task.acknowledged` |
| `console-api` | REST + SSE backend for the control room | projections | writes definitions to git |
| `mcp-servers` | one MCP server per company system exposing the tool catalogue | tool calls | results, `tool.call.*` via guardrails |

Shared contracts: `contracts/openapi.yaml` (console API), `schemas/` (definitions and envelope), `events/catalogue.yaml` (types and consumers), `tools/*.yaml` (tool specs). Reference logic: `reference/python/assistant_core`.
