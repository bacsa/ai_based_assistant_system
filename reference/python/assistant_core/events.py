from __future__ import annotations
import time, os, json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

def ulid(now_ms: Optional[int] = None) -> str:
    """Time-ordered unique id (Crockford base32, 10 time chars + 16 random chars)."""
    t = int(time.time() * 1000) if now_ms is None else now_ms
    out = []
    for _ in range(10):
        out.append(_ALPHABET[t % 32]); t //= 32
    rnd = os.urandom(16)
    return "".join(reversed(out)) + "".join(_ALPHABET[b % 32] for b in rnd)

@dataclass
class Event:
    type: str
    source: str
    data: dict[str, Any]
    subject: str = ""
    idempotencykey: str = ""
    partitionkey: str = ""
    correlationid: str = ""
    causationid: Optional[str] = None
    actor: str = "system"
    pii: str = "none"
    id: str = field(default_factory=ulid)
    time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    specversion: str = "1.0"
    datacontenttype: str = "application/json"

    def __post_init__(self):
        if not self.partitionkey:
            self.partitionkey = self.subject
        if not self.idempotencykey:
            self.idempotencykey = f"{self.type}:{self.subject}:{self.id}"
        if not self.correlationid:
            self.correlationid = self.id

    def caused(self, type: str, data: dict[str, Any], **kw) -> "Event":
        """Create a follow-up event in the same causal chain."""
        kw.setdefault("source", self.source); kw.setdefault("subject", self.subject)
        return Event(type=type, data=data, correlationid=self.correlationid, causationid=self.id, **kw)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

def matches(pattern: str, type_: str) -> bool:
    """NATS-style subject matching: '>' matches everything, 'erp.>' matches a prefix, otherwise exact."""
    if pattern == ">":
        return True
    if pattern.endswith(".>"):
        return type_.startswith(pattern[:-1])
    return pattern == type_

class IdempotencyStore:
    """In-memory processed-key store with TTL. Replace with a Postgres table in production."""
    def __init__(self, ttl_seconds: int = 30 * 86400):
        self.ttl = ttl_seconds; self._seen: dict[str, float] = {}
    def seen_before(self, key: str, now: Optional[float] = None) -> bool:
        now = time.time() if now is None else now
        self._seen = {k: t for k, t in self._seen.items() if now - t < self.ttl}
        if key in self._seen:
            return True
        self._seen[key] = now
        return False
