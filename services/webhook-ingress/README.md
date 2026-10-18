# webhook-ingress
**Job:** one public endpoint per source (`/hooks/<source>/<event>`), verify the source's signature, deduplicate by delivery id, map the payload to the event envelope (`schemas/event.schema.json`), publish to JetStream, return 200 within 200 ms. Never process inline.
**Config:** `sources.yaml` (secret ref, signature scheme, mapping to event type, idempotency key expression). Emits `producer.heartbeat`.
**Failure handling:** invalid signature → 401 and audit; schema invalid → DLQ `dlq.ingress`; bus unavailable → local spool, replay on reconnect.
**Reference:** `assistant_core.events.Event`, `IdempotencyStore`.
