# assistant-core (Python reference implementation)

Framework-free, tested implementations of the deterministic engines that the console prototype runs in JavaScript. Use them as the starting point for the production services, or as executable documentation of the intended behaviour.

| Module | Production home | What it gives you |
|--------|-----------------|-------------------|
| `events.py` | webhook ingress, every producer and consumer | envelope with idempotency / partition / correlation / causation, ULIDs, subject matching, idempotency store |
| `rules.py` | rule engine (bus consumer) | same-weekday-median baselines with consecutive-breach logic, time-rule phases and reminder timers, state rules, pattern rules |
| `policy.py` | guardrail service / tool gateway | auto / approve / forbid decisions for a tool call |
| `flows.py` | Temporal interpreter workflow | runs `flows/*.json`; waits are returned to the caller; handlers injected |
| `knowledge.py` | knowledge pipeline and retrieval | chunking, obligation extraction, keyword retrieval with glossary expansion, confidence |

```bash
cd reference/python
pip install -e ".[test]"
pytest -q
```

The tests load the real definition files from `rules/`, `flows/`, `tools/`, `evals/` and `inventory/` at the repository root, so they double as integration tests for those files.
