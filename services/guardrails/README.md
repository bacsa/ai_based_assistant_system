# guardrails
**Job:** the only path to a tool. `decide(tool, args, actor)` from `rules/policy-*.yaml` → auto | approve | forbid; dry run first for writes; approval queue with cards (Slack/Teams/console); audit sink consuming `>`; rate limits and budget checks; kill switch that pauses action consumers.
**Storage:** Postgres `approvals`, `audit` (append-only), `processed_idempotency_keys`.
**Reference:** `assistant_core.policy.decide`.
