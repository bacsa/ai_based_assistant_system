# AI Operations Assistant – Architecture Plan

A plan for building a company-internal AI assistant that:

- answers questions from the company's own documents (knowledge base),
- watches deadlines and system signals and alerts the right person at the right time
  (e.g. "organic traffic on the website dropped 30 % week over week"),
- executes repetitive tasks in the company's own software, first with a human
  approving every action, later autonomously for low-risk tasks,
- learns the company's flows over time and turns them into reusable playbooks.

The plan is written for a company with its own architecture and in-house software,
so it does not assume any specific SaaS stack. Everything that touches the company's
systems goes through a **tool layer** that you build once per system.

## How to read this plan

| # | Document | Answers |
|---|----------|---------|
| 1 | [docs/01-discovery-checklist.md](docs/01-discovery-checklist.md) | *What can I measure and check in the company in the first round?* |
| 2 | [docs/02-architecture.md](docs/02-architecture.md) | *How do the pieces fit together?* (the big picture, layer by layer) |
| 3 | [docs/03-knowledge-base.md](docs/03-knowledge-base.md) | *How do the documents become a knowledge base?* |
| 4 | [docs/04-rule-system.md](docs/04-rule-system.md) | *What is the rule system, where do rules come from, how are they written?* |
| 5 | [docs/05-tool-system.md](docs/05-tool-system.md) | *What is the tool system, how do I expose in-house software to the assistant?* |
| 6 | [docs/06-learning-loop.md](docs/06-learning-loop.md) | *How does the assistant learn the company flows?* |
| 7 | [docs/07-roadmap.md](docs/07-roadmap.md) | *In what order do we build it, and how do we know it works?* |
| 9 | [docs/09-event-messaging.md](docs/09-event-messaging.md) | *How does it react in real time?* Event bus, producers, consumers, reliability rules, technology choice. |
| 8 | [docs/08-web-console.md](docs/08-web-console.md) | *What does the admin console look like?* Screen map, data model, API. |
| – | [console/index.html](console/index.html) | Clickable prototype of the console with working in-browser engines (open the file in a browser). |
| – | [examples/](examples/) | Concrete rule, tool and playbook definitions you can copy. |

## The one-paragraph version

The assistant is **not** a single chatbot. It is an *agent runtime* (an LLM such as
Claude running in a loop) surrounded by four things it cannot do without:

1. a **knowledge base** built from the company's documents and system data,
2. a **rule system** – deterministic, human-readable rules that say *when* the assistant
   must look at something, *what* counts as abnormal, and *what it is allowed to do*,
3. a **tool system** – a catalogue of safe, typed functions that read from and write to
   the company's software (exposed through the Model Context Protocol, MCP),
4. a **memory and learning loop** – logs of what happened, human feedback, and a process
   for promoting observed patterns into new rules and playbooks.

A **durable event bus** carries every change from the company systems (webhooks, outbox, change data capture, a timer service for deadlines) to the rule engine and the agent within seconds; cron survives only for reconciliation. A
**guardrail layer** decides which actions need human approval, and an **audit log**
records every decision. Channels (Slack/Teams/email/web) are just thin front-ends.

## Core design principles

- **Rules decide, the LLM reasons.** Deadlines, thresholds and permissions live in
  rules that a human can read and audit, not in a prompt. The LLM interprets context,
  drafts messages and chooses between tools – it never decides on its own whether it is
  allowed to write to the ERP.
- **Events for latency, reconciliation for correctness.** Every change is an event on a
  durable bus; consumers are idempotent; a few periodic jobs only compare and correct.
- **Read before write.** Every integration starts read-only. Write tools are added one
  at a time, each with a dry-run mode and an approval policy.
- **Measure first.** Phase 0 is a measurement phase. You cannot alert on "SEO is
  different than usual" without a baseline of what "usual" is.
- **Humans in the loop by default, out of the loop by evidence.** An action becomes
  autonomous only after it has been approved N times without correction.
- **Everything is a document.** Rules, tools, playbooks and lessons learned are files in
  version control, so the assistant's behaviour is reviewable and reversible.
