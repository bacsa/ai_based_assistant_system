# 12. Unified design system and screen designs

The full screen designs live on the design canvas:
<https://claude.ai/artifact/FqqtZCHqwEu6bs6cTkWaKS> (34 artboards, Hungarian UI,
built from the design brief `INSEDO_AI_design_brief_for_Claude_Design.md`). The shared
stylesheet those artboards use is checked in at `console/design/insedo.css` so the
production console, the operations shell and the discovery tool build on the same tokens.

## Canvas map

| Row | Artboards | What they fix |
|-----|-----------|---------------|
| 0 · System map | Rendszerkép · Információs architektúra | object glossary with one visual identity per object, one navigation for all surfaces, role-aware menu, screen template |
| 1 · Design system | Tokenek · Komponensek · Csomópont-legenda · UI-szövegezés | colours (light + dark), type, spacing, the mandatory components (§8 of the brief), the nine node types with all run states, the two-tier labelling guide |
| 2 · Operations shell | Mi történik most · Iratkezelés · Partnerek · Képzésadminisztráció · Web és marketing · Pénzügy (VIR) · Ügyfélkapcsolat · HR | the seven assumed modules, each with the "Mit csinál most a rendszer" strip, in-context decision cards and event badges; labelled as assumptions to validate in P0 |
| 3 · Assistant console | Digitális szerep (Iktató) · Döntéseim és a napló · Tudástár · Mire figyel a rendszer · Munkafolyamatok (tervező) · Rendszerkapcsolatok · Munkautasítások · Események és eseménykezelő · Naptár és ütemezés · Tesztlabor | the twelve console screens of the brief, redesigned on the shared system |
| 4 · Conversation and voice | asztali panel · telefon chat · telefon döntés · telefon eredmények · Google Chat kártya | planner transparency, ask-back, missing-tool card, approval modal, results view, phone and Chat reductions of the decision card |
| 5 · Discovery (P0) | Áttekintés · Interjú · Elemzés · Tudásgyűjtő és alapmérés | the Workflow Discovery and Knowledge Intake tool |
| 6 · Dark theme | Mi történik most (sötét) | the same tokens in dark mode |

## Token decisions

- Neutral green-grey base, continuing the prototype palette in `console/index.html`.
- `--brand` (teal `#1E6B74`) is the swappable primary; the INSEDO brand colour replaces it later and must not be amber or yellow.
- `--dec` (amber `#8F5300` on `#FFF1D6`) is reserved for human control points: the decision card, the approval modal, the "Emberi döntés" node and the decision counter. Nothing else may use it.
- Semantic set: `--ok` (live, done), `--obs` (observe, inferred), `--warn` (degraded, attention), `--dang` (error, forbidden, hard rule), `--info` (running, information). Every badge differs in shape as well as colour.
- Node accents: trigger = brand, check = slate, tool = blue, agent = violet with a double border, human decision = amber with a heavy border, task = brown, notify = cyan, wait = grey dashed, end = dark pill.
- Typography: IBM Plex Sans and IBM Plex Mono. Technical identifiers are mono, muted, never bold.
- Policy badge: `.pol.read` (olvasás · automatikus), `.pol.write` (írás · jóváhagyás szükséges), `.pol.forbid` (tiltott). It appears on tools, workflow steps, run traces and decision cards.

## Mapping to the repository

| UI object | Definition in git |
|-----------|-------------------|
| Munkafolyamat, Lépés | `flows/*.json`, palette `flows/node-types.json` |
| Szabály (Mire figyel a rendszer) | `rules/*.yaml` (threshold, time, state, pattern, policy) |
| Eszköz (Rendszerkapcsolat) | `tools/*.yaml` |
| Esemény, Eseménykezelő | `events/catalogue.yaml`, `events/consumers.yaml` |
| Munkautasítás | `playbooks/*.md` |
| Tudástár-elem | `evals/` documents, knowledge pipeline (doc 03) |
| Döntés szükséges, Futás, Naplóbejegyzés | guardrails tables (doc 05), `contracts/openapi.yaml` |

The design keeps the brief's rule that the console is a projection of these files: the
designer screens show file ids in the second, muted tier so an engineer can find the
definition from any screen.
