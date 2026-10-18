# kb-pipeline
**Job:** connectors (SharePoint, Drive, Confluence, SMB, Jira, mailbox, console upload) → parse (docx/pdf/pptx/xlsx/html/md, OCR) → clean and dedupe → chunk by headings (300–800 tokens) → enrich (type, department, systems, people, dates, obligations → draft rules) → embed → index (Qdrant + keyword) → stamp chunk ACLs. Incremental on `kb.document.changed`; nightly reconciliation listing.
**Retrieval API:** hybrid search + rerank, ACL pre-filter by the caller's groups, citations, freshness flag. Golden set in `evals/golden-questions.json`.
**Reference:** `assistant_core.knowledge` (chunking, obligation extraction, keyword fallback).
