# Non-functional requirements (one page)

- **Data residency / privacy:** what may leave the premises; which categories may be sent to a model API; redaction rules.
- **Identity provider:** (Entra ID / Google / Keycloak) → roles for the console and approvals.
- **Network:** segments, VPN, egress rules for webhooks and model API.
- **Secrets:** vault in use; how service accounts are issued per MCP server.
- **Hosting:** on-prem / cloud / hybrid; container platform; who operates it.
- **Availability targets:** event ingress to rule decision p95 < 5 s; to first notification p95 < 60 s; DLQ empty end of day.
- **Audit and retention:** how long events, audit entries and run data are kept; PII flags.
- **Budget:** model spend ceiling per month; alerting on spend.
