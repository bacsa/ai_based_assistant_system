# orchestrator
**Job:** Temporal worker. Two workflow types: (1) **playbook run** per `task.created` (the agent runtime executes `playbooks/*.md` steps as activities: tool calls through guardrails, bounded LLM calls); (2) **flow run** per matching trigger event, interpreting `flows/*.json` (`assistant_core.flows` is the reference interpreter; waits become Temporal signals and timers).
**Signals:** `approval.decided`, `task.acknowledged`, awaited events (matched by type + key); escalation timers.
**Outputs:** `agent.step.completed`, `flow.run.started|step|completed|failed`, episodes to memory.
**Model:** Claude via one internal gateway (swap-able); prompts carry evidence from events, never raw secrets.
