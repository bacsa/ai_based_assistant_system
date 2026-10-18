# Instructions for AI agents working in this repository

Start with `HANDOVER.md` (what this is, map, order of work), then `docs/00-index.md`.

**Before changing definitions:** read the relevant doc (`rules/` → docs/04, `tools/` → docs/05, `flows/` → docs/10, `events/` → docs/09). Keep ids equal to file names. Validate with `python3 scripts/validate.py`.

**Before changing engines:** the Python reference in `reference/python/assistant_core` is the source of truth for behaviour; the console mirrors it in JavaScript. Change both, run `pytest -q` in `reference/python` and `npm test` in `console/`.

**Before changing the console:** read `console/README.md` for the block layout. Keep it a single file with no build step unless the client asks for the production console (then build against `contracts/openapi.yaml`).

**Never:** put thresholds or permissions into prompts; add a write tool without `dry_run`, `idempotency_key` and a policy rule; activate a rule or flow without a shadow or test phase; let the console own state that is not also in git.

**Demo data:** everything naming the fictional company (people, systems, documents, pages like `/pricing`, invoice ids) is demo data. Replace it per client; do not build on it as if it were real.
