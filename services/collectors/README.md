# collectors
**Job:** fetch from sources that cannot push (Search Console, analytics, crawler, TLS, uptime API), diff against the last snapshot in Postgres, publish only changes. Triggered by events (`day.closed`, `cms.page.published`), never by their own cron.
**Each collector:** `collect(trigger_event) -> list[Event]`, snapshot table `collector_snapshots(source, key, hash, payload, at)`, heartbeat every 60 s, quota-aware backoff.
**Starter set:** search-console, analytics, crawler (page diff of title / meta / robots / canonical / H1 / schema), tls, uptime.
