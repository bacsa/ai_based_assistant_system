"""Reference implementation of the deterministic parts of the assistant.

These modules mirror the engines that run inside console/index.html so that a
production team (or an AI agent) starts from tested, framework-free code:

- events.py   : event envelope, idempotency store, subject matching
- rules.py    : threshold (same-weekday-median baseline), time (lead times), state, pattern rules
- policy.py   : policy decision for a tool call (auto / approve / forbid)
- flows.py    : interpreter for flows/*.json (synchronous; waits are returned, not blocked on)
- knowledge.py: chunking, obligation extraction, keyword retrieval with glossary expansion

Nothing here talks to a network. Wire these into NATS JetStream consumers, Temporal
activities and MCP servers as described in docs/09 and docs/10.
"""
__all__ = ["events", "rules", "policy", "flows", "knowledge"]
