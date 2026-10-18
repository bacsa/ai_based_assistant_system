# Assistant Control Room (prototype)

A single HTML file (`index.html`) with no build step. Open it in a browser, or `npm run serve` and visit http://localhost:8080. Everything runs in the browser against demo data; state is kept in `localStorage` (sidebar: "Reset demo data").

## What it demonstrates

| Section | Backed by (in the prototype) | Production counterpart |
|---------|------------------------------|------------------------|
| Overview | state projections | console-api over Postgres |
| Knowledge base | keyword index + glossary expansion, chunking, obligation extraction | kb-pipeline (Qdrant hybrid search, LLM enrichment) |
| Rules | `evalThreshold`, `timeStatus`, `evalState`, pattern handler | rule-engine (`assistant_core.rules`) |
| Events | `emit()` with subscriptions, idempotency, DLQ, timers, live feed | NATS JetStream + timer-service + webhook-ingress |
| Flows | `startRun` / `execNode` / `resumeRun`, SVG canvas | orchestrator (Temporal interpreter) + React Flow UI |
| Tools | `runTool` mocks behind `callTool` → `policyDecision` | MCP servers behind guardrails |
| Test lab | scenario injection, chat routing, golden evaluation | evals + staging stack |
| Approvals & audit | in-memory arrays | guardrails tables |

## Where things are in `index.html`

The script is organised in labelled blocks (search for `// ----------`):

1. `utilities` · 2. `demo data` (`PEOPLE`, `SYSTEMS`, `DOCS`, `RULES`, `TOOLS`, `PLAYBOOKS`, `initialState`) · 3. `knowledge engine` · 4. `rule engine` · 5. `policy + tools` · 6. `scenario + agent trace` · 7. `assistant chat` · 8. `event bus` (`TOPICS`, `SUBSCRIPTIONS`, `emit`, `HANDLERS`, live feed) · 9. `flows` (`seedFlows`, interpreter, canvas) · 10. `views` · 11. `actions` (`A`), `FORMS`, event wiring, `start()`.

The definitions in blocks 2, 8 and 9 are also exported as files at the repository root (`rules/`, `tools/`, `flows/`, `playbooks/`, `events/`, `inventory/`, `evals/`). When adapting the prototype for a new client, change the files first, then mirror them into the demo data (a loader that reads the files at runtime is a small, worthwhile improvement).

## Tests

```bash
npm install                        # playwright
npx playwright install chromium    # unless a browser is already configured
npm run check                      # script parses
npm run test                       # three headless smoke runs: core, events, flows (screenshots in tests/out/)
```

Each smoke test prints a line per checked behaviour and `ERRORS none` at the end.
