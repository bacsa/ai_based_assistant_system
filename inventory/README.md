# Inventory

Discovery outputs live here. The files at this level are **demo data for the fictional company** used by the console; the `templates/` folder holds blank templates for a new client. Fill the templates during Phase 0 (see `docs/01-discovery-checklist.md`), then replace the demo files.

| File | Feeds |
|------|-------|
| `systems.csv` | tool catalogue (`tools/`), producers (`events/catalogue.yaml`) |
| `processes.md` | flows (`flows/`), playbooks (`playbooks/`), rules (`rules/`) |
| `deadlines.csv` | time rules and timer-service timers |
| `signals.csv` | threshold rules and the metrics store |
| `people.yaml` | routing of alerts and approvals; console roles |
| `documents.md`, `glossary.yaml` | knowledge base pipeline and retrieval |
| `non-functional-requirements.md` | hosting, privacy, model choice |
