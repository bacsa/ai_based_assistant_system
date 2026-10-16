# 6. How the assistant learns the company's flows

"Learning" here does not mean fine-tuning a model. It means systematically turning
observations into **rules, playbooks, glossary entries and KB updates** that are
reviewed by humans and stored in git. This is cheaper, auditable and reversible.

## 6.1 Sources of learning

| Source | What is extracted | Becomes |
|--------|-------------------|---------|
| Documents (SOPs, policies, contracts) | steps, obligations, deadlines, owners | playbook drafts, time rules, entity records |
| Tickets, emails, chat history (with consent) | recurring request types, who handles them, typical resolution | process entries, playbooks, routing |
| System logs and events | sequences of actions people take in the systems (process mining) | playbook drafts, state rules |
| Metrics history | seasonality, normal ranges | baselines for anomaly rules |
| Human feedback on alerts (ack / dismiss / "not useful") | rule precision | threshold tuning, rule retirement |
| Human edits of drafted actions and messages | preferred wording, missing steps | playbook and prompt updates |
| Unanswered questions | KB gaps | document requests to owners, glossary entries |

## 6.2 Memory design

- **Episodic memory**: every task run stored as (trigger, context, tools called,
  result, human reaction, outcome). Indexed semantically so the agent can recall "the
  last time clicks dropped on /pricing it was a noindex tag".
- **Procedural memory**: playbooks – versioned step lists with preconditions, tools to
  use, decision points, and a "done" definition. The agent prefers a playbook when one
  matches the task.
- **Semantic memory**: the KB and the entity store (doc 03).
- **Preferences**: per person/team – channel, tone, autonomy level, quiet hours.

Memory writes from the agent are **proposals** reviewed in a weekly "lessons" queue,
except for low-risk preference updates.

## 6.3 The promotion ladder

```
observation ─► pattern (seen ≥ 3×) ─► draft (rule / playbook / glossary) ─► human review ─► shadow ─► active
```

Concretely:

1. A weekly job clusters episodes and tool-call sequences.
2. For clusters with ≥ 3 occurrences and consistent resolution, the agent drafts an
   artefact: a rule ("deployment → page meta diff"), a playbook ("month-end invoice
   reminders"), or a glossary term.
3. The draft lands as a pull request / console item with the evidence attached.
4. A human approves, edits or rejects. Rules go to shadow mode first (doc 04 §4.5).

## 6.4 Autonomy ladder per action

Each (playbook, tool) pair has an autonomy level:

| Level | Behaviour | Promotion criterion |
|-------|-----------|---------------------|
| 0 Observe | assistant describes what it would do | – |
| 1 Suggest | assistant drafts; human executes | ≥ 10 suggestions accepted unchanged |
| 2 Approve | assistant executes after one-click approval | ≥ 20 approvals, 0 corrections in 30 days |
| 3 Auto with report | executes, reports daily | demotion on any correction |
| 4 Auto silent | executes, visible in audit only | only for trivial, reversible actions |

Promotion is a human decision informed by the numbers; demotion is automatic on error.

## 6.5 Evaluation as a habit

- Re-run the golden question set and the anomaly scenario set on every change.
- Monthly review meeting: rule precision table, autonomy promotions, top unanswered
  questions, hours saved vs. baseline.
- Keep a `CHANGELOG` of behaviour changes (new rules, playbooks, autonomy level
  changes) so employees can see what the assistant now does differently.
