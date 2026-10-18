# Decision log

Each entry: decision, why, consequences, when to revisit.

| # | Decision | Why | Consequences | Revisit when |
|---|----------|-----|--------------|--------------|
| 1 | Rules decide, the model reasons | reproducibility and auditability of alerts and permissions | thresholds, deadlines, policies are YAML in git; the agent cannot change them | a rule class is genuinely judgement-based; then add a bounded LLM classifier *as a tool* the rule calls |
| 2 | Events as the primary trigger, cron for reconciliation only | latency, causality, no silent failures (heartbeats) | more components (bus, timer service, ingress); idempotency discipline everywhere | the client has only pull-only sources and no appetite for a bus; then start with event-triggered collectors on a single-node JetStream |
| 3 | NATS JetStream over Kafka | small team, single binary, subjects with wildcards, pull consumers, replay | fewer ecosystem connectors than Kafka (Debezium needs a bridge) | the client already runs Kafka or expects > 10k events/s |
| 4 | Temporal for durable workflows | waits of days, signals for approvals, history per task | one more system to operate | the client has Step Functions or similar in place |
| 5 | MCP for tools, one server per system | discoverable catalogue, same tools for Claude, Claude Code and the console | each system needs a thin server | never; the format is cheap |
| 6 | At-least-once delivery with idempotent consumers | exactly-once does not survive external systems | idempotency key on every event and write tool | never |
| 7 | Flows as a visual layer that cannot bypass policy | client control without losing guardrails | own canvas (React Flow) instead of embedding n8n for core flows | the client's needs are pure integration glue; then n8n via webhooks (docs/10 §10.7) |
| 8 | Chunk-level ACLs in the knowledge base | documents have different audiences | pipeline must know groups; negative tests mandatory | never |
| 9 | Autonomy promoted per (playbook, tool) from events | evidence-based trust | learning-loop consumer; demotion on correction | never |
| 10 | Single-file console prototype | zero build, portable demo, honest about scope | not the production UI | immediately when building the real console |
| 11 | Claude behind one internal gateway | swap-able model, PII redaction in one place | gateway is a service | data residency requires a local model |
