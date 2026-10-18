# Schemas

JSON Schema (draft 2020-12) for every definition type stored in this repository. CI validates:

| Schema | Validates |
|--------|-----------|
| `event.schema.json` | the event envelope on the bus (CloudEvents 1.0 + extensions) |
| `rule.schema.json` | `rules/*.yaml` |
| `tool.schema.json` | `tools/*.yaml` |
| `flow.schema.json` | `flows/*.json` |

Run `python3 scripts/validate.py` to validate everything, and the graph rules for flows (exactly one trigger, every node reachable, every edge target exists).
