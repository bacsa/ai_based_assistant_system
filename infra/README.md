# Infrastructure

`docker-compose.yml` brings up the backbone for local development: NATS JetStream (bus), Postgres (projections, timers, approvals, audit, flow runs; schema in `sql/`), Temporal + UI (durable workflows), Qdrant (vectors), Langfuse (LLM tracing) and nginx serving the console prototype at http://localhost:8080. Application services are listed commented out until their code exists.

Production notes are in `docs/02-architecture.md` §2.4 and `docs/09-event-messaging.md` §9.9: run inside the company network, service accounts per MCP server from the vault, mTLS between services, a staging stack wired to the systems' test instances.
