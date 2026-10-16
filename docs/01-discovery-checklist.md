# 1. Discovery – what to measure and check in the first round

Goal of the first round (2–4 weeks): leave with a **written inventory** of the
company's systems, flows, deadlines and documents, plus a **numeric baseline** for the
signals the assistant will later watch. Without this inventory the rule system and the
tool system cannot be designed – they are derived from it.

Treat this as a questionnaire plus a measurement exercise. Each section ends with the
artefact you should walk away with.

---

## 1.1 System inventory – "what software exists and how can a program reach it?"

For **every** system the employees touch (in-house or bought), record:

| Field | Why it matters |
|-------|----------------|
| Name, owner, purpose | Who approves integration, who answers questions |
| Type: in-house / SaaS / on-prem package | Determines integration options |
| **Access path**: REST/GraphQL API, SOAP, direct DB, file export, email reports, UI only | Decides how the tool layer is built (see doc 05) |
| Authentication: SSO, API key, service account, per-user login | Decides whether the assistant acts as itself or on behalf of a user |
| Data it holds (entities): customers, orders, invoices, tickets, pages, employees… | Becomes the shared data model |
| Events it emits: webhooks, log lines, status emails, nothing | Decides push vs poll in the scheduler |
| Environment: test instance available? | You cannot build write tools without a sandbox |
| Criticality / blast radius of a wrong write | Sets the approval policy per tool |

**Artefact:** `inventory/systems.csv` (or a sheet) with one row per system, and an
"integration feasibility" score per row: *API available* › *DB read replica* ›
*file export* › *UI automation only*.

## 1.2 Process inventory – "what do people do repeatedly?"

Interview 1–2 people per team. For each recurring task capture:

- **Trigger** – calendar date ("every 1st of the month"), an event ("new order arrives"),
  a condition ("stock below 20"), or a person asking.
- **Steps** – clicks, systems touched, documents consulted, approvals needed.
- **Inputs / outputs** – which fields are read, which records are created or changed.
- **Frequency and duration** – how often, minutes per occurrence. (frequency × duration
  = the value of automating it.)
- **Failure modes** – what happens when it is forgotten or done wrong, how often that happens.
- **Decision points** – where a human judgement is needed vs. a lookup.
- **Deadline** – hard (legal/contractual) or soft (internal).

Prioritise with a simple score: `(frequency × minutes) + (penalty of forgetting)`,
discounted by `complexity` and `blast radius`. The top of that list is Phase 1 scope.

**Artefact:** `inventory/processes.md`, one short SOP-style entry per task, plus the
priority table.

## 1.3 Deadline and calendar inventory

Collect every recurring obligation into one table, regardless of where it lives today
(someone's head, Outlook, a spreadsheet, the ERP):

| Deadline | Owner | Source of truth | Lead time needed | Consequence if missed |
|----------|-------|-----------------|------------------|-----------------------|
| VAT return | Finance | tax calendar | 10 days | fine |
| SSL certificate renewal | IT | certificate expiry | 14 days | site down |
| Supplier contract renewal | Procurement | contract DB | 60 days | auto-renew at old price |
| Domain renewal, licence renewals, audits, reports, payroll cut-offs, … | | | | |

This table becomes the first set of **time rules** almost 1:1.

**Artefact:** `inventory/deadlines.csv`.

## 1.4 Signal inventory and baselines – "what does *normal* look like?"

The assistant can only say "this is different than usual" if it has a baseline. For
each domain, pick the handful of metrics that matter and record **where the number comes
from**, **how often it can be read**, and **4–12 weeks of history**.

### Website / SEO (your example)

| Signal | Source | Cadence | Baseline method |
|--------|--------|---------|-----------------|
| Organic sessions, by landing page | Google Analytics / Matomo / server logs | daily | week-over-week and same-weekday-4-week median |
| Impressions, clicks, CTR, avg. position | Google Search Console API | daily (2-day lag) | 28-day rolling median ± MAD |
| Indexed pages, coverage errors, manual actions | Search Console | daily | count delta |
| Crawl errors, 4xx/5xx, redirect chains | server logs / crawler run | daily | count delta |
| Core Web Vitals (LCP, INP, CLS) | PageSpeed Insights API / CrUX | weekly | threshold (good/needs work/poor) |
| Title/meta/H1/canonical/robots/sitemap changes | own crawler diffing the HTML | daily | any change on key pages = event |
| Backlinks lost/gained | Ahrefs / Semrush / Majestic API | weekly | count delta |
| Keyword rankings for the top N terms | rank tracker | daily/weekly | position drop > X |
| Uptime, TLS expiry, DNS changes | uptime monitor | minutes | binary |

### Other common domains (pick what applies)

- **Sales / CRM**: new leads per day, lead response time, stale opportunities, pipeline value by stage.
- **Finance**: open invoices by age bucket, overdue payables, cash position, unusual transactions.
- **Operations / fulfilment**: orders per status, time in status, stock below reorder point, late shipments.
- **Support**: open tickets by age, first-response time, SLA breaches, sentiment spikes.
- **HR / admin**: contract end dates, probation ends, mandatory training expiry, leave balances.
- **IT**: backup success, disk/CPU, failed logins, certificate and licence expiry, pending updates.
- **Compliance**: audit dates, policy review dates, data retention deletions due.

For each signal write down the **thresholds people actually use today** ("if traffic
drops more than 20 % we look at it") – these are the first threshold rules. Where nobody
has a number, use a statistical default (median ± 3×MAD over 28 days) and tune later.

**Artefact:** `inventory/signals.csv` + a notebook/sheet with the baselines.

## 1.5 Document corpus audit – input for the knowledge base

For the "bunch of documents":

- Where do they live (file shares, SharePoint/Drive, wiki, ticket system, email)?
- Formats and volume (count and GB per format: docx, pdf, xlsx, pptx, html, md, images with text).
- Which are **authoritative** (policies, SOPs, contracts, product specs) vs **noise** (drafts, duplicates, old versions)?
- Freshness: when were they last updated, who owns them, is there a review cycle?
- **Access control**: who may read what. The assistant must respect this; a document-level ACL map is mandatory before ingestion.
- Language(s) and terminology: collect a glossary of company-specific terms and abbreviations early – it improves retrieval a lot.
- Structured data hiding in documents: tables in Excel, price lists, calendars – these should become *data*, not text chunks.

**Artefact:** `inventory/documents.md` with sources, volumes, owners, ACL notes, and a
"golden set" of 30–50 documents that cover the most important questions.

## 1.6 People and communication

- Which channel do people live in (Slack, Teams, email, phone)? That is where alerts must arrive.
- Who is the owner / backup per process and per system (for routing alerts and approvals).
- Working hours, time zones, escalation paths ("if not acknowledged in 4 h, notify the manager").
- Appetite for autonomy per team: who wants suggestions, who wants the assistant to just do it.

**Artefact:** `inventory/people.yaml` – a routing table of roles → people → channels.

## 1.7 Constraints

- Data residency and privacy (GDPR, customer data, employee data) – decides cloud vs on-prem LLM and what may be sent to a model API.
- Security policies: network segmentation, VPN, secrets management, logging requirements.
- Budget and hosting options.
- Existing identity provider (Entra ID, Google, Keycloak…) – reuse it for the assistant's permissions.

**Artefact:** a one-page "non-functional requirements" note.

## 1.8 Success metrics to agree up front

Pick 3–5 that you will report on every month:

- hours of repetitive work removed per week (from the process inventory),
- number of deadlines missed (before vs after),
- mean time from anomaly to human awareness (e.g. SEO drop detected after 1 day instead of 3 weeks),
- knowledge-base answer accuracy on the golden question set (target ≥ 90 % "correct and cited"),
- adoption: weekly active users, alerts acknowledged vs ignored (ignored alerts = bad rules).

---

## Discovery output = inputs to the design

| Discovery artefact | Feeds |
|--------------------|-------|
| systems.csv | Tool system (doc 05) – one connector per row |
| processes.md | Playbooks and action rules (docs 04, 06) |
| deadlines.csv | Time rules (doc 04) |
| signals.csv + baselines | Threshold/anomaly rules (doc 04) and the metrics store |
| documents.md + golden set | Knowledge base (doc 03) and the evaluation set |
| people.yaml | Routing, approvals, escalation |
| NFR note | Hosting, model choice, security design |
