# 3. Knowledge base

The knowledge base answers "what does the company know?" It has two halves:
**unstructured** (documents) and **structured** (metrics, entities, deadlines). Most
projects only build the first and then wonder why the assistant cannot tell you that an
invoice is overdue. Build both.

## 3.1 Document pipeline

```
sources ──► connectors ──► parse ──► clean/dedupe ──► chunk ──► enrich ──► embed ──► index
   │                                                                              │
   └──────────── change detection (new / modified / deleted / ACL change) ◄───────┘
```

1. **Connectors** – one per source from discovery §1.5 (file share, SharePoint/Drive,
   Confluence/wiki, ticketing, email archive, the company's own apps). Each connector
   yields documents with: id, title, path, owner, last-modified, **ACL** (groups that may
   read it), source URL.
2. **Parse** – docx/pdf/pptx/xlsx/html/md → text + structure (headings, tables). Tables
   go to the structured store as well when they are really data (price lists, calendars).
   OCR for scanned PDFs and images.
3. **Clean and dedupe** – drop boilerplate, detect duplicates and old versions (keep
   the newest, link the rest), flag drafts.
4. **Chunk** – by heading structure, 300–800 tokens, with overlap, keep the heading
   path as a prefix ("Finance Handbook › Invoicing › Reminders").
5. **Enrich** – per chunk: document type (policy / SOP / contract / spec / meeting
   note), department, systems mentioned, people mentioned, dates and deadlines found,
   glossary terms. An LLM pass does this cheaply at ingestion time. Enrichment is what
   makes filters ("only SOPs from Finance") and the learning loop possible.
6. **Embed and index** – vector embedding + BM25 keyword index (hybrid). Store the
   ACL on every chunk.
7. **Change detection** – incremental re-ingestion on modify; hard delete on delete;
   re-stamp ACLs on permission change. Nightly full reconciliation.

## 3.2 Retrieval

- **Hybrid search** (vector + keyword) → rerank (cross-encoder) → top 5–10 chunks.
- **Pre-filter by the asking user's groups** so nobody sees a chunk they may not read.
- **Metadata filters** chosen by the agent: document type, department, date range.
- **Answer with citations** always: title + link + section. "I don't know, nearest
  documents are…" beats a confident guess.
- **Freshness signal**: tell the user when the source document is older than its
  review cycle.

## 3.3 Structured knowledge

| Table | Key columns | Filled by |
|-------|-------------|-----------|
| `systems` | name, owner, access path, criticality | discovery |
| `people` / `roles` | person, role, team, channel id, backup | discovery + HR system |
| `processes` | name, trigger, owner, playbook ref, systems used | discovery + learning loop |
| `deadlines` | name, due rule (cron/date), owner, lead time, status, source system | discovery + pollers |
| `signals` | name, source tool, cadence, baseline method, thresholds | discovery |
| `metrics` | signal id, timestamp, dimensions (page, customer…), value | pollers |
| `glossary` | term, meaning, synonyms | discovery + learning loop |

The agent gets **SQL/read tools over these tables**, so "which deadlines does Finance
have next month?" is a query, not a document search.

## 3.4 Glossary and terminology

Company abbreviations ("KSZ report", internal product codes) break retrieval and
embeddings. Keep a glossary table, inject the relevant entries into the agent's context,
and expand synonyms at query time.

## 3.5 Quality and maintenance

- **Golden question set** (50–200 Q/A pairs with expected source) – run on every
  pipeline change; target ≥ 90 % correct-and-cited.
- **Unanswered-question log** – every "I don't know" is a KB gap; review weekly, ask
  the owner to write or update the document.
- **Document owners** get a nudge from the assistant itself when a document passes its
  review date (a time rule).
- **Coverage report** per department: documents indexed, last update, questions asked,
  answer accuracy.

## 3.6 Privacy

- Redact or exclude personal data categories the policy forbids sending to a model.
- Chunk-level ACLs are non-negotiable; test them with negative test cases ("user from
  Sales asks about salaries → no result").
- Keep an export of what was indexed so you can prove what the assistant could see.
