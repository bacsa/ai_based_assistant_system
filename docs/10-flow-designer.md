# 10. Flow designer and real-time monitoring (the n8n-style layer)

The client should be able to **see** how the assistant works and **shape** it without
reading YAML: a canvas of flows, each a chain of nodes from a trigger to actions, with
executions lighting up the canvas as events arrive. This document designs that layer
on top of the event backbone ([doc 09](09-event-messaging.md)) and the rule, tool and
playbook systems ([docs 04](04-rule-system.md), [05](05-tool-system.md), [06](06-learning-loop.md)).
The console prototype ([`console/index.html`](../console/index.html), section **Flows**)
implements it end to end against demo data.

## 10.1 What a flow is

A **flow** is a visual program:

```
trigger ──► filter / rule ──► enrich (read tools) ──► agent step ──► decision ──► actions ──► end
             │                                                        │
             └─ (not matched) ─► end                                  └─ approval ─► approved / rejected
```

Formally: a directed graph of typed nodes. One node is the trigger (an event type on the
bus, optionally with a filter). Every other node consumes the output of its predecessor
and may branch (`true/false`, `fired/not fired`, `approved/rejected`, `received/timeout`).
A flow definition is a JSON/YAML file in git, versioned like rules and playbooks.

What a flow is **not**: a way around the guardrails. An action node is a tool call and
goes through the same policy engine, dry run and approval path as any other tool call.
The canvas cannot draw an arrow that bypasses an approval.

## 10.2 Node catalogue

| Node | What it does | Branches | Backed by |
|------|--------------|----------|-----------|
| **Trigger: event** | Starts a run when an event of this type (and matching filter) arrives | – | a durable subscription on the bus |
| **Trigger: timer** | Starts a run on a timer event (`day.closed`, `deadline.reminder.due`) | – | timer service |
| **Trigger: manual / message** | Started by a person (button, chat command) | – | `message.received`, console |
| **Filter** | Field condition on the data (`equals`, `contains`, `>`, `<`, `in`, `exists`) | true / false | expression evaluator |
| **Rule** | Evaluates a rule from the rule system against the current state (threshold, pattern, state, time) | fired / not fired | rule engine |
| **Tool (read)** | Calls a read tool, templated from previous outputs (`{{data.path}}`) | ok / error | tool gateway |
| **Agent step** | Runs a playbook or a bounded LLM task (classify, summarise, draft) with the run's evidence as context | ok | agent runtime |
| **Approval** | Asks a role to approve a specific action; the run **waits** on `approval.decided` | approved / rejected | guardrails + durable workflow signal |
| **Tool (write)** | Executes a write tool; policy may turn it into an approval automatically | ok / error | tool gateway |
| **Notify** | Sends a message to a channel or person, one message per run updated in place | ok | notifier |
| **Task** | Creates a task for a role with severity and evidence | ok | task store |
| **Wait for event** | Pauses until an event of a type with a matching key arrives, or a timeout | received / timeout | durable workflow signal + timer |
| **Delay** | Pauses for a duration or until a date | elapsed | durable timer |
| **Branch / merge** | Explicit routing on a value; join parallel paths | per value | – |
| **Sub-flow** | Calls another flow as a step | ok / error | child workflow |
| **End** | Marks the run finished with a status and a summary | – | – |

Data between nodes is JSON. Each node sees `data` (trigger payload), `event` (envelope),
`prev` (previous node output) and `nodes.<id>` (any earlier output), the same way n8n
exposes `$json` and `$node`.

## 10.3 Execution model

- **One run per trigger event.** A run has an id, the triggering event, the correlation
  id (inherited from the event, so the run is part of the causal chain), per-node steps
  with input, output, status and duration, and a final status: `success`, `failed`,
  `waiting`, `stopped`.
- **Runs are durable workflows.** Every flow compiles to a generic interpreter workflow
  in Temporal: nodes are activities (idempotent, retried), waits are signals and timers.
  A deploy or crash in the middle of a 21-day invoice ladder loses nothing.
- **Waits are events.** Approval, wait-for-event and delay nodes park the run. The bus
  (or the timer service) wakes it. Nothing polls.
- **Every run emits operational events**: `flow.run.started`, `flow.run.step`, `flow.run.completed`.
  The audit log, the live monitor and the learning loop are consumers of these.
- **Idempotency per run**: the run id is derived from the flow id and the event's
  idempotency key, so a redelivered event does not start a second run.
- **Error path**: a node failure after retries routes to the flow's error edge if one is
  drawn, otherwise the run fails, a `flow.run.failed` event is emitted and the flow owner
  is notified. Repeated failures of the same node pause the flow automatically.

## 10.4 Monitoring (what the client watches in real time)

- **Monitor board**: one card per flow with state (active / paused / draft), runs today,
  success / failed / waiting counts, last run, p95 duration, and a strip of the last runs
  as coloured ticks. Cards pulse when a run passes.
- **Canvas live view**: nodes light up as a run passes them; counters on each node show
  how many runs passed in the window; waiting nodes show how many runs are parked there.
- **Executions list** per flow: trigger event, status, duration, who approved what; click
  a run to project it onto the canvas (node ring colours) and inspect each node's input and
  output, exactly like n8n's execution view.
- **Global stream** (the Events section) remains the source of truth; the monitor is a
  projection of `flow.run.*` events delivered over server-sent events.
- **Alerts on the flows themselves**: a flow with a rising failure rate, a run waiting on
  approval longer than its SLA, a trigger that has not fired within its expected interval
  (silence detection). These are rules like any other and show up as tasks.

## 10.5 Designing (what the client edits)

- **Node palette** with the catalogue above; the tool nodes are generated from the tool
  catalogue, the rule node lists the rules, the agent node lists the playbooks. Nothing on
  the palette is an unregistered capability.
- **Inspector** for the selected node: name, parameters (typed forms, templates with
  autocomplete from upstream outputs), the last input and output, and node statistics.
- **Connections**: drag from an output port to an input port; branches are labelled ports.
- **Test run with pinned data**: pick a sample event (or a real past event from the
  stream), run the flow without side effects (write tools in dry run, notifications to the
  tester only), see every node's output. Same as n8n's "test workflow" with pinned data.
- **Versioning and lifecycle**: draft → test → active → paused. Activating writes the
  definition to git (pull request in regulated setups) and registers the subscription.
  Every run records the flow version it ran on. Roll back by activating an earlier version.
- **Permissions**: viewers see the monitor and executions; designers edit drafts; owners
  activate. Approval nodes name roles from the people table; a designer cannot assign an
  approval to themselves for a tool they are not allowed to approve.
- **Export / import** JSON for sharing a flow between environments (staging → production).

## 10.6 Relationship to rules, playbooks and the agent

The three are complementary, not competing:

- **Rules** stay the deterministic detectors. A flow *uses* a rule node; it does not
  re-implement thresholds in filters. This keeps thresholds auditable and simulated in one place.
- **Playbooks** are what an agent node executes. A flow decides *when* the agent is
  called and *what happens with its result*; the playbook decides *how* the agent investigates.
- **Policy** is enforced inside tool and approval nodes. A designer who drops a write
  tool node onto the canvas gets the approval behaviour the policy prescribes, whether or
  not they drew an approval node.

In short: flows are the orchestration the client can see and change; rules, playbooks
and policies are the parts that must stay precise.

## 10.7 Build or embed n8n?

| Option | Fits when | Costs |
|--------|-----------|-------|
| **A. Own canvas over own engine** (recommended for the core) | The flows involve the agent, approvals, policy and audit; the client must never be able to bypass guardrails; executions must be durable for weeks | Build the canvas (React Flow / xyflow is the standard library and is what n8n's editor is built on), the inspector and the monitor. The engine already exists (Temporal interpreter + bus consumers). |
| **B. Embed n8n as the engine** | The client already runs n8n; most flows are integration glue between SaaS tools without approvals or LLM reasoning | Policy and audit would have to be re-implemented as n8n custom nodes or enforced only at the tool gateway; long waits depend on n8n's execution persistence; two UIs for one system. |
| **C. Both** | Realistic in many companies | n8n handles low-risk glue and talks to the bus through webhook-in and HTTP-out nodes; the control room monitors its executions through n8n's API alongside its own flows. |

Recommendation: **A for everything that touches the assistant, approvals or company
data; C where a team already lives in n8n.** Either way the flow definitions, the
tool catalogue and the policies remain in this repository.

## 10.8 Implementation notes

- **Front end**: React + xyflow (React Flow) for the canvas; node components per type;
  inspector forms generated from node schemas; SSE subscription for live run events;
  virtualised executions list.
- **Definition format**: `flows/<id>.json` with `nodes[]`, `edges[]`, `version`,
  `status`, `owner`, `trigger`. JSON Schema validated in CI. The prototype's export shows
  the exact shape.
- **Compiler**: validates the graph (one trigger, no unreachable nodes, every write tool
  under policy, approvals assigned to roles), then registers a durable consumer for the
  trigger subject and stores the definition for the interpreter workflow.
- **Interpreter workflow** (Temporal): walks the graph, runs node activities with
  retries, handles signals (`approval.decided`, awaited events, timers), writes steps to
  the execution store, emits `flow.run.*` events.
- **Execution store**: Postgres tables `flow_runs` and `flow_run_steps` with input and
  output JSON (PII-flagged fields redacted according to the event's `pii` attribute).
- **API additions**: `GET/POST /flows`, `PUT /flows/{id}`, `POST /flows/{id}/activate|pause`,
  `POST /flows/{id}/test {event}`, `GET /flows/{id}/runs`, `GET /runs/{id}`,
  `POST /runs/{id}/replay`, `GET /runs/stream` (SSE).
- **Prototype scope**: the console implements the canvas (SVG, draggable nodes, ports,
  branch labels), the inspector with editable parameters, add/connect/delete nodes,
  activate/pause, test runs with sample events, the executions list with per-node input and
  output, waits on approvals, events and timers, the monitor board, and export. It runs on
  the in-browser bus, so flows start from real published events and from the live feed.
